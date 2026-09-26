import { NextResponse } from "next/server";
import { load, save } from "../../../lib/db";
import { validateSettings } from "../../../lib/validate";

export async function POST(req) {
  const body = await req.json();
  const errors = validateSettings(body);
  if (Object.keys(errors).length) return NextResponse.json({ errors }, { status: 400 });
  const db = load();
  db.settings = {
    storeName: body.storeName.trim(),
    currency: body.currency,
    lowStockThreshold: Number(body.lowStockThreshold),
    emailNotifications: Boolean(body.emailNotifications),
  };
  save(db);
  return NextResponse.json({ ok: true });
}
