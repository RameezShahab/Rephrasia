import { useState } from "react";
import { motion } from "framer-motion";
import { Search, Trash2, FileText, Sparkles, Clock3, Filter } from "lucide-react";

export default function History() {
  const [search, setSearch] = useState("");

  const [history, setHistory] = useState([
    {
      id: 1,
      title: "AI Paraphrased Blog Article",
      type: "Paraphraser",
      time: "2 hours ago",
    },
    {
      id: 2,
      title: "Urdu Translation Task",
      type: "Translator",
      time: "Yesterday",
    },
    {
      id: 3,
      title: "Grammar Fix - Essay Draft",
      type: "Grammar Checker",
      time: "2 days ago",
    },
    {
      id: 4,
      title: "AI Chat Session on Marketing",
      type: "AI Chat",
      time: "3 days ago",
    },
  ]);

  const handleDelete = (id) => {
    setHistory(history.filter((item) => item.id !== id));
  };

  const filtered = history.filter((item) =>
    item.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="relative min-h-screen text-white p-8">

      {/* BACKGROUND */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(168,85,247,0.15),transparent_40%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,rgba(59,130,246,0.12),transparent_40%)]" />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto">

        {/* HEADER */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold flex items-center gap-2">
            <Clock3 className="text-purple-400" />
            History
          </h1>

          <p className="text-gray-400 mt-2">
            Your AI activity and generated content history
          </p>
        </motion.div>

        {/* SEARCH + FILTER */}
        <div className="flex flex-col md:flex-row gap-4 mb-8">

          <div className="relative flex-1">
            <Search className="absolute left-4 top-3 text-gray-500" size={18} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search history..."
              className="w-full bg-white/5 border border-white/10 rounded-2xl py-3 pl-12 pr-4 outline-none focus:border-purple-500/30"
            />
          </div>

          <button className="flex items-center gap-2 px-5 py-3 rounded-2xl bg-white/5 border border-white/10 hover:border-purple-500/30">
            <Filter size={16} />
            Filter
          </button>

        </div>

        {/* LIST */}
        <div className="space-y-4">

          {filtered.length === 0 ? (
            <p className="text-gray-500 text-center py-10">
              No history found.
            </p>
          ) : (
            filtered.map((item) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center justify-between p-5 rounded-2xl bg-white/5 border border-white/10 hover:border-purple-500/20 transition"
              >

                {/* LEFT */}
                <div className="flex items-center gap-4">

                  <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center text-purple-400">
                    <FileText size={18} />
                  </div>

                  <div>

                    <h3 className="font-semibold">
                      {item.title}
                    </h3>

                    <p className="text-sm text-gray-500">
                      {item.type}
                    </p>

                  </div>

                </div>

                {/* RIGHT */}
                <div className="flex items-center gap-4">

                  <span className="text-sm text-gray-500">
                    {item.time}
                  </span>

                  <button
                    onClick={() => handleDelete(item.id)}
                    className="text-gray-500 hover:text-red-400 transition"
                  >
                    <Trash2 size={18} />
                  </button>

                </div>

              </motion.div>
            ))
          )}

        </div>

        {/* FOOTER */}
        <div className="mt-12 border-t border-white/10 pt-6 text-center text-gray-500 text-sm">

          <div className="flex items-center justify-center gap-2 mb-2">
            <Sparkles size={14} className="text-purple-400" />
            Rephrasia AI Workspace
          </div>

          <p>
            AI-powered writing • Translation • Grammar • Chat system
          </p>

        </div>

      </div>
    </div>
  );
}