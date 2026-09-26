// Resets data/db.json from data/seed.json (fake data only).
import { copyFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
copyFileSync(join(root, "data", "seed.json"), join(root, "data", "db.json"));
console.log("Seeded data/db.json");
