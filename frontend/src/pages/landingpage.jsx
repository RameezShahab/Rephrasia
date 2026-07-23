import { Link } from "react-router-dom";
import {
  Sparkles,
  Languages,
  CheckCircle,
  MessageSquare,
  ArrowRight
} from "lucide-react";
import { Typewriter } from "react-simple-typewriter";
import { useState, useEffect } from "react";

export default function LandingPage() {
  return (
    <div className="relative min-h-screen bg-gray-950 text-white overflow-hidden">

      {/* ========= FLOATING BACKGROUND ========= */}
<div className="absolute inset-0 overflow-hidden pointer-events-none">

  <div className="absolute top-[-100px] left-[-100px] w-[500px] h-[500px] bg-purple-500 opacity-60 blur-[80px] rounded-full animate-float1"></div>

  <div className="absolute bottom-[-100px] right-[-100px] w-[450px] h-[450px] bg-pink-500 opacity-60 blur-[80px] rounded-full animate-float2"></div>

  <div className="absolute top-[30%] left-[40%] w-[350px] h-[350px] bg-blue-500 opacity-50 blur-[80px] rounded-full animate-float3"></div>

  {/* Radial Glow */}
  <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(168,85,247,0.15),transparent_40%)]"></div>

  {/* Grid Mesh */}
  <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:60px_60px]"></div>

</div>
      {/* ========= NAVBAR ========= */}
      <nav className="sticky top-0 z-50 flex items-center justify-between px-8 py-5 backdrop-blur-xl bg-black/30 shadow-lg shadow-black/20 border-b border-white/5">
       <h1 className="text-2xl font-extrabold tracking-tight bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
          Rephrasia AI
        </h1>

       <div className="flex items-center gap-5">

  <Link
    to="/dashboard"
    className="text-gray-300 hover:text-white transition font-medium"
  >
    Dashboard
  </Link>

  <button className="text-gray-300 hover:text-white transition font-medium">
    Login
  </button>

  <Link
    to="/dashboard"
    className="px-5 py-2 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 font-semibold hover:scale-105 transition-all duration-300 shadow-lg shadow-purple-500/20"
  >
    Get Started
  </Link>

</div>
      </nav>
      <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-purple-500/20 bg-white/5 backdrop-blur-xl mb-8">
  <Sparkles size={16} className="text-purple-400" />
  <span className="text-sm text-gray-300 tracking-wide">
    AI-Powered Writing Assistant
  </span>
</div>

      {/* ========= HERO ========= */}
     <section className="relative z-10 text-center px-6 pt-32 pb-24 max-w-5xl mx-auto">
      

       <h1 className="text-6xl md:text-8xl font-black leading-[0.95] tracking-tight mb-8">
          Rewrite{" "}
          <span className="bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent drop-shadow-[0_0_40px_rgba(168,85,247,0.35)]">
            <Typewriter
              words={["Smarter", "Faster", "Like a Pro", "with AI"]}
              loop={true}
              cursor
              cursorStyle="|"
              typeSpeed={70}
              deleteSpeed={40}
              delaySpeed={1500}
            />
          </span>
        </h1>

       <p className="text-gray-400 text-xl leading-relaxed max-w-2xl mx-auto mb-10">
          Paraphrase, translate, fix grammar, and chat with AI — all in one powerful platform.
        </p>

        <div className="flex justify-center gap-4 flex-wrap">
          <Link
            to="/dashboard"
           className="px-8 py-4 rounded-xl font-semibold tracking-wide bg-gradient-to-r from-purple-500 to-pink-500 text-lg flex items-center gap-2 hover:scale-105 transition"
          >
            Start for Free <ArrowRight size={18} />
          </Link>

          <Link
            to="/paraphrase"
       className="px-8 py-4 rounded-xl font-semibold tracking-wide  border border-white/10 hover:bg-white/5 transition"
          >
            Try Paraphraser
          </Link>
        </div>

        {/* ========= AI PREVIEW ========= */}
     <div className="w-full max-w-5xl mt-16 bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-xl shadow-xl">

  {/* HEADER */}
  <div className="flex items-center justify-between mb-4">
    <span className="text-sm text-gray-400">AI Paraphraser</span>
    <span className="text-xs text-green-400">● Live</span>
  </div>

  <div className="grid md:grid-cols-2 gap-6">

    {/* INPUT */}
    <div>
      <p className="text-gray-400 text-sm mb-2">Original</p>

      <div className="bg-gray-800 p-4 rounded-lg text-sm leading-relaxed">
        AI is changing the world very fast and people need better tools to improve productivity.
      </div>
    </div>

    {/* OUTPUT */}
    <div>
      <p className="text-gray-400 text-sm mb-2">Rewritten</p>
