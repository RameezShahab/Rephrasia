import { useState, useEffect } from "react";
import { useWorkspaceStore } from "../store/useWorkspaceStore";
import {
  Copy,
  Wand2,
  Trash2,
  Download,
  ChevronDown,
  Sparkles,
  Info,
  BarChart3,
  ListChecks,
} from "lucide-react";

import { motion } from "framer-motion";

import jsPDF from "jspdf";
import { Document, Packer, Paragraph } from "docx";
import { saveAs } from "file-saver";
import { rephraseText, batchRephrase, getBatchStatus } from "../services/api";

export default function Paraphrase() {
  const {
    paraphraseInput: input,
    setParaphraseInput: setInput,
    paraphraseOutput: output,
    setParaphraseOutput: setOutput,
    paraphraseMode: mode,
    setParaphraseMode: setMode,
    paraphraseIsBatchMode: isBatchMode,
    setParaphraseIsBatchMode: setIsBatchMode,
    paraphraseBatchJob: batchJob,
    setParaphraseBatchJob: setBatchJob,
    paraphraseHistory: history,
    setParaphraseHistory: setHistory,
  } = useWorkspaceStore();

  const [loading, setLoading] = useState(false);
  const [showDownloadMenu, setShowDownloadMenu] = useState(false);

  const modes = ["Standard", "Fluency", "Creative", "Academic"];

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

  /* ========= REWRITE ========= */
  const handleRewrite = async () => {
    if (!input.trim()) return;

    setLoading(true);

    if (isBatchMode) {
      // BATCH LOGIC
      const texts = input.split("\n").map(t => t.trim()).filter(t => t.length > 0);
      if (texts.length > 20) {
        setOutput("Error: Batch exceeds maximum of 20 items. Please reduce the number of lines.");
        setLoading(false);
        return;
      }
      
      try {
        const data = await batchRephrase(texts);
        setBatchJob({ id: data.job_id, status: data.status, result: null, error: null });
        setOutput("Batch job submitted. Processing...");
      } catch (error) {
        console.error(error);
        setOutput(`Error: ${error.message}`);
      }
    } else {
      // SINGLE LOGIC
      try {
        const data = await rephraseText(input, mode.toLowerCase());
        if (data.rephrased_results && data.rephrased_results.length > 0) {
          setOutput(data.rephrased_results.join("\n\n"));
          setHistory([input, ...history].slice(0, 5));
        } else {
          setOutput("No output generated.");
        }
      } catch (error) {
        console.error(error);
        setOutput(`Error: ${error.message}`);
      }
    }
    
    setLoading(false);
  };

  /* ========= CLEAR ========= */
  const handleClear = () => {
    setInput("");
    setOutput("");
    setBatchJob(null);
  };

  /* ========= COPY ========= */
  const handleCopy = () => {
    navigator.clipboard.writeText(output);
  };

  /* ========= EXPORT: TXT ========= */
  const downloadTXT = () => {
    const blob = new Blob([output || ""], {
      type: "text/plain;charset=utf-8",
    });
    saveAs(blob, "paraphrased-text.txt");
  };

  /* ========= EXPORT: PDF ========= */
  const downloadPDF = () => {
    const pdf = new jsPDF();

    const text = output || "No content available";
    const splitText = pdf.splitTextToSize(text, 180);

    pdf.text(splitText, 10, 10);
    pdf.save("paraphrased-text.pdf");
  };

  /* ========= EXPORT: DOCX ========= */
  const downloadDOCX = () => {
    const doc = new Document({
      sections: [
        {
          children: [
            new Paragraph(output || "No content available"),
          ],
        },
      ],
    });

    Packer.toBlob(doc).then((blob) => {
      saveAs(blob, "paraphrased-text.docx");
    });
  };

  return (
    <div className="max-w-6xl mx-auto space-y-10">

      {/* ========= HEADER ========= */}
      <div>
        <h1 className="text-4xl font-bold tracking-tight">
          AI Paraphraser
        </h1>
        <p className="text-gray-400 mt-2">
          Rewrite content with AI-powered clarity and precision.
        </p>
      </div>

      {/* ========= MODES ========= */}
      <div className="flex flex-wrap gap-2">
        {modes.map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`px-4 py-2 rounded-full text-sm border transition ${
              mode === m
                ? "bg-purple-600 border-purple-500 text-white"
                : "bg-white/5 border-white/10 text-gray-400 hover:text-white"
            }`}
          >
            {m}
          </button>
        ))}
      </div>

      {/* ========= TEXT AREAS ========= */}
      <div className="grid md:grid-cols-2 gap-6">

        {/* INPUT */}
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
          {/* Input Header & Batch Toggle */}
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold text-gray-300">Original Text</h3>
            <div className="flex bg-white/5 rounded-lg p-1">
              <button
                onClick={() => setIsBatchMode(false)}
                className={`px-3 py-1 rounded-md text-sm transition ${!isBatchMode ? "bg-white/20 text-white" : "text-gray-400 hover:text-white"}`}
              >
                Single
              </button>
              <button
                onClick={() => setIsBatchMode(true)}
                className={`px-3 py-1 rounded-md text-sm flex items-center gap-1 transition ${isBatchMode ? "bg-purple-500/50 text-white" : "text-gray-400 hover:text-white"}`}
              >
                <ListChecks size={14} /> Batch
              </button>
            </div>
          </div>

          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="w-full h-60 bg-black/30 border border-white/10 rounded-xl p-4 outline-none resize-none"
            placeholder={isBatchMode ? "Paste multiple texts, one per line (max 20 lines)..." : "Paste your text here..."}
          />
        </div>

        {/* OUTPUT */}
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6 flex flex-col">

          <div className="flex justify-between items-center mb-4 pb-2">
            <h3 className="font-semibold text-gray-300">
              {isBatchMode && batchJob ? (
                <span className="flex items-center gap-2">
                  {batchJob.status === "completed" ? <CheckCircle size={16} className="text-green-400"/> : <Loader2 size={16} className="animate-spin text-purple-400" />}
                  Job Status: <span className="text-purple-400 capitalize">{batchJob.status}</span>
                </span>
              ) : "AI Output"}
            </h3>

            {!isBatchMode && (
              <button onClick={handleCopy} className="text-gray-400 hover:text-white">
                <Copy size={18} />
              </button>
            )}
          </div>

          {isBatchMode && batchJob ? (
            <div className="flex-1 h-60 overflow-y-auto space-y-3 bg-black/20 p-4 rounded-xl border border-white/5">
              {batchJob.status === "completed" && batchJob.result ? (
                batchJob.result.map((res, i) => (
                  <div key={i} className="bg-white/5 p-3 rounded-lg border border-white/10">
                    <p className="text-xs text-purple-400 mb-1 font-medium">Item {i+1}</p>
                    <p className="text-gray-200 text-sm whitespace-pre-wrap">{res.join("\n")}</p>
                  </div>
                ))
              ) : batchJob.error ? (
                <div className="text-red-400 p-3 bg-red-500/10 rounded-lg">{batchJob.error}</div>
              ) : (
                <div className="text-gray-500 italic text-sm text-center mt-10">Processing batch items...</div>
              )}
            </div>
          ) : (
            <textarea
              value={output}
              readOnly
              className="w-full h-60 bg-black/30 border border-white/10 rounded-xl p-4 outline-none resize-none"
              placeholder="AI output will appear here..."
            />
          )}
        </div>

      </div>

      {/* ========= ACTION BAR ========= */}
      <div className="flex flex-wrap items-center gap-4">

        {/* REWRITE */}
        <button
          onClick={handleRewrite}
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 font-medium hover:scale-[1.03] active:scale-95 transition shadow-lg shadow-purple-500/20"
        >
          <Wand2 size={18} />
          {loading ? "Rewriting..." : "Rewrite Text"}
        </button>

        {/* CLEAR */}
        <button
          onClick={handleClear}
          className="flex items-center gap-2 px-5 py-3 rounded-xl bg-white/5 border border-white/10 hover:border-white/25 hover:bg-white/10 transition"
        >
          <Trash2 size={18} />
          Clear
        </button>

        {/* EXPORT */}
        <div className="relative">

          <button
            onClick={() => setShowDownloadMenu(!showDownloadMenu)}
            className="flex items-center gap-2 px-5 py-3 rounded-xl bg-white/5 border border-white/10 hover:border-white/25 hover:bg-white/10 transition"
          >
            <Download size={18} />
            Export
            <ChevronDown
              size={16}
              className={`transition-transform duration-200 ${
                showDownloadMenu ? "rotate-180" : ""
              }`}
            />
          </button>

          {showDownloadMenu && (
            <div className="absolute mt-2 w-44 bg-[#0B1220] border border-white/10 rounded-xl overflow-hidden shadow-2xl z-50">

              <button
                onClick={() => {
                  downloadTXT();
                  setShowDownloadMenu(false);
                }}
                className="w-full text-left px-4 py-2 hover:bg-white/5"
              >
                Export as TXT
              </button>

              <button
                onClick={() => {
                  downloadPDF();
                  setShowDownloadMenu(false);
                }}
                className="w-full text-left px-4 py-2 hover:bg-white/5"
              >
                Export as PDF
              </button>

              <button
                onClick={() => {
                  downloadDOCX();
                  setShowDownloadMenu(false);
                }}
                className="w-full text-left px-4 py-2 hover:bg-white/5"
              >
                Export as DOCX
              </button>

            </div>
          )}

        </div>

      </div>

      {/* ========= INSIGHTS ========= */}
      <div className="grid md:grid-cols-3 gap-6">

        <Card icon={<BarChart3 size={18} />} title="Readability" value="87 / 100" />
        <Card icon={<Sparkles size={18} />} title="AI Quality" value="High" />
        <Card icon={<Info size={18} />} title="Suggestion" value="Improve flow" />

      </div>

      {/* ========= TIPS ========= */}
      <div className="bg-white/5 border border-white/10 rounded-2xl p-6">

        <h2 className="text-lg font-semibold mb-3">Writing Tips</h2>

        <ul className="text-gray-400 space-y-2 text-sm">
          <li>• Use Fluency mode for natural rewriting</li>
          <li>• Academic mode improves formal tone</li>
          <li>• Keep input clean for best AI output</li>
        </ul>

      </div>

      {/* ========= FOOTER ========= */}
      <footer className="border-t border-white/10 pt-8 mt-10">

        <div className="grid md:grid-cols-3 gap-6 text-sm text-gray-400">

          <div>
            <h3 className="text-white font-semibold mb-2">Rephrasia AI</h3>
            <p>AI-powered writing assistant for modern creators.</p>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-2">Product</h3>
            <p>Paraphraser</p>
            <p>Translator</p>
            <p>Grammar Checker</p>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-2">Support</h3>
            <p>Help Center</p>
            <p>Documentation</p>
            <p>Contact</p>
          </div>

        </div>

        <p className="text-center text-xs text-gray-500 mt-8">
          © {new Date().getFullYear()} Rephrasia AI. All rights reserved.
        </p>

      </footer>

    </div>
  );
}

/* ========= CARD ========= */
function Card({ icon, title, value }) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-5">
      <div className="text-purple-400 mb-3">{icon}</div>
      <p className="text-gray-400 text-sm">{title}</p>
      <h3 className="text-lg font-semibold mt-1">{value}</h3>
    </div>
  );
}