# ===== gita_pipeline.py =====

import os
import re
import json
import pandas as pd
from collections import Counter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma # type: ignore
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate


# ========== CONFIGURATION ==========
DATA_DIR = "data"
CSV_PATH = os.path.join(DATA_DIR, "structured_gita.csv")
EMBEDDINGS_DIR = os.path.join(DATA_DIR, "chroma_embeddings")

# Set API Key (read from env or directly — don't hardcode in production!)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not set in environment")

os.environ["OPENAI_API_KEY"] = api_key


# ========== STEP 1: Load and Process Gita Dataset ==========
def loadAndProcessGita():
    from datasets import load_dataset  # Local import to avoid extra dependency at top

    dataset = load_dataset("utkarshpophli/bhagwat_gita")
    gitaDf = dataset["train"].to_pandas()

    structured = []
    currentVerse, spokenBy, sanskritText, translations = None, None, None, []

    for _, row in gitaDf.iterrows():
        text = row["text"].strip()

        if text.startswith("<s>[INST]"):
            if currentVerse:
                structured.append([currentVerse, spokenBy, sanskritText] + translations)
            translations = []

            verseMatch = re.search(r"verse (\d+\.\d+)", text)
            currentVerse = verseMatch.group(1) if verseMatch else None

            speakerMatch = re.search(r"spoken by ([^.\[\]/]+)", text)
            spokenBy = speakerMatch.group(1).strip() if speakerMatch else None

        elif text.startswith("Sanskrit:"):
            sanskrit = text.replace("Sanskrit:", "").strip()
            sanskritText = re.sub(r"\d+$", "", sanskrit).strip()

        elif text.startswith("Translations:") or (text and text[0].isdigit()):
            translations.append(text.split(" ", 1)[-1] if " " in text else text)

    if currentVerse:
        structured.append([currentVerse, spokenBy, sanskritText] + translations)

    maxTranslations = max(len(row) - 3 for row in structured)
    for row in structured:
        while len(row) < 3 + maxTranslations:
            row.append("")

    columns = ["verse_no", "spoken_by", "sanskrit_text"] + [f"translation_{i+1}" for i in range(maxTranslations)]
    df = pd.DataFrame(structured, columns=columns)

    # Drop translation_1 if it's empty and rename others
    if "translation_1" in df.columns:
        df = df.drop(columns=["translation_1"])

    renameMap = {
        f"translation_{i}": f"translation_{i-1}"
        for i in range(2, 7)
        if f"translation_{i}" in df.columns
    }
    df = df.rename(columns=renameMap)

    speakerMap = {
        "अर्जुन": "Arjun",
        "सञ्जय": "Sanjay",
        "संजय": "Sanjay",
        "धृतराष्ट्र": "Dhritrashtra",
        "भगवान": "Krishna"
    }
    df["spoken_by"] = df["spoken_by"].replace(speakerMap)

    for col in [col for col in df.columns if col.startswith("translation_")]:
        df[col] = df[col].str.lower()

    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(CSV_PATH, index=False)

    print("✅ Gita structured data saved.")
    return df


# ========== STEP 2: Generate or Load Embeddings ==========
def generateEmbeddings(df: pd.DataFrame):
    embeddingModel = OpenAIEmbeddings(model="text-embedding-ada-002")

    if os.path.exists(EMBEDDINGS_DIR) and os.listdir(EMBEDDINGS_DIR):
        print("🔄 Loading existing embeddings from ChromaDB...")
        vectorStore = Chroma(embedding_function=embeddingModel, persist_directory=EMBEDDINGS_DIR)
    else:
        print("⏳ Creating new embeddings and storing in ChromaDB...")
        documents = []

        for _, row in df.iterrows():
            for i in range(1, 6):
                text = row.get(f"translation_{i}")
                if isinstance(text, str) and text.strip():
                    metadata = {
                        "verse_no": row["verse_no"],
                        "spoken_by": row["spoken_by"],
                        "sanskrit_text": row["sanskrit_text"],
                        "translation_index": i
                    }
                    documents.append(Document(page_content=text, metadata=metadata))

        vectorStore = Chroma.from_documents(documents, embeddingModel, persist_directory=EMBEDDINGS_DIR)
        print("✅ Embeddings created and saved.")

    return vectorStore

# ========== STEP 3: Create Query Variations ==========
def generateQueryVariations(question: str):
    prompt = ChatPromptTemplate.from_template(
        """You are an AI assistant helping improve information retrieval.
        Generate five different variations of the given user question.
        Provide each variation on a new line.
        Original question: {question}"""
    )
    messages = prompt.format_messages(question=question)
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    response = model.invoke(messages)
    return response.content.strip().split("\n")


# ========== STEP 4: Semantic Search Across Variations ==========
from collections import defaultdict, Counter

def retrieveRelevantDocs(question: str, vectorStore):
    variations = generateQueryVariations(question)
    print("🔍 Query Variations Generated:")
    for v in variations:
        print(f" - {v}")

    allDocs = []
    for query in variations:
        results = vectorStore.similarity_search(query, k=3)
        allDocs.extend(results)

    # Count frequency of (verse_no, translation_index)
    freqCounter = Counter(
        (doc.metadata["verse_no"], doc.metadata["translation_index"]) for doc in allDocs
    )

    # Group by verse_no and pick the most frequent translation per verse
    bestTranslationPerVerse = {}
    for (verse_no, translation_index), count in freqCounter.items():
        if verse_no not in bestTranslationPerVerse or count > bestTranslationPerVerse[verse_no]["count"]:
            bestTranslationPerVerse[verse_no] = {
                "translation_index": translation_index,
                "count": count
            }

    # Limit to top N unique verses
    topN = 2
    topVerses = sorted(
        bestTranslationPerVerse.items(),
        key=lambda x: x[1]["count"],
        reverse=True
    )[:topN]

    selected = {}
    for doc in allDocs:
        verse_no = doc.metadata["verse_no"]
        translation_index = doc.metadata["translation_index"]

        for topVerse, info in topVerses:
            if verse_no == topVerse and translation_index == info["translation_index"]:
                selected[(verse_no, translation_index)] = doc
    print("✅ Top matching verses identified.")
    print()
    return selected

# ========== STEP 5: Explain Selected Verses ==========
def explainSelectedVerses(selectedDocs):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=200)

    all_explanations = []

    for key, doc in selectedDocs.items():
        verseNo = doc.metadata.get("verse_no", "Unknown")
        sanskrit = doc.metadata.get("sanskrit_text", "")
        content = doc.page_content.strip()

        prompt = ChatPromptTemplate.from_template(
            """In the verse (shlok) {verse_no}, it is explained:
            "{page_content}"

            Provide a clear and insightful explanation in English within 200 tokens.

            The verse that explains this is:
            {sanskrit_text}
            """
        )

        response = llm.invoke(prompt.format(
            verse_no=verseNo,
            page_content=content,
            sanskrit_text=sanskrit
        ))

        explanation = response.content.strip()

        all_explanations.append({
            "verse_no": verseNo,
            "sanskrit_text": sanskrit,
            "translation": content,
            "explanation": explanation
        })

    return all_explanations


# ========== MAIN FLOW ==========
if __name__ == "__main__":
    print("🚀 Starting Bhagavad Gita Processing Pipeline...\n")

    gitaDf = loadAndProcessGita()
    vectorStore = generateEmbeddings(gitaDf)

    userQuestion = "What does Krishna advise about controlling your mind?"
    topDocs = retrieveRelevantDocs(userQuestion, vectorStore)
    explainSelectedVerses(topDocs)

    print("\n🎉 Done. Ready for web integration.")
