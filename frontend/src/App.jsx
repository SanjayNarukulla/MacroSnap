import { useState } from "react";
import Onboarding from "./components/Onboarding";
import Chat from "./components/Chat";

export default function App() {
  const [session, setSession] = useState(null); // { session_id, name, messages }

  return session ? (
    <Chat session={session} setSession={setSession} />
  ) : (
    <Onboarding onDone={setSession} />
  );
}
