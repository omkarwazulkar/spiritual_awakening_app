import React, { useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { Switch } from "@headlessui/react";
import { SparklesIcon, Loader2Icon } from "lucide-react";

export default function Home() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [showSanskrit, setShowSanskrit] = useState(true);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResults(null);
    try {
      const response = await axios.post(`${import.meta.env.VITE_API_URL}/api/gita`, {
        question,
      });
      setResults(response.data);
    } catch (error) {
      console.error("❌ Error fetching results:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-tr from-yellow-50 via-white to-indigo-50 text-gray-800 px-4 py-8">
      <div className="max-w-3xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-xl p-8 border border-gray-200"
        >
          <h1 className="text-4xl font-extrabold text-center mb-6 flex items-center justify-center gap-2">
            <SparklesIcon className="h-7 w-7 text-yellow-500" />
            Ask the Bhagavad Gita
          </h1>

          <form onSubmit={handleSubmit} className="space-y-4">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask your question about life, karma, dharma, mind..."
              className="w-full p-4 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              rows={4}
              required
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 text-white py-3 rounded-xl font-semibold hover:bg-indigo-700 transition flex justify-center items-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2Icon className="animate-spin h-5 w-5" />
                  Processing...
                </>
              ) : (
                <>
                  <SparklesIcon className="h-5 w-5" />
                  Get Insights
                </>
              )}
            </button>
          </form>
        </motion.div>

        {results && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="mt-10 space-y-8"
          >
            <div className="flex justify-end">
              <div className="flex items-center gap-3">
                <span className="text-sm">Show Sanskrit</span>
                <Switch
                  checked={showSanskrit}
                  onChange={setShowSanskrit}
                  className={`${
                    showSanskrit ? "bg-indigo-600" : "bg-gray-300"
                  } relative inline-flex h-6 w-11 items-center rounded-full transition`}
                >
                  <span
                    className={`${
                      showSanskrit ? "translate-x-6" : "translate-x-1"
                    } inline-block h-4 w-4 transform bg-white rounded-full transition`}
                  />
                </Switch>
              </div>
            </div>

            {results.verses.map((v, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="bg-white p-6 rounded-xl shadow-lg border border-gray-100"
              >
                <h2 className="text-xl font-semibold text-indigo-700">
                  📖 Verse {v.verse_no}
                </h2>
                {showSanskrit && (
                  <p className="mt-2 text-sm text-gray-600 italic border-l-4 border-yellow-300 pl-4">
                    🕉 {v.sanskrit_text}
                  </p>
                )}
                <p className="mt-4 text-gray-700">🔸 {v.translation}</p>
                <h3 className="font-semibold text-xl text-yellow-800 mb-2">🧠 Explanation</h3>
                <p className="text-gray-800 leading-relaxed"> {v.explanation}</p>
              </motion.div>
            ))}

            {/* <div className="bg-gradient-to-br from-yellow-100 to-white p-6 rounded-xl shadow border border-yellow-200">
              <h3 className="font-semibold text-xl text-yellow-800 mb-2">
                🧠 Explanation
              </h3>
              <p className="text-gray-800 leading-relaxed">
                {results.explanation}
              </p>
            </div> */}
          </motion.div>
        )}
      </div>
    </div>
  );
}
