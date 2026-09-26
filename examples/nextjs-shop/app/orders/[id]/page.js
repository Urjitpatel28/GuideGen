import Link from "next/link";
import { notFound } from "next/navigation";
import { load, money, orderTotal } from "../../../lib/db";
import ActionButton from "../../../components/ActionButton";

export const dynamic = "force-dynamic";

export default async function OrderDetail({ params }) {
  const { id } = await params;
  const db = load();
  const o = db.orders.find((x) => x.id === id);
  if (!o) notFound();
  const customer = db.customers.find((c) => c.id === o.customerId);
  return (
    <>
      <p><Link href="/orders">← Orders</Link></p>
      <h1>Order {o.id.toUpperCase()} <span className={`pill ${o.status}`}>{o.status}</span></h1>
      <p className="sub">Placed {o.createdAt} by {customer?.name}</p>
      <div className="card">
        <table>
          <thead><tr><th>Product</th><th>Quantity</th><th>Price</th><th>Line total</th></tr></thead>
          <tbody>
            {o.items.map((it) => {
              const p = db.products.find((x) => x.id === it.productId);
              return (
                <tr key={it.productId}>
                  <td>{p?.name}</td><td>{it.quantity}</td><td>{money(db, p?.price || 0)}</td><td>{money(db, (p?.price || 0) * it.quantity)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <p><strong>Total: {money(db, orderTotal(db, o))}</strong></p>
        {o.note && <p>Note: {o.note}</p>}
        <p>Invoice email: {customer?.email}</p>
        <div className="actions">
          {o.status === "Open" && <ActionButton url={`/api/orders/${o.id}`} body={{ action: "ship" }} variant="primary" testId="mark-shipped">Mark as shipped</ActionButton>}
          <ActionButton url={`/api/orders/${o.id}`} body={{ action: "invoice" }} testId="send-invoice">Send invoice</ActionButton>
        </div>
      </div>
    </>
  );
}
