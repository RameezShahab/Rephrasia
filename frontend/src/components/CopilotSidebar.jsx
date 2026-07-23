import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Sparkles, Bot, User, X, MessageSquare } from "lucide-react";
import { sendChatMessage } from "../services/api";

export default function CopilotSidebar() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([
    { role: "ai", text: "Hello! I am Rephrasia Copilot. Ask me anything about your documents!" }
  ]);

  const chatRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    chatRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isOpen]);

  // Listen for text sent from other components
  useEffect(() => {
    const handleSendToCopilot = (e) => {
      setIsOpen(true);
      const text = e.detail?.text;
      if (text) {
        setInput(`Please analyze or summarize this text (You MUST reply in English):\n\n"${text}"\n`);
      }
    };
    window.addEventListener("sendToCopilot", handleSendToCopilot);
    return () => window.removeEventListener("sendToCopilot", handleSendToCopilot);
  }, []);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 250)}px`;
    }
  }, [input]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput("");
    if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
    }
    setLoading(true);

    try {
      const data = await sendChatMessage(currentInput, sessionId);
      if (data.session_id) setSessionId(data.session_id);
      if (data.reply) {
        setMessages((prev) => [...prev, { role: "ai", text: data.reply }]);
      }
    } catch (error) {
      console.error(error);
      setMessages((prev) => [...prev, { role: "ai", text: `Error: ${error.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-8 right-8 w-14 h-14 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full flex items-center justify-center shadow-lg hover:shadow-purple-500/50 hover:scale-105 transition-all z-50"
        >
          <MessageSquare className="text-white" size={24} />
        </button>
      )}

      {/* Slide-out Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ x: "100%", opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: "100%", opacity: 0 }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed top-0 right-0 w-96 h-screen bg-gray-950/95 backdrop-blur-3xl border-l border-white/10 shadow-2xl z-50 flex flex-col"
          >
            {/* Header */}
            <div className="h-16 border-b border-white/10 flex items-center justify-between px-6 bg-white/5">
              <div className="flex items-center gap-2">
                <Sparkles className="text-purple-400" size={20} />
                <h2 className="font-bold bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">Rephrasia Copilot</h2>
              </div>
              <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-white transition">
                <X size={20} />
              </button>
            </div>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg, i) => (
                <div key={i} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === "user" ? "bg-blue-600" : "bg-purple-600"}`}>
                    {msg.role === "user" ? <User size={14} /> : <Bot size={14} />}
                  </div>
                  <div className={`max-w-[85%] p-3 rounded-2xl text-sm ${msg.role === "user" ? "bg-blue-600/20 border border-blue-500/30 rounded-tr-none break-words" : "bg-white/5 border border-white/10 rounded-tl-none whitespace-pre-wrap break-words"}`}>
                    {msg.text}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center shrink-0">
                    <Bot size={14} />
                  </div>
                  <div className="p-3 bg-white/5 border border-white/10 rounded-2xl rounded-tl-none text-sm text-gray-400">
                    Thinking...
                  </div>
                </div>
              )}
              <div ref={chatRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-white/10 bg-white/5">
              <div className="relative flex items-end gap-2">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Ask the Copilot anything..."
                  className="flex-1 max-h-[250px] overflow-y-auto bg-black/50 border border-white/10 rounded-xl p-3 text-sm outline-none resize-none focus:border-purple-500/50"
                  rows={1}
                />
                <button
                  onClick={handleSend}
                  disabled={loading || !input.trim()}
                  className="mb-1 p-3 text-purple-400 hover:bg-purple-500/20 rounded-xl disabled:opacity-50 transition-colors shrink-0"
                >
                  <Send size={18} />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
