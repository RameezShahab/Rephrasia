import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  FileText,
  Languages,
  CheckCircle,
  MessageSquare,
  History,
  Settings,
  Image as ImageIcon,
  File
} from "lucide-react";

function Sidebar({ collapsed }) {
  return (
    <aside
      className={`bg-gray-900 border-r border-gray-800 p-4 transition-all duration-300 
      ${collapsed ? "w-20" : "w-64"}`}
    >
      <div className="space-y-2">

        <SidebarLink to="/" icon={<LayoutDashboard size={20} />} label="Dashboard" collapsed={collapsed} />
        <SidebarLink to="/dashboard/paraphrase" icon={<FileText size={20} />} label="Paraphraser" collapsed={collapsed} />
        <SidebarLink to="/dashboard/translator" icon={<Languages size={20} />} label="Translator" collapsed={collapsed} />
        <SidebarLink to="/dashboard/grammar" icon={<CheckCircle size={20} />} label="Grammar Checker" collapsed={collapsed} />
        <SidebarLink to="/dashboard/ocr" icon={<ImageIcon size={20} />} label="OCR Scanner" collapsed={collapsed} />
        <SidebarLink to="/dashboard/documents" icon={<File size={20} />} label="Documents" collapsed={collapsed} />
        <SidebarLink to="/dashboard/history" icon={<History size={20} />} label="History" collapsed={collapsed} />
        <SidebarLink to="/dashboard/settings" icon={<Settings size={20} />} label="Settings" collapsed={collapsed} />

      </div>
    </aside>
  );
}

function SidebarLink({ to, icon, label, collapsed }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center ${collapsed ? "justify-center" : "gap-3"}
        px-4 py-3 rounded-xl transition-all duration-200 border-l-4
        ${
          isActive
            ? "bg-purple-600/20 text-white border-purple-500"
            : "text-gray-400 border-transparent hover:bg-gray-800 hover:text-white hover:border-purple-500"
        }`
      }
    >
      {icon}
      {!collapsed && <span>{label}</span>}
    </NavLink>
  );
}

export default Sidebar;