<div className="bg-gray-900 p-4 rounded-lg text-sm text-purple-300 leading-relaxed min-h-[120px] border border-purple-500/20 shadow-[0_0_20px_rgba(168,85,247,0.2)]">

        <TypingPreview />
      </div>
    </div>

  </div>
</div>

      </section>

      {/* STATS SECTION */}
      <section className="relative z-10 px-6 pb-24">
  <div className="max-w-6xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6">

    <div className="text-center p-6 rounded-2xl bg-white/5 border border-white/10">
      <h3 className="text-4xl font-black text-purple-400">10K+</h3>
      <p className="text-gray-400 mt-2">Words Rewritten</p>
    </div>

    <div className="text-center p-6 rounded-2xl bg-white/5 border border-white/10">
      <h3 className="text-4xl font-black text-pink-400">98%</h3>
      <p className="text-gray-400 mt-2">Accuracy</p>
    </div>

    <div className="text-center p-6 rounded-2xl bg-white/5 border border-white/10">
      <h3 className="text-4xl font-black text-blue-400">24/7</h3>
      <p className="text-gray-400 mt-2">AI Availability</p>
    </div>

    <div className="text-center p-6 rounded-2xl bg-white/5 border border-white/10">
      <h3 className="text-4xl font-black text-green-400">1 Sec</h3>
      <p className="text-gray-400 mt-2">Response Speed</p>
    </div>

  </div>
</section>

{/*HOW IT WORKS SECTION*/}
<section className="relative z-10 px-6 pb-28">

  <div className="max-w-6xl mx-auto text-center mb-16">
    <h2 className="text-5xl font-black tracking-tight mb-6">
      How Rephrasia AI Works
    </h2>

    <p className="text-gray-400 text-xl max-w-2xl mx-auto leading-relaxed">
      Rewrite content intelligently in just a few seconds.
    </p>
  </div>

  <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">

    <div className="p-8 rounded-3xl bg-white/5 border border-white/10 backdrop-blur-xl">
      <div className="text-5xl font-black text-purple-400 mb-4">01</div>
      <h3 className="text-2xl font-bold mb-3">Enter Text</h3>
      <p className="text-gray-400 leading-relaxed">
        Paste your content into the AI editor.
      </p>
    </div>

    <div className="p-8 rounded-3xl bg-white/5 border border-white/10 backdrop-blur-xl">
      <div className="text-5xl font-black text-pink-400 mb-4">02</div>
      <h3 className="text-2xl font-bold mb-3">AI Processing</h3>
      <p className="text-gray-400 leading-relaxed">
        Our intelligent AI analyzes and rewrites your content.
      </p>
    </div>

    <div className="p-8 rounded-3xl bg-white/5 border border-white/10 backdrop-blur-xl">
      <div className="text-5xl font-black text-blue-400 mb-4">03</div>
      <h3 className="text-2xl font-bold mb-3">Get Results</h3>
      <p className="text-gray-400 leading-relaxed">
        Receive optimized and improved rewritten text instantly.
      </p>
    </div>

  </div>

