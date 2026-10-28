import { useState } from "react";

const API = import.meta.env.VITE_API_URL;

export default function Auth({ onDone }) {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const payload = mode === "register"
      ? { name: name.trim(), email, password }
      : { email, password };

    try {
      const res = await fetch(`${API}/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail ?? "Something went wrong");
        return;
      }
      localStorage.setItem("token", data.token);
      onDone({
        session_id: data.session_id,
        name: data.name,
        messages: [{ role: "assistant", kind: "text", content: data.welcome }],
      });
    } catch {
      setError("Failed to connect to server");
    } finally {
      setLoading(false);
    }
  }

  function switchMode() {
    setMode(mode === "login" ? "register" : "login");
    setError("");
    setName("");
    setEmail("");
    setPassword("");
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
          {mode === "register" && (
            <input
              type="text"
              placeholder="Your name"
              value={name}
              onChange={(e) => { setName(e.target.value); setError(""); }}
              className="w-full px-4 py-3 rounded-xl bg-slate-700 text-white placeholder-slate-400 border border-slate-600 focus:outline-none focus:border-green-500 transition"
            />
          )}
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => { setEmail(e.target.value); setError(""); }}
            className="w-full px-4 py-3 rounded-xl bg-slate-700 text-white placeholder-slate-400 border border-slate-600 focus:outline-none focus:border-green-500 transition"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => { setPassword(e.target.value); setError(""); }}
            className="w-full px-4 py-3 rounded-xl bg-slate-700 text-white placeholder-slate-400 border border-slate-600 focus:outline-none focus:border-green-500 transition"
          />
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-green-500 hover:bg-green-400 disabled:opacity-50 text-white font-semibold transition"
          >
            {loading ? "Please wait..." : mode === "login" ? "Login 🚀" : "Create Account 🚀"}
          </button>
        </form>

        <p className="text-slate-400 text-sm">
          {mode === "login" ? "Don't have an account?" : "Already have an account?"}{" "}
          <button onClick={switchMode} className="text-green-400 hover:underline font-medium">
            {mode === "login" ? "Register" : "Login"}
          </button>
        </p>
      </div>
    </div>
  );
}
