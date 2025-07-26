from flask import Flask, request, jsonify # type: ignore
from flask_cors import CORS # type: ignore
from gita_pipeline import explainSelectedVerses, loadAndProcessGita, generateEmbeddings, retrieveRelevantDocs
import os

app = Flask(__name__)
CORS(app)

# Load and prepare once
gitaDf = loadAndProcessGita()
vectorStore = generateEmbeddings(gitaDf)

@app.route("/", methods=["GET"])
def home():
    print("Home")
    return "✨ Gita API is running. Use /api/gita with POST requests."

@app.route("/api/gita", methods=["POST"])
def gita():
    print("✅ /api/gita POST route was called")
    data = request.json
    question = data.get("question")
    print(f"Question received: {question}")

    # topDocs = retrieveRelevantDocs(question, vectorStore)
    # verses = explainSelectedVerses(topDocs)

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

