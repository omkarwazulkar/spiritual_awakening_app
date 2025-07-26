from flask import Flask, request, jsonify # type: ignore
from flask_cors import CORS # type: ignore
from gita_pipeline import explainSelectedVerses, loadAndProcessGita, generateEmbeddings, retrieveRelevantDocs
import os

app = Flask(__name__)
CORS(app)

# Load and prepare once
# gitaDf = loadAndProcessGita()
# vectorStore = generateEmbeddings(gitaDf)

@app.route("/", methods=["GET"])
def home():
    return "✨ Gita API is running. Use /api/gita with POST requests."

@app.route("/api/gita", methods=["POST"])
def gita():
    data = request.json
    question = data.get("question")
    print(f"Question received: {question}")

    # topDocs = retrieveRelevantDocs(question, vectorStore)
    # verses = explainSelectedVerses(topDocs)

    verses = [
        {
            "verse_no": "2.47",
            "sanskrit_text": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन",
            "translation": "You have a right to perform your prescribed duties, but you are not entitled to the fruits of your actions.",
            "explanation": "This verse teaches the principle of detached action. Focus on your duty, not on the results."
        },
        {
            "verse_no": "4.7",
            "sanskrit_text": "यदा यदा हि धर्मस्य ग्लानिर्भवति भारत",
            "translation": "Whenever there is a decline in righteousness, O Bharata, and a rise in unrighteousness, I manifest Myself.",
            "explanation": "Krishna promises that He will incarnate to protect dharma whenever it is under threat."
        }
    ]

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

# if __name__ == "__main__":
#     app.run(port=5000)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 for local testing
    app.run(host="0.0.0.0", port=port)

