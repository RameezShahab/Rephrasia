import { useState, useEffect } from "react";
import { useWorkspaceStore } from "../store/useWorkspaceStore";
import { motion } from "framer-motion";
import { Upload, Image as ImageIcon, Languages, Sparkles, Copy, FileText, CheckCircle, Loader2, MessageSquare } from "lucide-react";
import { getOcrLanguages, processOcr, rephraseText, translateText } from "../services/api";

export default function OcrScanner() {
  const [languages, setLanguages] = useState([]);
  const [selectedLang, setSelectedLang] = useState("eng");
  const [targetLang, setTargetLang] = useState("urdu");
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const {
    ocrInput: extractedText,
    setOcrInput: setExtractedText,
    ocrOutput: resultText,
    setOcrOutput: setResultText,
  } = useWorkspaceStore();
  const [activeAction, setActiveAction] = useState(null);
  const [error, setError] = useState(null);
  const [lastAction, setLastAction] = useState(null);

  useEffect(() => {
    getOcrLanguages()
      .then(data => setLanguages(Object.entries(data || {})))
      .catch(console.error);
  }, []);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setPreview(URL.createObjectURL(selected));
      setExtractedText("");
      setResultText("");
      setError(null);
    }
  };

  const handleExtract = async () => {
    if (!file) return;
    setActiveAction("extract");
    setError(null);
    
    const formData = new FormData();
    formData.append("image", file);
    formData.append("language", selectedLang);

    try {
      const data = await processOcr(formData);
      setExtractedText(data.extracted_text);
    } catch (err) {
      setError(err.message);
    } finally {
      setActiveAction(null);
    }
  };

  const handleAction = async (actionType) => {
    if (!extractedText) return;
    setActiveAction(actionType);
    setError(null);
    
    try {
      if (actionType === "rephrase") {
        setLastAction("rephrase");
        const data = await rephraseText(extractedText, "standard");
        if (data.rephrased_results && data.rephrased_results.length > 0) {
          setResultText(data.rephrased_results.join("\n\n"));
        } else {
          setResultText("No results.");
        }
      } else if (actionType === "translate") {
        setLastAction(targetLang);
        const data = await translateText(extractedText, targetLang);
        setResultText(data.translated_text);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setActiveAction(null);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="relative min-h-screen p-8 text-white">
      {/* Background */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(168,85,247,0.15),transparent_40%)]" />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto space-y-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-4xl font-bold flex items-center gap-2">
            <ImageIcon className="text-purple-400" />
            OCR Scanner
          </h1>
          <p className="text-gray-400 mt-2">Extract text from images and process it instantly</p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* LEFT: Upload & Extract */}
          <div className="space-y-6">
            <div className="p-6 bg-white/5 border border-white/10 rounded-2xl">
              <label className="flex flex-col items-center justify-center w-full h-48 border-2 border-dashed border-white/20 rounded-xl cursor-pointer hover:bg-white/5 transition">
                {preview ? (
                  <img src={preview} alt="Preview" className="h-full object-contain p-2" />
                ) : (
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <Upload className="w-10 h-10 text-gray-400 mb-3" />
                    <p className="mb-2 text-sm text-gray-400"><span className="font-semibold text-white">Click to upload</span> or drag and drop</p>
                    <p className="text-xs text-gray-500">JPG, PNG, BMP, TIFF</p>
                  </div>
                )}
                <input type="file" accept="image/*" className="hidden" onChange={handleFileChange} />
              </label>

              <div className="mt-6 flex gap-4">
                <div className="flex-1">
                  <label className="block text-sm text-gray-400 mb-2">Image Language</label>
                  <select 
                    value={selectedLang} 
                    onChange={(e) => setSelectedLang(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-xl p-3 outline-none"
                  >
                    {languages.map(([code, name]) => <option key={code} value={code} className="bg-gray-900">{name}</option>)}
                  </select>
                </div>
                <div className="flex items-end">
                    <button 
                      onClick={handleExtract}
                      disabled={!file || activeAction !== null}
                      className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-medium disabled:opacity-50 transition flex justify-center items-center gap-2"
                    >
                      {activeAction === "extract" ? <Loader2 className="animate-spin" /> : "Extract Text"}
                    </button>
                </div>
              </div>
            </div>

            {error && (
              <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl">
                {error}
              </div>
            )}

            {extractedText && (
              <div className="p-6 bg-white/5 border border-white/10 rounded-2xl">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-semibold flex items-center gap-2"><FileText size={18} /> Extracted Text</h3>
                  <button onClick={() => copyToClipboard(extractedText)} className="text-gray-400 hover:text-white"><Copy size={16} /></button>
                </div>
                <textarea 
                  value={extractedText}
                  onChange={(e) => setExtractedText(e.target.value)}
                  className="w-full h-32 bg-white/5 border border-white/10 rounded-xl p-4 outline-none resize-none"
                />
                
                <div className="mt-4 pt-4 border-t border-white/10">
                  <p className="text-sm text-gray-400 mb-3">Process this text:</p>
                  <div className="flex gap-3">
                      <button 
                        onClick={() => handleAction("rephrase")}
                        disabled={activeAction !== null}
                        className={`flex-1 py-2 bg-purple-600/20 text-purple-400 border border-purple-500/30 rounded-lg flex items-center justify-center gap-2 ${activeAction !== null ? 'opacity-50 cursor-not-allowed' : 'hover:bg-purple-600/30'}`}
                      >
                        {activeAction === "rephrase" ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />} Rephrase
                      </button>
                    
                    <div className="flex flex-1 gap-2">
                      <select 
                        value={targetLang}
                        onChange={(e) => setTargetLang(e.target.value)}
                        className="bg-white/5 border border-white/10 rounded-lg px-2 text-sm outline-none"
                      >
                        <option value="urdu" className="bg-gray-900">Urdu</option>
                        <option value="english" className="bg-gray-900">English</option>
                      </select>
                        <button 
                          onClick={() => handleAction("translate")}
                          disabled={activeAction !== null}
                          className={`flex-1 py-2 bg-blue-600/20 text-blue-400 border border-blue-500/30 rounded-lg flex items-center justify-center gap-2 ${activeAction !== null ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-600/30'}`}
                        >
                          {activeAction === "translate" ? <Loader2 size={16} className="animate-spin" /> : <Languages size={16} />} Translate
                        </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* RIGHT: Result */}
          {resultText && (
             <div className="p-6 bg-white/5 border border-white/10 rounded-2xl flex flex-col h-full">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-semibold flex items-center gap-2 text-green-400"><CheckCircle size={18} /> Result</h3>
                <button onClick={() => copyToClipboard(resultText)} className="text-gray-400 hover:text-white"><Copy size={16} /></button>
              </div>
              <textarea 
                readOnly
                value={resultText}
                className={`flex-1 w-full bg-white/5 border border-white/10 rounded-xl p-4 outline-none resize-none ${lastAction === "urdu" ? "urdu-text" : ""}`}
              />
              <div className="mt-4 flex justify-end">
                <button 
                  onClick={() => {
                    window.dispatchEvent(new CustomEvent('sendToCopilot', { detail: { text: resultText } }));
                  }}
                  className="flex items-center gap-2 px-4 py-2 bg-purple-600/20 text-purple-400 hover:bg-purple-600/30 border border-purple-500/30 rounded-lg text-sm transition-colors"
                >
                  <MessageSquare size={16} />
                  Send to Copilot
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
