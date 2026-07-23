import {
  Search,
  Bell,
  TrendingUp,
  FileText,
  Zap,
  Clock3,
  Wand2,
  PenSquare,
  CheckCircle,
  Languages,
} from "lucide-react";

import { motion } from "framer-motion";

export default function DashboardPage() {
  return (
    <div className="relative min-h-screen bg-[#030712] text-white overflow-hidden flex">

      {/* ========= BACKGROUND ========= */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(168,85,247,0.14),transparent_35%)]" />

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,rgba(59,130,246,0.10),transparent_35%)]" />

        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:55px_55px]" />

      </div>

      {/* ========= MAIN ========= */}
      <main className="relative z-10 flex-1 p-8 overflow-y-auto">

        {/* ========= TOPBAR ========= */}
        <div className="flex items-center justify-between mb-10">

          {/* SEARCH */}
          <div className="relative w-[380px]">

            <Search
              className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500"
              size={18}
            />

            <input
              type="text"
              placeholder="Search workspace..."
              className="w-full bg-white/[0.04] border border-white/10 rounded-2xl py-3 pl-12 pr-4 outline-none focus:border-purple-500/40 transition backdrop-blur-xl"
            />

          </div>

          {/* PROFILE */}
          <div className="flex items-center gap-4">

            <button className="relative w-12 h-12 rounded-2xl border border-white/10 bg-white/[0.04] flex items-center justify-center hover:border-purple-500/30 transition">
              <Bell size={18} />
              <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-pink-500"></span>
            </button>

            <div className="flex items-center gap-3 bg-white/[0.04] border border-white/10 rounded-2xl px-4 py-2 backdrop-blur-xl">

              <div className="w-11 h-11 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center font-bold">
                RJ
              </div>

              <div>
                <h3 className="font-semibold">Rafay Javed</h3>
                <p className="text-xs text-purple-400">AI Researcher</p>
              </div>

            </div>

          </div>

        </div>

        {/* ========= HERO ========= */}
        <motion.div
          initial={{ opacity: 0, y: 25 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-purple-900/20 via-[#050816] to-blue-900/10 p-10 mb-10"
        >

          <div className="absolute top-0 right-0 w-80 h-80 bg-purple-500/20 blur-[120px] rounded-full" />

          <div className="relative z-10 max-w-3xl">

            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-purple-500/20 bg-white/[0.04] mb-6">
              <Zap size={16} className="text-purple-400" />
              <span className="text-sm text-gray-300">
                Smart AI Workspace
              </span>
            </div>

            <h1 className="text-5xl font-black mb-5">
              Create Better Content{" "}
              <span className="bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
                Faster
              </span>
            </h1>

            <p className="text-xl text-gray-400 mb-8 max-w-2xl">
              Rewrite, improve grammar, translate languages, and generate AI-powered content in seconds.
            </p>

            <button className="px-8 py-4 rounded-2xl bg-gradient-to-r from-purple-500 to-pink-500 font-semibold hover:scale-105 transition">
              Start Writing
            </button>

          </div>

        </motion.div>

        {/* ========= STATS ========= */}
        <div className="grid md:grid-cols-3 gap-6 mb-10">

          <StatsCard icon={<TrendingUp size={20} />} title="Words Generated" value="12,450" />
          <StatsCard icon={<FileText size={20} />} title="Documents Created" value="84" />
          <StatsCard icon={<Zap size={20} />} title="AI Requests" value="320" />

        </div>

        {/* ========= QUICK ACTIONS ========= */}
        <div className="mb-10">

          <h2 className="text-3xl font-black mb-6">Quick Actions</h2>

          <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-6">

            <QuickAction icon={<Wand2 size={22} />} title="Continue Writing" />
            <QuickAction icon={<PenSquare size={22} />} title="Generate Blog Intro" />
            <QuickAction icon={<CheckCircle size={22} />} title="Fix Grammar" />
            <QuickAction icon={<Languages size={22} />} title="Translate File" />

          </div>

        </div>

        {/* ========= LOWER GRID ========= */}
        <div className="grid xl:grid-cols-3 gap-6">

          {/* GRAPH */}
          <div className="xl:col-span-2 rounded-2xl border border-white/10 bg-white/[0.04] p-8">

            <div className="flex justify-between mb-8">
              <h2 className="text-2xl font-bold">Weekly AI Usage</h2>
              <span className="text-green-400 text-sm">+18% Growth</span>
            </div>

            <div className="flex items-end gap-4 h-[260px]">

              {[40, 65, 55, 90, 70, 110, 85].map((h, i) => (
                <motion.div
                  key={i}
                  initial={{ height: 0 }}
                  animate={{ height: `${h}%` }}
                  transition={{ duration: 0.6, delay: i * 0.1 }}
                  className="flex-1 bg-gradient-to-t from-purple-500 to-pink-500 rounded-t-2xl min-h-[40px]"
                />
              ))}

            </div>

          </div>

          {/* ACTIVITY */}
          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-8">

            <div className="flex justify-between mb-6">
              <h2 className="text-2xl font-bold">Recent Activity</h2>
              <Clock3 size={18} className="text-purple-400" />
            </div>

            <div className="space-y-5">

              <Activity title="Paraphrased Blog Article" time="2h ago" />
              <Activity title="Translated Paper" time="Yesterday" />
              <Activity title="Grammar Fix" time="3 days ago" />

            </div>

          </div>

        </div>

      </main>
    </div>
  );
}

/* ========= STATS ========= */
function StatsCard({ icon, title, value }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 hover:-translate-y-1 transition">
      <div className="text-purple-400 mb-4">{icon}</div>
      <p className="text-gray-400 text-sm">{title}</p>
      <h3 className="text-3xl font-bold">{value}</h3>
    </div>
  );
}

/* ========= QUICK ACTION ========= */
function QuickAction({ icon, title }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 hover:border-purple-500/30 transition">
      <div className="text-purple-400 mb-4">{icon}</div>
      <p className="font-medium">{title}</p>
    </div>
  );
}

/* ========= ACTIVITY ========= */
function Activity({ title, time }) {
  return (
    <div className="flex justify-between border-b border-white/5 pb-3">
      <div>
        <p className="font-medium">{title}</p>
        <p className="text-xs text-gray-500">AI processed successfully</p>
      </div>
      <span className="text-xs text-gray-500">{time}</span>
    </div>
  );
}