import { useState, useEffect } from "react";
import { useWorkspaceStore } from "../store/useWorkspaceStore";
import { translateText, textToSpeech, batchTranslate, getBatchStatus } from "../services/api";

import {
  Languages,
  Wand2,
  Copy,
  Download,
  CheckCircle,
  Clock,
  Speaker,
  Volume2,
  RefreshCw,
  ListChecks,
  Loader2,
  ArrowLeftRight,
  Trash2,
  Sparkles,
  Check,
  Globe,
  Zap,
  Shield,
  Clock3,
  ChevronDown,
} from "lucide-react";

import { motion } from "framer-motion";

export default function TranslatorPage() {

  const {
    translateInput: input,
    setTranslateInput: setInput,
    translateOutput: output,
    setTranslateOutput: setOutput,
    translateFromLang: fromLang,
    setTranslateFromLang: setFromLang,
    translateToLang: toLang,
    setTranslateToLang: setToLang,
    translateIsBatchMode: isBatchMode,
    setTranslateIsBatchMode: setIsBatchMode,
    translateBatchJob: batchJob,
    setTranslateBatchJob: setBatchJob,
  } = useWorkspaceStore();

  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [playing, setPlaying] = useState(false);

  const languages = [
    "English",
    "Urdu",
  ];

  // Poll Batch Job
  useEffect(() => {
    if (!batchJob || batchJob.status === "completed" || batchJob.status === "failed") return;

    const interval = setInterval(async () => {
      try {
        const data = await getBatchStatus(batchJob.id);
        if (data.status !== batchJob.status) {
          if (data.status === "completed") {
            setOutput(data.result.join("\n\n"));
          }
          setBatchJob({ id: data.job_id, status: data.status, result: data.result, error: data.error });
        }
      } catch (err) {
        console.error("Batch polling error:", err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [batchJob]);

  /* ========= TRANSLATE ========= */
  const handleTranslate = async () => {
    if (!input.trim()) return;

    setLoading(true);

    if (isBatchMode) {
      const texts = input.split("\n").map(t => t.trim()).filter(t => t.length > 0);
      if (texts.length > 20) {
        setOutput("Error: Batch exceeds maximum of 20 items. Please reduce the number of lines.");
        setLoading(false);
        return;
      }
      
      try {
        const data = await batchTranslate(texts, toLang.toLowerCase());
        setBatchJob({ id: data.job_id, status: data.status, result: null, error: null });
        setOutput("Batch translation submitted. Processing...");
      } catch (error) {
        console.error(error);
        setOutput(`Error: ${error.message}`);
      }
    } else {
      try {
        const data = await translateText(input, toLang.toLowerCase());
        if (data.translated_text) {
          setOutput(data.translated_text);
        } else {
          setOutput("Translation failed.");
        }
      } catch (error) {
        console.error(error);
        setOutput(`Error: ${error.message}`);
      }
    }
    setLoading(false);
  };

  const handleSpeak = async () => {
    if (!output) return;
    setPlaying(true);
    try {
      const data = await textToSpeech(output, toLang.toLowerCase());
      if (data.audio_url) {
        const audio = new Audio(data.audio_url);
        audio.play();
        audio.onended = () => setPlaying(false);
      }
    } catch (error) {
      console.error("TTS Error:", error);
      setPlaying(false);
    }
  };

  /* ========= SWAP ========= */
  const handleSwap = () => {

    setFromLang(toLang);
    setToLang(fromLang);

    setInput(output);
    setOutput(input);

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
    setBatchJob(null);

  };

  return (
    <div className="relative min-h-screen text-white overflow-hidden">

      {/* ========= BACKGROUND ========= */}
      <div className="absolute inset-0 pointer-events-none">

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(168,85,247,0.14),transparent_35%)]"></div>

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,rgba(59,130,246,0.12),transparent_35%)]"></div>

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

          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-purple-500/20 bg-white/[0.04] backdrop-blur-xl mb-6">

            <Sparkles size={15} className="text-purple-400" />

            <span className="text-sm text-gray-300">
              AI Translation Workspace
            </span>

          </div>

          <h1 className="text-5xl font-black tracking-tight leading-tight mb-4">

            Translate Instantly With{" "}

            <span className="bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
              AI Precision
            </span>

          </h1>

          <p className="text-gray-400 text-lg max-w-3xl leading-relaxed">
            Translate text naturally across multiple languages using advanced AI models with fluency optimization and contextual understanding.
          </p>

        </motion.div>

        {/* ========= TRANSLATOR GRID ========= */}
        <div className="grid lg:grid-cols-2 gap-6 mb-8">

          {/* INPUT */}
          <motion.div
            initial={{ opacity: 0, x: -25 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="bg-white/5 border border-white/10 rounded-3xl p-6 flex flex-col relative h-[450px]"
          >
            {/* Input Header & Batch Toggle */}
            <div className="flex justify-between items-center mb-4 pb-4 border-b border-white/10">
              <select
                value={fromLang}
                onChange={(e) => setFromLang(e.target.value)}
                className="bg-transparent text-gray-300 font-semibold outline-none cursor-pointer hover:text-white transition"
              >
                {languages.map((l) => (
                  <option key={`from-${l}`} value={l} className="bg-[#0f172a]">
                    {l}
                  </option>
                ))}
              </select>
              <div className="flex bg-white/5 rounded-lg p-1">
                <button
                  onClick={() => setIsBatchMode(false)}
                  className={`px-3 py-1 rounded-md text-sm transition ${!isBatchMode ? "bg-white/20 text-white" : "text-gray-400 hover:text-white"}`}
                >
                  Single
                </button>
                <button
                  onClick={() => setIsBatchMode(true)}
                  className={`px-3 py-1 rounded-md text-sm flex items-center gap-1 transition ${isBatchMode ? "bg-blue-500/50 text-white" : "text-gray-400 hover:text-white"}`}
                >
                  <ListChecks size={14} /> Batch
                </button>
              </div>
            </div>

            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={isBatchMode ? "Paste multiple texts, one per line (max 20 lines)..." : "Type to translate..."}
              className="w-full flex-1 bg-transparent border-none outline-none resize-none text-gray-200 placeholder:text-gray-600 text-lg leading-relaxed"
            />
          </motion.div>

          {/* OUTPUT */}
          <motion.div
            initial={{ opacity: 0, x: 25 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="rounded-3xl border border-purple-500/10 bg-white/[0.04] backdrop-blur-xl overflow-hidden relative flex flex-col h-[450px]"
          >

            {/* GLOW */}
            <div className="absolute top-0 right-0 w-60 h-60 bg-purple-500/10 blur-[100px] rounded-full"></div>

            {/* TOP */}
            <div className="relative z-10 flex items-center justify-between px-6 py-4 border-b border-white/5">

              <div className="flex items-center gap-4">
                <select
                  value={toLang}
                  onChange={(e) => setToLang(e.target.value)}
                  className="bg-transparent text-gray-300 font-semibold outline-none cursor-pointer hover:text-white transition"
                >
                  {languages.map((l) => (
                    <option key={`to-${l}`} value={l} className="bg-[#0f172a]">
                      {l}
                    </option>
                  ))}
                </select>

                {isBatchMode && batchJob && (
                  <span className="flex items-center gap-2 text-sm ml-2">
                    {batchJob.status === "completed" ? <CheckCircle size={16} className="text-green-400"/> : <Loader2 size={16} className="animate-spin text-blue-400" />}
                    <span className="text-blue-400 capitalize">{batchJob.status}</span>
                  </span>
                )}
              </div>

              {!isBatchMode && (
                <div className="flex items-center gap-3">
                  {/* SPEAK */}
                  <button 
                    onClick={handleSpeak}
                    disabled={playing}
                    className={`${playing ? "text-purple-400" : "text-gray-400 hover:text-white"} transition`}
                  >
                    <Volume2 size={18} />
                  </button>

                  {/* COPY */}
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
              )}
            </div>

            {/* OUTPUT */}
            {isBatchMode && batchJob ? (
              <div className="relative z-10 flex-1 overflow-y-auto space-y-3 p-6">
                {batchJob.status === "completed" && batchJob.result ? (
                  batchJob.result.map((res, i) => (
                    <div key={i} className="bg-white/5 p-3 rounded-lg border border-white/10">
                      <p className="text-xs text-blue-400 mb-1 font-medium">Item {i+1}</p>
                      <p className="text-gray-200 text-sm whitespace-pre-wrap">{res}</p>
                    </div>
                  ))
                ) : batchJob.error ? (
                  <div className="text-red-400 p-3 bg-red-500/10 rounded-lg">{batchJob.error}</div>
                ) : (
                  <div className="text-gray-500 italic text-sm text-center mt-10">Processing batch translations...</div>
                )}
              </div>
            ) : (
              <textarea
                value={output}
                readOnly
                placeholder="AI translated result will appear here..."
                className={`relative z-10 w-full flex-1 bg-transparent p-6 outline-none resize-none text-gray-200 placeholder:text-gray-500 text-lg leading-relaxed ${toLang === "Urdu" ? "text-right font-urdu" : "text-left"}`}
              />
            )}
          </motion.div>

        </div>

        {/* ========= ACTION BAR ========= */}
        <div className="flex flex-wrap gap-4 items-center mb-12">

          {/* TRANSLATE */}
          <button
            onClick={handleTranslate}
            className="relative overflow-hidden flex items-center gap-2 px-7 py-4 rounded-2xl bg-gradient-to-r from-purple-500 to-pink-500 font-semibold hover:scale-105 transition-all duration-300 shadow-xl shadow-purple-500/20"
          >

            <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full hover:translate-x-full transition-transform duration-1000"></span>

            <Sparkles size={18} className="relative z-10" />

            <span className="relative z-10">
              {loading ? "Translating..." : "Translate Text"}
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

        {/* ========= FEATURES ========= */}
        <div className="grid md:grid-cols-3 gap-6 mb-16">

          <FeatureCard
            icon={<Zap size={22} />}
            title="Real-Time AI"
            desc="Lightning-fast translations powered by modern AI models."
          />

          <FeatureCard
            icon={<Shield size={22} />}
            title="Context Aware"
            desc="Preserves sentence meaning and natural readability."
          />

          <FeatureCard
            icon={<Globe size={22} />}
            title="Global Languages"
            desc="Translate content across multiple major languages."
          />

        </div>

        {/* ========= FOOTER ========= */}
        <footer className="border-t border-white/5 pt-8">

          <div className="flex flex-col md:flex-row items-center justify-between gap-6">

            {/* LEFT */}
            <div>

              <h3 className="text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
                Rephrasia AI
              </h3>

              <p className="text-gray-500 text-sm mt-2">
                Professional AI writing and translation workspace.
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

              AI Powered Translation Suite

            </div>

          </div>

        </footer>

      </div>

    </div>
  );
}

/* ========= FEATURE CARD ========= */
function FeatureCard({ icon, title, desc }) {

  return (
    <motion.div
      whileHover={{ y: -5 }}
      className="relative overflow-hidden rounded-3xl border border-white/10 bg-white/[0.04] p-6 backdrop-blur-xl"
    >

      <div className="absolute inset-0 opacity-0 hover:opacity-100 transition duration-500 bg-gradient-to-br from-purple-500/10 to-transparent"></div>

      <div className="relative z-10">

        <div className="w-14 h-14 rounded-2xl bg-purple-500/10 flex items-center justify-center text-purple-400 mb-5">
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