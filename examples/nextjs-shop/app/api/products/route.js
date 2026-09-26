import { NextResponse } from "next/server";
import { load, save, nextId } from "../../../lib/db";
import { validateProduct } from "../../../lib/validate";

export async function POST(req) {
  const body = await req.json();
  const errors = validateProduct(body);
  if (Object.keys(errors).length) return NextResponse.json({ errors }, { status: 400 });
  const db = load();
  const product = {
    id: nextId("p", db.products),
    name: body.name.trim(),
    sku: body.sku.trim(),
    price: Number(body.price),
    stock: Number(body.stock),
    category: body.category || "Other",
  };
  db.products.push(product);
  save(db);
  return NextResponse.json({ ok: true, id: product.id });
}
