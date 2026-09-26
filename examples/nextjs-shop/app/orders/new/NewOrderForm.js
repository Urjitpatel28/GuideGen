"use client";

import Link from "next/link";
import { Field, formValues, useJsonForm } from "../../../components/forms";

export default function NewOrderForm({ customers, products }) {
  const { errors, busy, submit } = useJsonForm("/api/orders", { onDone: (d, r) => { r.push(`/orders/${d.id}`); r.refresh(); } });
  return (
    <form className="card" noValidate onSubmit={(e) => { e.preventDefault(); submit(formValues(e.currentTarget)); }}>
      <Field label="Customer" name="customerId" error={errors.customerId}>{(id) => (
        <select id={id} name="customerId" defaultValue="" data-testid="order-customer">
          <option value="">Choose a customer…</option>
          {customers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      )}</Field>
      <Field label="Product" name="productId" error={errors.productId}>{(id) => (
        <select id={id} name="productId" defaultValue="" data-testid="order-product">
          <option value="">Choose a product…</option>
          {products.map((p) => <option key={p.id} value={p.id}>{p.name} ({p.stock} in stock)</option>)}
        </select>
      )}</Field>
      <Field label="Quantity" name="quantity" error={errors.quantity}>{(id) => <input id={id} name="quantity" inputMode="numeric" defaultValue="1" data-testid="order-quantity" />}</Field>
      <Field label="Note" name="note" hint="Optional. Shown on the order.">{(id) => <textarea id={id} name="note" rows={3} data-testid="order-note" />}</Field>
      <div className="actions">
        <button className="btn primary" type="submit" disabled={busy} data-testid="save-order">Create order</button>
        <Link className="btn" href="/orders">Cancel</Link>
      </div>
    </form>
  );
}
