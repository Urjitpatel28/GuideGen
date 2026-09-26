"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

// Submit JSON to an API route; show field errors; navigate on success.
export function useJsonForm(url, { method = "POST", onDone } = {}) {
  const router = useRouter();
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);

  async function submit(values) {
    setBusy(true);
    setErrors({});
    const res = await fetch(url, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(values) });
    const data = await res.json().catch(() => ({}));
    setBusy(false);
    if (!res.ok) {
      setErrors(data.errors || { form: data.error || "Something went wrong" });
      return;
    }
    onDone ? onDone(data, router) : router.refresh();
  }
  return { errors, busy, submit };
}

export function Field({ label, name, error, children, hint }) {
  const id = `f-${name}`;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      {children(id)}
      {hint && !error && <p className="hint">{hint}</p>}
      {error && <p className="error" role="alert" data-testid={`error-${name}`}>{error}</p>}
    </div>
  );
}

export function formValues(form) {
  const fd = new FormData(form);
  const out = {};
  for (const [k, v] of fd.entries()) out[k] = v;
  form.querySelectorAll("input[type=checkbox]").forEach((c) => (out[c.name] = c.checked));
  return out;
}
