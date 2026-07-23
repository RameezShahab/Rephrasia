import { useState } from "react";
import { motion } from "framer-motion";
import { User, Bell, Shield, Palette, Globe, Key, Save } from "lucide-react";

export default function Settings() {

  const [name, setName] = useState("Rafay Javed");
  const [email, setEmail] = useState("rafay@example.com");

  const [notifications, setNotifications] = useState(true);
  const [darkMode, setDarkMode] = useState(true);

  return (
    <div className="relative min-h-screen text-white p-8">

      {/* BACKGROUND */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(168,85,247,0.15),transparent_40%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,rgba(59,130,246,0.12),transparent_40%)]" />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto">

        {/* HEADER */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10"
        >
          <h1 className="text-4xl font-bold flex items-center gap-2">
            <User className="text-purple-400" />
            Settings
          </h1>
          <p className="text-gray-400 mt-2">
            Manage your account and AI workspace preferences
          </p>
        </motion.div>

        {/* GRID */}
        <div className="grid lg:grid-cols-2 gap-6">

          {/* PROFILE */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="p-6 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl"
          >

            <div className="flex items-center gap-2 mb-6">
              <User size={18} className="text-purple-400" />
              <h2 className="text-xl font-semibold">Profile</h2>
            </div>

            <div className="space-y-4">

              <div>
                <label className="text-sm text-gray-400">Name</label>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full mt-1 px-4 py-3 rounded-xl bg-white/5 border border-white/10 outline-none focus:border-purple-500/30"
                />
              </div>

              <div>
                <label className="text-sm text-gray-400">Email</label>
                <input
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full mt-1 px-4 py-3 rounded-xl bg-white/5 border border-white/10 outline-none focus:border-purple-500/30"
                />
              </div>

            </div>

          </motion.div>

          {/* PREFERENCES */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="p-6 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl"
          >

            <div className="flex items-center gap-2 mb-6">
              <Palette size={18} className="text-purple-400" />
              <h2 className="text-xl font-semibold">Preferences</h2>
            </div>

            <div className="space-y-4">

              {/* Notifications */}
              <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10">
                <div className="flex items-center gap-2">
                  <Bell size={16} />
                  <span>Notifications</span>
                </div>

                <input
                  type="checkbox"
                  checked={notifications}
                  onChange={() => setNotifications(!notifications)}
                  className="w-5 h-5 accent-purple-500"
                />
              </div>

              {/* Dark Mode */}
              <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10">
                <div className="flex items-center gap-2">
                  <Palette size={16} />
                  <span>Dark Mode</span>
                </div>

                <input
                  type="checkbox"
                  checked={darkMode}
                  onChange={() => setDarkMode(!darkMode)}
                  className="w-5 h-5 accent-purple-500"
                />
              </div>

            </div>

          </motion.div>

        </div>

        {/* SECURITY CARD */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 p-6 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl"
        >

          <div className="flex items-center gap-2 mb-4">
            <Shield size={18} className="text-purple-400" />
            <h2 className="text-xl font-semibold">Security</h2>
          </div>

          <div className="flex flex-col md:flex-row gap-4">

            <button className="flex items-center gap-2 px-5 py-3 rounded-xl bg-white/5 border border-white/10 hover:border-purple-500/30">
              <Key size={16} />
              Change Password
            </button>

            <button className="flex items-center gap-2 px-5 py-3 rounded-xl bg-white/5 border border-white/10 hover:border-purple-500/30">
              <Globe size={16} />
              Login Sessions
            </button>

          </div>

        </motion.div>

        {/* SAVE BUTTON */}
        <div className="mt-8 flex justify-end">

          <button className="flex items-center gap-2 px-7 py-4 rounded-2xl bg-gradient-to-r from-purple-500 to-pink-500 font-semibold hover:scale-105 transition">

            <Save size={18} />
            Save Changes

          </button>

        </div>

        {/* FOOTER */}
        <div className="mt-12 border-t border-white/10 pt-6 text-center text-gray-500 text-sm">

          Rephrasia AI • Settings Panel • Secure Workspace

        </div>

      </div>
    </div>
  );
}