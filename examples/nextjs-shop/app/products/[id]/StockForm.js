"use client";

import { Field, formValues, useJsonForm } from "../../../components/forms";

export default function StockForm({ id, stock }) {
  const { errors, busy, submit } = useJsonForm(`/api/products/${id}`, { method: "PATCH" });
  return (
    <form noValidate onSubmit={(e) => { e.preventDefault(); submit(formValues(e.currentTarget)); }} style={{ marginTop: 18, maxWidth: 320 }}>
      <Field label="Adjust stock" name="stock" error={errors.stock}>{(id2) => <input id={id2} name="stock" defaultValue={stock} data-testid="stock-input" />}</Field>
      <button className="btn" type="submit" disabled={busy} data-testid="update-stock">Update stock</button>
    </form>
  );
}
