"use client";

import { useRouter } from "next/navigation";
import { Field, formValues, useJsonForm } from "../../components/forms";

export default function LoginPage() {
  const router = useRouter();
  const { errors, busy, submit } = useJsonForm("/api/login", { onDone: () => { router.push("/"); router.refresh(); } });

  return (
    <form className="card login" onSubmit={(e) => { e.preventDefault(); submit(formValues(e.currentTarget)); }}>
      <img src="/logo.svg" alt="Acme Shop" width="56" height="56" />
      <h1>Sign in to Acme Shop</h1>
      <Field label="Email" name="email">{(id) => <input id={id} name="email" type="email" autoComplete="username" data-testid="login-email" />}</Field>
      <Field label="Password" name="password">{(id) => <input id={id} name="password" type="password" autoComplete="current-password" data-testid="login-password" />}</Field>
      {errors.form && <p className="form-error" role="alert">{errors.form}</p>}
      <div className="actions">
        <button className="btn primary" type="submit" disabled={busy} data-testid="login-submit">Sign in</button>
      </div>
    </form>
  );
}
