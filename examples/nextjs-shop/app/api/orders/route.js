import { NextResponse } from "next/server";
import { load, save, nextId } from "../../../lib/db";
import { validateOrder } from "../../../lib/validate";

export async function POST(req) {
  const body = await req.json();
  const db = load();
  const product = db.products.find((p) => p.id === body.productId);
  const errors = validateOrder(body, product);
  if (Object.keys(errors).length) return NextResponse.json({ errors }, { status: 400 });
  const order = {
    id: nextId("o", db.orders),
    customerId: body.customerId,
    items: [{ productId: body.productId, quantity: Number(body.quantity) }],
    status: "Open",
    createdAt: new Date().toISOString().slice(0, 10),
    note: body.note || "",
  };
  product.stock -= Number(body.quantity);
  db.orders.push(order);
  save(db);
  return NextResponse.json({ ok: true, id: order.id });
}
