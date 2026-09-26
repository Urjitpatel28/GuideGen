"use client";

import Link from "next/link";
import { Field, formValues, useJsonForm } from "../../../components/forms";

export default function NewCustomer() {
  const { errors, busy, submit } = useJsonForm("/api/customers", { onDone: (_d, r) => { r.push("/customers"); r.refresh(); } });
  return (
    <>
      <h1>New customer</h1>
      <p className="sub">Customers must exist before you can create orders for them.</p>
      <form className="card" noValidate onSubmit={(e) => { e.preventDefault(); submit(formValues(e.currentTarget)); }}>
        <Field label="Name" name="name" error={errors.name}>{(id) => <input id={id} name="name" data-testid="customer-name" />}</Field>
        <Field label="Email" name="email" error={errors.email}>{(id) => <input id={id} name="email" type="email" data-testid="customer-email" />}</Field>
        <Field label="Phone" name="phone">{(id) => <input id={id} name="phone" data-testid="customer-phone" />}</Field>
        <Field label="City" name="city">{(id) => <input id={id} name="city" data-testid="customer-city" />}</Field>
        <div className="actions">
          <button className="btn primary" type="submit" disabled={busy} data-testid="save-customer">Save customer</button>
          <Link className="btn" href="/customers">Cancel</Link>
        </div>
      </form>
    </>
  );
}
