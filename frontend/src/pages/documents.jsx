import { useState, useEffect } from "react";
import { useWorkspaceStore } from "../store/useWorkspaceStore";
import { motion } from "framer-motion";
import { FileText, FileUp, Sparkles, Languages, Clock, CheckCircle, AlertTriangle, Loader2, Download, MessageSquare } from "lucide-react";
import { extractPdfChunks, asyncRephrase, asyncTranslate, asyncPdfRephrase, asyncPdfTranslate, getAsyncStatus } from "../services/api";

export default function DocumentProcessor() {
  const {
    documentsInputType: inputType,
    setDocumentsInputType: setInputType,
    documentsTaskType: taskType,
    setDocumentsTaskType: setTaskType,
    documentsText: text,
    setDocumentsText: setText,
    documentsLanguage: language,
    setDocumentsLanguage: setLanguage,
    documentsActiveJobs: activeJobs,
    setDocumentsActiveJobs: setActiveJobs,
  } = useWorkspaceStore();

  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Poll for job status
  useEffect(() => {
    const pendingJobs = activeJobs.filter(j => j.status === "pending" || j.status === "processing");
    if (pendingJobs.length === 0) return;

    const interval = setInterval(() => {
      pendingJobs.forEach(async (job) => {
        try {
          const statusData = await getAsyncStatus(job.job_id);
          if (statusData.status !== job.status) {
            setActiveJobs(prev => prev.map(j => 
              j.job_id === job.job_id 
                ? { ...j, status: statusData.status, result: statusData.result, error: statusData.error } 
                : j
            ));
          }
        } catch (err) {
          console.error("Failed to fetch job status", err);
        }
      });
    }, 3000);

    return () => clearInterval(interval);
  }, [activeJobs]);

  const handleSubmit = async () => {
    if (inputType === "text" && !text.trim()) return;
    if (inputType === "pdf" && !file) return;

    setLoading(true);
    setError(null);
    let jobName = inputType === "text" ? "Long Text Process" : file.name;

    try {
      let data;
      if (inputType === "text") {
        if (taskType === "paraphrase") {
          data = await asyncRephrase(text);
        } else {
          data = await asyncTranslate(text, language);
        }
      } else {
        const formData = new FormData();
        formData.append("pdf", file);
        if (taskType === "translate") formData.append("language", language);
        
        if (taskType === "paraphrase") {
          data = await asyncPdfRephrase(formData);
        } else {
          data = await asyncPdfTranslate(formData);
        }
      }

      if (data.job_id) {
        setActiveJobs([{ job_id: data.job_id, status: data.status, result: null, error: null, name: jobName, type: taskType, targetLanguage: taskType === "translate" ? language : null }, ...activeJobs]);
        setText("");
        setFile(null);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const removeJob = (jobId) => {
    setActiveJobs(activeJobs.filter(j => j.job_id !== jobId));
  };

  const downloadAsPDF = (job) => {
    const isUrdu = job.targetLanguage === "urdu";
    const text = typeof job.result === "string" ? job.result : job.result.join("\n");
    
    const printWindow = window.open('', '', 'width=800,height=600');
    printWindow.document.write(`
      <html>
        <head>
          <title>${job.name} - Result</title>
          <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Noto+Nastaliq+Urdu:wght@400;700&display=swap" rel="stylesheet">
          <style>
            body { 
              font-family: ${isUrdu ? "'Noto Nastaliq Urdu', serif" : "'Inter', sans-serif"};
              padding: 40px; 
              line-height: ${isUrdu ? "2.4" : "1.6"};
              font-size: ${isUrdu ? "22px" : "14px"};
              direction: ${isUrdu ? "rtl" : "ltr"};
              text-align: ${isUrdu ? "right" : "left"};
              white-space: pre-wrap;
              color: #000;
            }
            .header { 
              font-family: 'Inter', sans-serif; 
              font-size: 12px; 
              color: #666; 
              margin-bottom: 30px; 
              direction: ltr; 
              text-align: left; 
              border-bottom: 1px solid #ccc; 
              padding-bottom: 10px; 
            }
          </style>
        </head>
        <body>
          <div class="header">Rephrasia AI - ${job.type === "translate" ? "Translation" : "Paraphrase"} Result: ${job.name}</div>
          <div>${text}</div>
          <script>
            window.onload = () => {
              setTimeout(() => {
                window.print();
                window.close();
              }, 500);
            };
          </script>
        </body>
      </html>
    `);
    printWindow.document.close();
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
            <FileText className="text-blue-400" />
            Document Processor
          </h1>
          <p className="text-gray-400 mt-2">Upload PDFs or paste long text for asynchronous processing</p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* LEFT: Input Area */}
          <div className="space-y-6">
            <div className="p-6 bg-white/5 border border-white/10 rounded-2xl">
              
              {/* Type Selectors */}
              <div className="flex gap-2 mb-6">
                <button 
                  onClick={() => setInputType("text")}
                  className={`flex-1 py-2 rounded-lg font-medium transition ${inputType === "text" ? "bg-white/20 text-white" : "bg-white/5 text-gray-400 hover:bg-white/10"}`}
                >
                  📝 Text
                </button>
                <button 
                  onClick={() => setInputType("pdf")}
                  className={`flex-1 py-2 rounded-lg font-medium transition ${inputType === "pdf" ? "bg-white/20 text-white" : "bg-white/5 text-gray-400 hover:bg-white/10"}`}
                >
                  📄 PDF Upload
                </button>
              </div>

              {inputType === "text" ? (
                <textarea 
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Paste your long document text here..."
                  className="w-full h-48 bg-white/5 border border-white/10 rounded-xl p-4 outline-none resize-none mb-4"
                />
              ) : (
                <label className="flex flex-col items-center justify-center w-full h-48 border-2 border-dashed border-white/20 rounded-xl cursor-pointer hover:bg-white/5 transition mb-4">
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <FileUp className="w-10 h-10 text-gray-400 mb-3" />
                    <p className="mb-2 text-sm text-gray-400">
                      <span className="font-semibold text-white">Click to upload PDF</span>
                    </p>
                    <p className="text-xs text-blue-400">{file ? file.name : "Maximum file size: 16MB"}</p>
                  </div>
                  <input type="file" accept="application/pdf" className="hidden" onChange={(e) => setFile(e.target.files[0])} />
                </label>
              )}

              <div className="flex gap-4">
                <div className="flex-1">
                  <label className="block text-sm text-gray-400 mb-2">Task Type</label>
                  <select 
                    value={taskType} 
                    onChange={(e) => setTaskType(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-xl p-3 outline-none"
                  >
                    <option value="paraphrase" className="bg-gray-900">Paraphrase</option>
                    <option value="translate" className="bg-gray-900">Translate</option>
                  </select>
                </div>
                {taskType === "translate" && (
                  <div className="flex-1">
                    <label className="block text-sm text-gray-400 mb-2">Language</label>
                    <select 
                      value={language} 
                      onChange={(e) => setLanguage(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 rounded-xl p-3 outline-none"
                    >
                      <option value="urdu" className="bg-gray-900">Urdu</option>
                      <option value="english" className="bg-gray-900">English</option>
                    </select>
                  </div>
                )}
              </div>

              <button 
                onClick={handleSubmit}
                disabled={loading || (inputType === "text" ? !text : !file)}
                className="w-full mt-6 h-[50px] bg-blue-600 hover:bg-blue-500 rounded-xl font-medium disabled:opacity-50"
              >
                {loading ? "Initializing..." : "Start Processing"}
              </button>
              
              {error && <p className="text-red-400 text-sm mt-3">{error}</p>}
            </div>
          </div>

          {/* RIGHT: Jobs Queue */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold mb-4">Job Queue</h2>
            
            {activeJobs.length === 0 && (
              <div className="p-8 text-center bg-white/5 border border-white/10 rounded-2xl text-gray-500">
                No active jobs. Submit a document to start.
              </div>
            )}

            {activeJobs.map((job) => (
              <div key={job.job_id} className="p-5 bg-white/5 border border-white/10 rounded-2xl">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-semibold text-white truncate max-w-[200px]">{job.name}</h3>
                    <p className="text-sm text-gray-400 flex items-center gap-1 mt-1">
                      {job.type === "paraphrase" ? <Sparkles size={14}/> : <Languages size={14}/>} 
                      <span className="capitalize">{job.type}</span>
                    </p>
                  </div>
                  
                  {job.status === "completed" && <span className="flex items-center gap-1 text-green-400 text-sm font-medium"><CheckCircle size={16}/> Done</span>}
                  {(job.status === "pending" || job.status === "processing") && <span className="flex items-center gap-1 text-blue-400 text-sm font-medium"><Loader2 size={16} className="animate-spin"/> Processing</span>}
                  {job.status === "failed" && <span className="flex items-center gap-1 text-red-400 text-sm font-medium"><AlertTriangle size={16}/> Failed</span>}
                </div>

                {job.status === "completed" && job.result && (
                  <div className="mt-4 pt-4 border-t border-white/10">
                    <textarea 
                      readOnly
                      value={typeof job.result === "string" ? job.result : job.result.join("\n")}
                      className={`w-full h-48 bg-black/30 rounded-lg p-4 outline-none resize-y ${job.targetLanguage === "urdu" ? "urdu-text" : "text-sm"}`}
                    />
                    <div className="flex justify-between items-center mt-3">
                      <button onClick={() => removeJob(job.job_id)} className="text-sm text-gray-500 hover:text-white transition-colors">Dismiss</button>
                      <div className="flex items-center gap-2">
                        <button 
                          onClick={() => {
                            const resultText = typeof job.result === "string" ? job.result : job.result.join("\n");
                            window.dispatchEvent(new CustomEvent('sendToCopilot', { detail: { text: resultText } }));
                          }}
                          className="flex items-center gap-2 px-3 py-1.5 bg-purple-600/20 text-purple-400 hover:bg-purple-600/30 border border-purple-500/30 rounded-lg text-sm transition-colors"
                        >
                          <MessageSquare size={14} />
                          Send to Copilot
                        </button>
                        <button 
                          onClick={() => downloadAsPDF(job)} 
                          className="flex items-center gap-2 px-3 py-1.5 bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 border border-blue-500/30 rounded-lg text-sm transition-colors"
                        >
                          <Download size={14} />
                          Download PDF
                        </button>
                      </div>
                    </div>
                  </div>
                )}
                
                {job.status === "failed" && job.error && (
                  <div className="mt-3 text-sm text-red-400 bg-red-500/10 p-2 rounded">
                    {job.error}
                    <button onClick={() => removeJob(job.job_id)} className="block text-gray-400 hover:text-white mt-2">Dismiss</button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
