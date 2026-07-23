import { Routes, Route } from "react-router-dom";

import MainLayout from "./layout/MainLayout";

import LandingPage from "./pages/landingpage";
import Dashboard from "./pages/dashboard";
import Paraphrase from "./pages/paraphrase";
import Translator from "./pages/translate";
import Grammar from "./pages/grammar";
import History from "./pages/history";
import Settings from "./pages/settings";
import OcrScanner from "./pages/ocr";
import DocumentProcessor from "./pages/documents";

function App() {
  return (
    <Routes>

      {/* LANDING */}
      <Route path="/" element={<LandingPage />} />

      {/* DASHBOARD LAYOUT */}
      <Route path="/dashboard" element={<MainLayout />}>

        <Route index element={<Dashboard />} />

        <Route path="paraphrase" element={<Paraphrase />} />

        <Route path="translator" element={<Translator />} />

        <Route path="grammar" element={<Grammar />} />

        <Route path="ocr" element={<OcrScanner />} />
        <Route path="documents" element={<DocumentProcessor />} />
        <Route path="history" element={<History />} />
        <Route path="settings" element={<Settings />} />

      </Route>

    </Routes>
  );
}

export default App;