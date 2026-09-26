import { load } from "../../../lib/db";
import NewOrderForm from "./NewOrderForm";

export const dynamic = "force-dynamic";

export default function NewOrder() {
  const db = load();
  return (
    <>
      <h1>New order</h1>
      <p className="sub">Record an order for an existing customer.</p>
      <NewOrderForm
        customers={db.customers.map((c) => ({ id: c.id, name: c.name }))}
        products={db.products.map((p) => ({ id: p.id, name: p.name, stock: p.stock }))}
      />
    </>
  );
}
