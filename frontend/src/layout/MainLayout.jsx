import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import CopilotSidebar from "../components/CopilotSidebar";
import { Menu } from "lucide-react";

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">

      {/* NAVBAR */}
      <nav className="h-16 flex items-center justify-between px-6 
backdrop-blur-xl bg-white/5 border-b border-white/10 sticky top-0 z-50">

        
        <div className="flex items-center gap-4">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-2 rounded-lg hover:bg-gray-800 transition"
          >
            <Menu size={20} />
          </button>

          <h1 className="text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
            Rephrasia AI
          </h1>
        </div>

        <div className="flex items-center gap-6">
          <button className="px-4 py-2 bg-gray-800 rounded-lg hover:bg-gray-700 transition">
            Upgrade
          </button>
          <div className="w-8 h-8 bg-purple-500 rounded-full"></div>
        </div>
      </nav>

      <div className="flex flex-1">
        <Sidebar collapsed={collapsed} />
        <main className="flex-1 p-10 transition-all duration-300">
          <Outlet />
        </main>
      </div>

      <CopilotSidebar />
    </div>
  );
}
