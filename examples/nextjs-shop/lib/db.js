// Tiny JSON-file store. Good enough for an example app; never use this in production.
import { existsSync, readFileSync, writeFileSync, copyFileSync } from "node:fs";
import { join } from "node:path";

const DATA_DIR = join(process.cwd(), "data");
const DB = join(DATA_DIR, "db.json");

export function load() {
  if (!existsSync(DB)) copyFileSync(join(DATA_DIR, "seed.json"), DB);
  return JSON.parse(readFileSync(DB, "utf8"));
}

export function save(db) {
  writeFileSync(DB, JSON.stringify(db, null, 2));
}

export function nextId(prefix, list) {
  const n = list.map((x) => parseInt(String(x.id).replace(/\D/g, ""), 10) || 0);
  return prefix + (Math.max(0, ...n) + 1);
}

export function orderTotal(db, order) {
  return order.items.reduce((sum, it) => {
    const p = db.products.find((x) => x.id === it.productId);
    return sum + (p ? p.price * it.quantity : 0);
  }, 0);
}

export function money(db, value) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: db.settings.currency }).format(value);
}
