import { NextResponse } from "next/server";
import { load, save, nextId } from "../../../lib/db";
import { validateCustomer } from "../../../lib/validate";

export async function POST(req) {
  const body = await req.json();
  const errors = validateCustomer(body);
  if (Object.keys(errors).length) return NextResponse.json({ errors }, { status: 400 });
  const db = load();
  const c = { id: nextId("c", db.customers), name: body.name.trim(), email: body.email.trim(), phone: body.phone || "", city: body.city || "" };
  db.customers.push(c);
  save(db);
  return NextResponse.json({ ok: true, id: c.id });
}
