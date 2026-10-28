import { useState, useEffect } from "react";
import Auth from "./components/Onboarding";
import Chat from "./components/Chat";

const API = import.meta.env.VITE_API_URL;

export default function App() {
  const [session, setSession] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) { setChecking(false); return; }

    fetch(`${API}/me`, { headers: { "Authorization": `Bearer ${token}` } })
      .then((r) => r.ok ? r.json() : null)
      .then((data) => {
        if (data) setSession({ session_id: data.session_id, name: data.name, messages: data.messages });
        else localStorage.removeItem("token");
      })
      .catch(() => localStorage.removeItem("token"))
      .finally(() => setChecking(false));
  }, []);

  function handleLogout() {
    localStorage.removeItem("token");
    setSession(null);
  }

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <span className="text-4xl animate-spin">🥗</span>
      </div>
    );
  }

  return session ? (
    <Chat session={session} onLogout={handleLogout} />
  ) : (
    <Auth onDone={setSession} />
  );
}
