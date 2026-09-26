import { NextResponse } from "next/server";
import { load, save } from "../../../../lib/db";
import { MESSAGES } from "../../../../lib/validate";

export async function PATCH(req, { params }) {
  const { id } = await params;
  const { stock } = await req.json();
  if (Number(stock) < 0 || isNaN(Number(stock))) return NextResponse.json({ errors: { stock: MESSAGES.stockNegative } }, { status: 400 });
  const db = load();
  const p = db.products.find((x) => x.id === id);
  if (!p) return NextResponse.json({ error: "Not found" }, { status: 404 });
  p.stock = Number(stock);
  save(db);
  return NextResponse.json({ ok: true });
}

export async function DELETE(_req, { params }) {
  const { id } = await params;
  const db = load();
  db.products = db.products.filter((x) => x.id !== id);
  save(db);
  return NextResponse.json({ ok: true });
}
