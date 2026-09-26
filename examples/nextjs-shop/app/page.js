import Link from "next/link";
import { load, money, orderTotal } from "../lib/db";

export const dynamic = "force-dynamic";

export default function Dashboard() {
  const db = load();
  const open = db.orders.filter((o) => o.status === "Open");
  const revenue = db.orders.reduce((s, o) => s + orderTotal(db, o), 0);
  const low = db.products.filter((p) => p.stock <= db.settings.lowStockThreshold);
  const recent = [...db.orders].sort((a, b) => b.createdAt.localeCompare(a.createdAt)).slice(0, 5);

  return (
    <>
      <h1>Dashboard</h1>
      <p className="sub">Welcome back. Here is how {db.settings.storeName} is doing.</p>
      <div className="stats">
        <div className="card stat" data-testid="stat-open-orders"><strong>{open.length}</strong><span>Open orders</span></div>
        <div className="card stat"><strong>{money(db, revenue)}</strong><span>Total sales</span></div>
        <div className="card stat"><strong>{db.customers.length}</strong><span>Customers</span></div>
        <div className="card stat"><strong className={low.length ? "low" : ""}>{low.length}</strong><span>Low-stock products</span></div>
      </div>
      <div className="toolbar">
        <h2>Recent orders</h2>
        <Link className="btn primary" href="/orders/new" data-testid="dashboard-new-order">New order</Link>
      </div>
      <table>
        <thead><tr><th>Order</th><th>Customer</th><th>Date</th><th>Total</th><th>Status</th></tr></thead>
        <tbody>
          {recent.map((o) => (
            <tr key={o.id}>
              <td><Link href={`/orders/${o.id}`}>{o.id.toUpperCase()}</Link></td>
              <td>{db.customers.find((c) => c.id === o.customerId)?.name}</td>
              <td>{o.createdAt}</td>
              <td>{money(db, orderTotal(db, o))}</td>
              <td><span className={`pill ${o.status}`}>{o.status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
