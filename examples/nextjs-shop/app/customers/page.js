import Link from "next/link";
import { load } from "../../lib/db";

export const dynamic = "force-dynamic";

export default function Customers() {
  const db = load();
  return (
    <>
      <div className="toolbar">
        <div>
          <h1>Customers</h1>
          <p className="sub">People and businesses you sell to.</p>
        </div>
        <Link className="btn primary" href="/customers/new" data-testid="new-customer">New customer</Link>
      </div>
      <table data-testid="customers-table">
        <thead><tr><th>Name</th><th>Email</th><th>Phone</th><th>City</th><th>Orders</th></tr></thead>
        <tbody>
          {db.customers.map((c) => (
            <tr key={c.id}>
              <td>{c.name}</td><td>{c.email}</td><td>{c.phone}</td><td>{c.city}</td>
              <td>{db.orders.filter((o) => o.customerId === c.id).length}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
