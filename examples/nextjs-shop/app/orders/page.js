import Link from "next/link";
import { load, money, orderTotal } from "../../lib/db";

export const dynamic = "force-dynamic";

export default function Orders() {
  const db = load();
  const orders = [...db.orders].sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  return (
    <>
      <div className="toolbar">
        <div>
          <h1>Orders</h1>
          <p className="sub">All customer orders, newest first.</p>
        </div>
        <Link className="btn primary" href="/orders/new" data-testid="new-order">New order</Link>
      </div>
      <table data-testid="orders-table">
        <thead><tr><th>Order</th><th>Customer</th><th>Date</th><th>Items</th><th>Total</th><th>Status</th></tr></thead>
        <tbody>
          {orders.map((o) => (
            <tr key={o.id}>
              <td><Link href={`/orders/${o.id}`}>{o.id.toUpperCase()}</Link></td>
              <td>{db.customers.find((c) => c.id === o.customerId)?.name}</td>
              <td>{o.createdAt}</td>
              <td>{o.items.reduce((s, i) => s + i.quantity, 0)}</td>
              <td>{money(db, orderTotal(db, o))}</td>
              <td><span className={`pill ${o.status}`}>{o.status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
