import Link from "next/link";
import { load, money } from "../../lib/db";

export const dynamic = "force-dynamic";

export default function Products() {
  const db = load();
  return (
    <>
      <div className="toolbar">
        <div>
          <h1>Products</h1>
          <p className="sub">Everything you sell, with price and stock on hand.</p>
        </div>
        <Link className="btn primary" href="/products/new" data-testid="new-product">New product</Link>
      </div>
      <table data-testid="products-table">
        <thead><tr><th>Name</th><th>SKU</th><th>Category</th><th>Price</th><th>Stock</th></tr></thead>
        <tbody>
          {db.products.map((p) => (
            <tr key={p.id}>
              <td><Link href={`/products/${p.id}`}>{p.name}</Link></td>
              <td>{p.sku}</td>
              <td>{p.category}</td>
              <td>{money(db, p.price)}</td>
              <td className={p.stock <= db.settings.lowStockThreshold ? "low" : ""}>{p.stock}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
