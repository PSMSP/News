import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useState, useEffect } from "react";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import TickerDetail from "./pages/TickerDetail";

function App() {
  const [username, setUsername] = useState(
    () => localStorage.getItem("username") || ""
  );

  useEffect(() => {
    if (username) {
      localStorage.setItem("username", username);
    } else {
      localStorage.removeItem("username");
    }
  }, [username]);

  if (!username) {
    return <Login onLogin={setUsername} />;
  }

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-gray-100">
        <header className="border-b border-gray-800 bg-gray-900 px-6 py-3 flex items-center justify-between">
          <a href="/" className="text-lg font-semibold tracking-tight text-white">
            NewsFlow
          </a>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-400">{username}</span>
            <button
              onClick={() => setUsername("")}
              className="text-sm text-gray-500 hover:text-gray-300 cursor-pointer"
            >
              Switch User
            </button>
          </div>
        </header>
        <main className="max-w-5xl mx-auto px-6 py-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/ticker/:watchlistId" element={<TickerDetail />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
