"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

// A button that calls an API route and then refreshes or navigates.
export default function ActionButton({ url, method = "POST", body, children, variant = "secondary", confirmText, redirectTo, testId }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState("");

  async function run() {
    if (confirmText && !window.confirm(confirmText)) return;
    setBusy(true);
    await fetch(url, { method, headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
    setBusy(false);
    setDone("Done");
    if (redirectTo) router.push(redirectTo);
    else router.refresh();
  }

  return (
    <button type="button" className={`btn ${variant}`} onClick={run} disabled={busy} data-testid={testId}>
      {busy ? "Working…" : children}
      {done && <span className="visually-hidden"> {done}</span>}
    </button>
  );
}
