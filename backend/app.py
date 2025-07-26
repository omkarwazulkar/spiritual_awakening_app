from flask import Flask, request, jsonify # type: ignore
from flask_cors import CORS # type: ignore
from gita_pipeline import explainSelectedVerses, loadAndProcessGita, generateEmbeddings, retrieveRelevantDocs

app = Flask(__name__)
CORS(app)

# Load and prepare once
gitaDf = loadAndProcessGita()
vectorStore = generateEmbeddings(gitaDf)

@app.route("/api/gita", methods=["POST"])
def gita():
    data = request.json
    question = data.get("question")
    print(f"Question received: {question}")

    topDocs = retrieveRelevantDocs(question, vectorStore)
    verses = explainSelectedVerses(topDocs)

    return jsonify({
        "verses": [
            {
                "verse_no": v["verse_no"],
                "sanskrit_text": v["sanskrit_text"],
                "translation": v["translation"],
                "explanation": v["explanation"]
            } for v in verses
        ],
    })

if __name__ == "__main__":
    app.run(port=5000)
