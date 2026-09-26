import { NextResponse } from "next/server";
import { load, save } from "../../../../lib/db";

// action: "ship" marks the order as shipped; "invoice" pretends to email an invoice.
export async function POST(req, { params }) {
  const { id } = await params;
  const { action } = await req.json();
  const db = load();
  const order = db.orders.find((o) => o.id === id);
  if (!order) return NextResponse.json({ error: "Not found" }, { status: 404 });
  if (action === "ship") order.status = "Shipped";
  if (action === "invoice") order.invoicedAt = new Date().toISOString();
  save(db);
  return NextResponse.json({ ok: true });
}
