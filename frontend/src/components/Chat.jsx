import { useState, useRef, useEffect } from "react";

const API = import.meta.env.VITE_API_URL;

export default function Chat({ session, onLogout }) {
  const [messages, setMessages] = useState(session.messages);
  const [text, setText] = useState("");
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [telegramStatus, setTelegramStatus] = useState("");
  const [dragging, setDragging] = useState(false);
  const bottomRef = useRef(null);
  const fileRef = useRef(null);

  const hasUserMessage = messages.some((m) => m.role === "user");

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  function getToken() {
    return localStorage.getItem("token");
  }

  function loadFile(file) {
    if (!file || !file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = reader.result.split(",")[1];
      setImage({ base64, mime: file.type, preview: reader.result });
    };
    reader.readAsDataURL(file);
  }

  function handleFile(e) { loadFile(e.target.files[0]); }

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    loadFile(e.dataTransfer.files[0]);
  }

  async function sendMessage(e) {
    e.preventDefault();
    if (!text.trim() && !image) return;
    setLoading(true);

    const optimistic = [];
    if (image) optimistic.push({ role: "user", kind: "image", content: image.preview });
    if (text.trim()) optimistic.push({ role: "user", kind: "text", content: text });
    setMessages((prev) => [...prev, ...optimistic]);

    const payload = {
      session_id: session.session_id,
      text: text.trim(),
      image_base64: image?.base64 ?? "",
      image_mime: image?.mime ?? "",
    };

    setText("");
    setImage(null);
    if (fileRef.current) fileRef.current.value = "";

    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${getToken()}` },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        setMessages((prev) => [...prev, { role: "assistant", kind: "text", content: `Error: ${data.detail ?? res.status}` }]);
      } else {
        setMessages((prev) => [...prev, { role: "assistant", kind: "text", content: data.reply }]);
      }
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", kind: "text", content: "Error connecting to server." }]);
    } finally {
      setLoading(false);
    }
  }

  async function sendTelegram() {
    setTelegramStatus("sending");
    try {
      const res = await fetch(`${API}/send-telegram`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${getToken()}` },
        body: JSON.stringify({ session_id: session.session_id }),
      });
      const data = await res.json();
      if (!res.ok) console.error("Telegram error:", data);
      setTelegramStatus(res.ok ? "success" : "error");
    } catch (err) {
      console.error("Telegram fetch error:", err);
      setTelegramStatus("error");
    }
    setTimeout(() => setTelegramStatus(""), 3000);
  }

  return (
    <div className="flex flex-col h-screen bg-slate-900">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-800 border-b border-slate-700 shadow-md">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🥗</span>
          <div>
            <h1 className="text-white font-bold text-lg leading-none">MacroSnap</h1>
            <p className="text-slate-400 text-xs">Hey {session.name}!</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={sendTelegram}
            disabled={!hasUserMessage || telegramStatus === "sending"}
            className="flex items-center gap-2 px-3 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium transition"
          >
            <span>✈️</span>
            {telegramStatus === "sending" ? "Sending..." : telegramStatus === "success" ? "Sent! ✅" : telegramStatus === "error" ? "Failed ❌" : "Send to Telegram"}
          </button>
          <button
            onClick={onLogout}
            className="px-3 py-2 rounded-xl bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm transition"
          >Logout</button>
        </div>
      </div>

      {/* Messages */}
      <div
        className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-3"
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        {dragging && (
          <div className="fixed inset-0 bg-blue-900/60 flex items-center justify-center z-50 pointer-events-none">
            <p className="text-white text-xl font-semibold">Drop your meal photo here 📸</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "assistant" && (
              <div className="w-7 h-7 rounded-full bg-green-500 flex items-center justify-center text-sm mr-2 mt-1 shrink-0">🥗</div>
            )}
            <div
              className={`max-w-[75%] rounded-2xl px-4 py-2 text-sm leading-relaxed whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-green-600 text-white rounded-br-sm"
                  : "bg-slate-700 text-slate-100 rounded-bl-sm"
              }`}
            >
              {msg.kind === "image" ? (
                <img src={msg.content} alt="meal" className="rounded-xl max-w-[200px]" />
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-green-500 flex items-center justify-center text-sm shrink-0">🥗</div>
            <div className="bg-slate-700 rounded-2xl rounded-bl-sm px-4 py-3 flex gap-1">
              <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:0ms]"></span>
              <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:150ms]"></span>
              <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:300ms]"></span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 bg-slate-800 border-t border-slate-700">
        {image && (
          <div className="mb-2 relative inline-block">
            <img src={image.preview} alt="preview" className="h-16 rounded-lg border border-slate-600" />
            <button
              onClick={() => { setImage(null); if (fileRef.current) fileRef.current.value = ""; }}
              className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 rounded-full text-white text-xs flex items-center justify-center"
            >✕</button>
          </div>
        )}
        <form onSubmit={sendMessage} className="flex gap-2 items-end">
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className="p-2.5 rounded-xl bg-slate-700 hover:bg-slate-600 text-slate-300 transition shrink-0"
            title="Attach photo"
          >📎</button>
          <input ref={fileRef} type="file" accept="image/jpg,image/jpeg,image/png" onChange={handleFile} className="hidden" />
          <input
            type="text"
            placeholder="Describe your meal or attach a photo..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={loading}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) sendMessage(e); }}
            className="flex-1 px-4 py-2.5 rounded-xl bg-slate-700 text-white placeholder-slate-400 border border-slate-600 focus:outline-none focus:border-green-500 transition text-sm"
          />
          <button
            type="submit"
            disabled={loading || (!text.trim() && !image)}
            className="p-2.5 rounded-xl bg-green-500 hover:bg-green-400 disabled:opacity-40 disabled:cursor-not-allowed text-white transition shrink-0"
          >➤</button>
        </form>
      </div>
    </div>
  );
}
