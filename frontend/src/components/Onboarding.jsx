import { useState } from "react";

const API = "http://localhost:8000";

export default function Onboarding({ onDone }) {
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!name.trim()) return setError("Please enter your name");
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API}/onboard`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      const data = await res.json();
      onDone({
        session_id: data.session_id,
        name: name.trim(),
        messages: [{ role: "assistant", kind: "text", content: data.welcome }],
      });
    } catch {
      setError("Failed to connect to server");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
      <div className="w-full max-w-md bg-slate-800 rounded-2xl shadow-2xl p-8 flex flex-col items-center gap-6">
        <div className="text-5xl">🥗</div>
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white">MacroSnap</h1>
          <p className="text-slate-400 mt-1">Your AI nutrition buddy</p>
        </div>

        <form onSubmit={handleSubmit} className="w-full flex flex-col gap-3">
          <input
            type="text"
            placeholder="What's your name?"
            value={name}
            onChange={(e) => { setName(e.target.value); setError(""); }}
            className="w-full px-4 py-3 rounded-xl bg-slate-700 text-white placeholder-slate-400 border border-slate-600 focus:outline-none focus:border-green-500 transition"
          />
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-green-500 hover:bg-green-400 disabled:opacity-50 text-white font-semibold transition"
          >
            {loading ? "Setting up..." : "Let's go 🚀"}
          </button>
        </form>

        <p className="text-slate-500 text-xs text-center">
          Snap a photo or describe your meal — get instant calorie & macro estimates
        </p>
      </div>
    </div>
  );
}
