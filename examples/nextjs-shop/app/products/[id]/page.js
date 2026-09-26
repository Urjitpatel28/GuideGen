import Link from "next/link";
import { notFound } from "next/navigation";
import { load, money } from "../../../lib/db";
import ActionButton from "../../../components/ActionButton";
import StockForm from "./StockForm";

export const dynamic = "force-dynamic";

export default async function ProductDetail({ params }) {
  const { id } = await params;
  const db = load();
  const p = db.products.find((x) => x.id === id);
  if (!p) notFound();
  return (
    <>
      <p><Link href="/products">← Products</Link></p>
      <h1>{p.name}</h1>
      <p className="sub">{p.category} · SKU {p.sku}</p>
      <div className="card">
        <dl className="details">
          <dt>Price</dt><dd>{money(db, p.price)}</dd>
          <dt>Stock on hand</dt><dd className={p.stock <= db.settings.lowStockThreshold ? "low" : ""}>{p.stock}</dd>
        </dl>
        <StockForm id={p.id} stock={p.stock} />
        <div className="actions">
          <ActionButton url={`/api/products/${p.id}`} method="DELETE" variant="danger" redirectTo="/products"
            confirmText="Delete this product?" testId="delete-product">Delete product</ActionButton>
        </div>
      </div>
    </>
  );
}
