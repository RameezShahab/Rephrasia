import { useState } from "react";
import { useWorkspaceStore } from "../store/useWorkspaceStore";
import { checkGrammar } from "../services/api";

import {
  CheckCircle2,
  Copy,
  Trash2,
  Sparkles,
  Check,
  ShieldCheck,
  Zap,
  FileText,
  Clock3,
  Wand2,
  AlertTriangle,
  ChevronRight,
} from "lucide-react";

import { motion } from "framer-motion";

export default function GrammarPage() {

  const {
    grammarInput: input,
    setGrammarInput: setInput,
    grammarOutput: output,
    setGrammarOutput: setOutput,
  } = useWorkspaceStore();

  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const [stats, setStats] = useState({
    grammar: 0,
    readability: 0,
    clarity: 0,
  });

  /* ========= CHECK GRAMMAR ========= */
  const handleCheck = async () => {
    if (!input.trim()) return;

    setLoading(true);

    try {
      const data = await checkGrammar(input);
      if (data.corrected_text) {
        setOutput(data.corrected_text);
      } else {
        setOutput("No output generated.");
      }

      if (data.scores) {
        setStats({
          grammar: data.scores.grammar,
          readability: data.scores.readability,
          clarity: data.scores.clarity,
        });
      }
    } catch (error) {
      console.error(error);
      setOutput(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  /* ========= COPY ========= */
  const handleCopy = async () => {

    if (!output) return;

    await navigator.clipboard.writeText(output);

    setCopied(true);

    setTimeout(() => {
      setCopied(false);
    }, 2000);

  };

  /* ========= CLEAR ========= */
  const handleClear = () => {

    setInput("");
    setOutput("");

    setStats({
      grammar: 0,
      readability: 0,
      clarity: 0,
    });

  };

  return (
    <div className="relative min-h-screen text-white overflow-hidden">

      {/* ========= BACKGROUND ========= */}
      <div className="absolute inset-0 pointer-events-none">

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(168,85,247,0.14),transparent_35%)]"></div>

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,rgba(59,130,246,0.10),transparent_35%)]"></div>

        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:55px_55px]"></div>

      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 py-10">

        {/* ========= HEADER ========= */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-10"
        >

          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-green-500/20 bg-white/[0.04] backdrop-blur-xl mb-6">

            <Sparkles size={15} className="text-green-400" />

            <span className="text-sm text-gray-300">
              AI Grammar Assistant
            </span>

          </div>

          <h1 className="text-5xl font-black tracking-tight leading-tight mb-4">

            Improve Writing With{" "}

            <span className="bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text text-transparent">
              AI Grammar Checking
            </span>

          </h1>

          <p className="text-gray-400 text-lg max-w-3xl leading-relaxed">
            Instantly detect grammar mistakes, improve readability,
            and enhance sentence clarity with advanced AI correction tools.
          </p>

        </motion.div>

        {/* ========= STATS ========= */}
        <div className="grid md:grid-cols-3 gap-6 mb-10">

          <ScoreCard
            title="Grammar Score"
            value={`${stats.grammar}%`}
            icon={<ShieldCheck size={22} />}
          />

          <ScoreCard
            title="Readability"
            value={`${stats.readability}%`}
            icon={<FileText size={22} />}
          />

          <ScoreCard
            title="Clarity"
            value={`${stats.clarity}%`}
            icon={<Zap size={22} />}
          />

        </div>

        {/* ========= MAIN GRID ========= */}
        <div className="grid lg:grid-cols-2 gap-6 mb-8">

          {/* INPUT */}
          <motion.div
            initial={{ opacity: 0, x: -25 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="rounded-3xl border border-white/10 bg-white/[0.04] backdrop-blur-xl overflow-hidden"
          >

            {/* TOP */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">

              <div>

                <h3 className="font-semibold text-lg">
                  Original Text
                </h3>

                <p className="text-sm text-gray-500">
                  Paste your writing here
                </p>

              </div>

              <span className="text-sm text-gray-500">
                {input.length} chars
              </span>

            </div>

            {/* TEXTAREA */}
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Write or paste your text here for grammar correction..."
              className="w-full h-[420px] bg-transparent p-6 outline-none resize-none text-gray-200 placeholder:text-gray-500"
            />

          </motion.div>

          {/* OUTPUT */}
          <motion.div
            initial={{ opacity: 0, x: 25 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="rounded-3xl border border-green-500/10 bg-white/[0.04] backdrop-blur-xl overflow-hidden relative"
          >

            {/* GLOW */}
            <div className="absolute top-0 right-0 w-60 h-60 bg-green-500/10 blur-[100px] rounded-full"></div>

            {/* TOP */}
            <div className="relative z-10 flex items-center justify-between px-6 py-4 border-b border-white/5">

              <div>

                <h3 className="font-semibold text-lg">
                  Corrected Output
                </h3>

                <p className="text-sm text-green-400">
                  AI Enhanced Writing
                </p>

              </div>

              <button
                onClick={handleCopy}
                className="text-gray-400 hover:text-white transition"
              >

                {copied ? (
                  <Check size={18} className="text-green-400" />
                ) : (
                  <Copy size={18} />
                )}

              </button>

            </div>

            {/* OUTPUT */}
            <textarea
              value={output}
              readOnly
              placeholder="AI corrected result will appear here..."
              className="relative z-10 w-full h-[420px] bg-transparent p-6 outline-none resize-none text-gray-200 placeholder:text-gray-500"
            />

          </motion.div>

        </div>

        {/* ========= ACTION BAR ========= */}
        <div className="flex flex-wrap gap-4 items-center mb-14">

          {/* CHECK */}
          <button
            onClick={handleCheck}
            className="relative overflow-hidden flex items-center gap-2 px-7 py-4 rounded-2xl bg-gradient-to-r from-green-500 to-emerald-500 font-semibold hover:scale-105 transition-all duration-300 shadow-xl shadow-green-500/20"
          >

            <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full hover:translate-x-full transition-transform duration-1000"></span>

            <Wand2 size={18} className="relative z-10" />

            <span className="relative z-10">
              {loading ? "Checking..." : "Check Grammar"}
            </span>

          </button>

          {/* CLEAR */}
          <button
            onClick={handleClear}
            className="flex items-center gap-2 px-6 py-4 rounded-2xl border border-white/10 bg-white/[0.04] hover:border-white/20 transition-all duration-300"
          >

            <Trash2 size={18} />

            Clear

          </button>

        </div>

        {/* ========= ISSUES SECTION ========= */}
        <div className="mb-16">

          <div className="flex items-center justify-between mb-6">

            <h2 className="text-3xl font-black tracking-tight">
              Writing Insights
            </h2>

            <span className="text-sm text-green-400">
              AI Suggestions
            </span>

          </div>

          <div className="grid md:grid-cols-3 gap-6">

            <InsightCard
              icon={<AlertTriangle size={22} />}
              title="Grammar Errors"
              desc="Fix punctuation, tense consistency, and sentence structure issues."
            />

            <InsightCard
              icon={<CheckCircle2 size={22} />}
              title="Readability"
              desc="Improve sentence flow and make your content easier to understand."
            />

            <InsightCard
              icon={<Sparkles size={22} />}
              title="Professional Tone"
              desc="Enhance writing tone for academic, formal, or business communication."
            />

          </div>

        </div>

        {/* ========= FEATURES ========= */}
        <div className="grid lg:grid-cols-2 gap-6 mb-16">

          {/* LEFT */}
          <motion.div
            whileHover={{ y: -4 }}
            className="rounded-3xl border border-white/10 bg-white/[0.04] p-8 backdrop-blur-xl"
          >

            <div className="flex items-center gap-4 mb-6">

              <div className="w-14 h-14 rounded-2xl bg-green-500/10 flex items-center justify-center text-green-400">
                <Zap size={24} />
              </div>

              <div>

                <h3 className="text-2xl font-bold">
                  Real-Time AI Analysis
                </h3>

                <p className="text-gray-500 text-sm mt-1">
                  Fast and intelligent corrections
                </p>

              </div>

            </div>

            <div className="space-y-4">

              <FeatureRow text="Advanced grammar correction" />
              <FeatureRow text="Sentence clarity optimization" />
              <FeatureRow text="Professional tone enhancement" />
              <FeatureRow text="Academic writing improvements" />

            </div>

          </motion.div>

          {/* RIGHT */}
          <motion.div
            whileHover={{ y: -4 }}
            className="rounded-3xl border border-white/10 bg-gradient-to-br from-green-500/10 to-transparent p-8 backdrop-blur-xl relative overflow-hidden"
          >

            <div className="absolute top-0 right-0 w-52 h-52 bg-green-500/10 blur-[100px] rounded-full"></div>

            <div className="relative z-10">

              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-green-500/20 bg-white/[0.04] mb-6">

                <Sparkles size={15} className="text-green-400" />

                <span className="text-sm text-gray-300">
                  AI Optimization
                </span>

              </div>

              <h3 className="text-3xl font-black leading-tight mb-4">

                Write Cleaner, Smarter,
                and More Professional Content

              </h3>

              <p className="text-gray-400 leading-relaxed mb-8">
                Improve grammar accuracy, sentence structure,
                readability, and tone using advanced AI language processing.
              </p>

              <button className="flex items-center gap-2 text-green-400 font-medium hover:gap-3 transition-all">

                Learn More

                <ChevronRight size={18} />

              </button>

            </div>

          </motion.div>

        </div>

        {/* ========= FOOTER ========= */}
        <footer className="border-t border-white/5 pt-8">

          <div className="flex flex-col md:flex-row items-center justify-between gap-6">

            {/* LEFT */}
            <div>

              <h3 className="text-xl font-bold bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text text-transparent">
                Rephrasia AI
              </h3>

              <p className="text-gray-500 text-sm mt-2">
                Professional AI grammar and writing enhancement workspace.
              </p>

            </div>

            {/* CENTER */}
            <div className="flex items-center gap-6 text-sm text-gray-400">

              <button className="hover:text-white transition">
                Privacy
              </button>

              <button className="hover:text-white transition">
                Terms
              </button>

              <button className="hover:text-white transition">
                Support
              </button>

            </div>

            {/* RIGHT */}
            <div className="flex items-center gap-2 text-sm text-gray-500">

              <Clock3 size={15} />

              AI Grammar Correction Suite

            </div>

          </div>

        </footer>

      </div>

    </div>
  );
}

/* ========= SCORE CARD ========= */
function ScoreCard({ title, value, icon }) {

  return (
    <motion.div
      whileHover={{ y: -5 }}
      className="relative overflow-hidden rounded-3xl border border-white/10 bg-white/[0.04] p-6 backdrop-blur-xl"
    >

      <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-green-400 to-emerald-500"></div>

      <div className="w-14 h-14 rounded-2xl bg-green-500/10 flex items-center justify-center text-green-400 mb-5">
        {icon}
      </div>

      <p className="text-gray-400 mb-2">
        {title}
      </p>

      <h3 className="text-4xl font-black tracking-tight">
        {value}
      </h3>

    </motion.div>
  );
}

/* ========= INSIGHT CARD ========= */
function InsightCard({ icon, title, desc }) {

  return (
    <motion.div
      whileHover={{ y: -5 }}
      className="group relative overflow-hidden rounded-3xl border border-white/10 bg-white/[0.04] p-6 backdrop-blur-xl"
    >

      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition duration-500 bg-gradient-to-br from-green-500/10 to-transparent"></div>

      <div className="relative z-10">

        <div className="w-14 h-14 rounded-2xl bg-green-500/10 flex items-center justify-center text-green-400 mb-5">
          {icon}
        </div>

        <h3 className="text-xl font-bold mb-3">
          {title}
        </h3>

        <p className="text-gray-400 leading-relaxed">
          {desc}
        </p>

      </div>

    </motion.div>
  );
}

/* ========= FEATURE ROW ========= */
function FeatureRow({ text }) {

  return (
    <div className="flex items-center gap-3 text-gray-300">

      <div className="w-5 h-5 rounded-full bg-green-500/20 flex items-center justify-center">

        <CheckCircle2 size={12} className="text-green-400" />

      </div>

      {text}

    </div>
  );
}