</section>

      {/* ========= FEATURES ========= */}
      <section className="relative z-10 px-8 pb-24 max-w-6xl mx-auto">

        <h2 className="text-4xl font-bold tracking-tight mb-14 text-center">
          Powerful AI Tools
        </h2>

        <div className="group bg-white/[0.04] border border-white/10 p-8 rounded-3xl hover:bg-white/[0.07] hover:-translate-y-3 hover:border-purple-500/40 transition-all duration-500 backdrop-blur-xl relative overflow-hidden">

          <FeatureCard icon={<Sparkles />} title="Paraphraser" desc="Rewrite content smarter and faster" />
          <FeatureCard icon={<Languages />} title="Translator" desc="Translate across languages instantly" />
          <FeatureCard icon={<CheckCircle />} title="Grammar Fix" desc="Fix grammar with one click" />
          <FeatureCard icon={<MessageSquare />} title="AI Chat" desc="Chat with intelligent AI assistant" />

        </div>
      </section>

      {/* ========= CTA ========= */}
      <section className="relative z-10 px-6 pb-24">
        <div className="max-w-5xl mx-auto text-center bg-white/5 border border-white/10 rounded-2xl p-10 backdrop-blur-xl">

         <h2 className="text-4xl font-extrabold tracking-tight mb-5">
            Start using AI today
          </h2>

         <p className="text-gray-400 text-lg leading-relaxed mb-8 max-w-xl mx-auto">
            Join thousands of users improving their writing with AI.
          </p>

          <Link
            to="/dashboard"
          className="px-8 py-4 rounded-xl font-semibold tracking-wide  bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 transition"
          >
            Get Started Free
          </Link>

        </div>
      </section>
      {/* ========= FOOTER ========= */}
<footer className="relative z-10 border-t border-white/10 py-10 px-6">

  <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">

    <h1 className="text-2xl font-black bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
      Rephrasia AI
    </h1>

    <p className="text-gray-500 text-sm">
      © 2026 Rephrasia AI. All rights reserved.
    </p>
  </div>
</footer>
    </div>
  );
}

/* ========= TYPING PREVIEW ========= */
function TypingPreview() {
  const words = [
    { text: "AI ", highlight: false },
    { text: "is ", highlight: false },
    { text: "rapidly ", highlight: true },
    { text: "transforming ", highlight: true },
    { text: "the world, ", highlight: false },
    { text: "making it essential ", highlight: true },
    { text: "for individuals ", highlight: false },
    { text: "to use smarter tools ", highlight: true },
    { text: "to enhance productivity.", highlight: false },
  ];

  const [visibleWords, setVisibleWords] = useState([]);
  const [phase, setPhase] = useState("thinking");

  useEffect(() => {
    let interval;

    const runCycle = () => {
      setVisibleWords([]);
      setPhase("thinking");

      // STEP 1: Thinking
      setTimeout(() => {
        setPhase("rewriting");
      }, 1200);

      // STEP 2: Rewriting
      setTimeout(() => {
        setPhase("typing");

        let i = 0;

        interval = setInterval(() => {
          if (i >= words.length) {
            clearInterval(interval);

            // STEP 3: Pause then restart
            setTimeout(() => {
              runCycle(); // 🔁 LOOP AGAIN
            }, 2000);

            return;
          }

          if (words[i]) {
  if (words[i]) {
  setVisibleWords((prev) => [...prev, words[i]]);
}
}
          i++;
        }, 120);

      }, 2200);
    };

    runCycle();

    return () => clearInterval(interval);
  }, []);

  // ===== UI STATES =====

  if (phase === "thinking") {
    return (
      <span className="text-gray-400 animate-pulse">
        Analyzing text...
      </span>
    );
  }

  if (phase === "rewriting") {
    return (
      <span className="text-purple-400 animate-pulse">
        Rewriting with AI...
      </span>
    );
  }

  return (
    <span>
      {visibleWords
  .filter((word) => word)
  .map((word, index) => (
        <span
          key={index}
          className={
            word.highlight
              ? "text-purple-400 font-medium bg-purple-500/10 px-1 rounded"
              : ""
          }
        >
          {word.text}
        </span>
      ))}

      <span className="animate-pulse">|</span>
    </span>
  );
}
/* ========= FEATURE CARD ========= */
function FeatureCard({ icon, title, desc }) {
  return (
    <div className="group bg-white/[0.04] border border-white/10 p-6 rounded-2xl hover:bg-white/[0.07] hover:-translate-y-1 hover:border-purple-500/30 transition-all duration-300 backdrop-blur-xl relative overflow-hidden">

      {/* Content */}
      <div className="relative z-10">

        <div className="text-purple-400 mb-4">
          {icon}
        </div>

        <h3 className="font-semibold text-xl mb-3 tracking-tight">
          {title}
        </h3>

        <p className="text-gray-400 text-base leading-relaxed">
          {desc}
        </p>

      </div>

      {/* Hover Glow */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition duration-300 bg-gradient-to-br from-purple-500/5 to-transparent pointer-events-none"></div>

    </div>
  );
}
