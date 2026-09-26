"use client";

import Link from "next/link";
import { Field, formValues, useJsonForm } from "../../../components/forms";

export default function NewProduct() {
  const { errors, busy, submit } = useJsonForm("/api/products", { onDone: (d, r) => { r.push(`/products/${d.id}`); r.refresh(); } });
  return (
    <>
      <h1>New product</h1>
      <p className="sub">Add something new to your catalogue.</p>
      <form className="card" noValidate onSubmit={(e) => { e.preventDefault(); submit(formValues(e.currentTarget)); }}>
        <Field label="Name" name="name" error={errors.name}>{(id) => <input id={id} name="name" data-testid="product-name" />}</Field>
        <Field label="SKU" name="sku" error={errors.sku} hint="Your own stock code, for example COF-002.">{(id) => <input id={id} name="sku" data-testid="product-sku" />}</Field>
        <Field label="Category" name="category">{(id) => (
          <select id={id} name="category" data-testid="product-category" defaultValue="Coffee">
            <option>Coffee</option><option>Kitchen</option><option>Equipment</option><option>Other</option>
          </select>
        )}</Field>
        <Field label="Price" name="price" error={errors.price}>{(id) => <input id={id} name="price" inputMode="decimal" data-testid="product-price" />}</Field>
        <Field label="Stock" name="stock" error={errors.stock}>{(id) => <input id={id} name="stock" inputMode="numeric" defaultValue="0" data-testid="product-stock" />}</Field>
        <div className="actions">
          <button className="btn primary" type="submit" disabled={busy} data-testid="save-product">Save product</button>
          <Link className="btn" href="/products">Cancel</Link>
        </div>
      </form>
    </>
  );
}
