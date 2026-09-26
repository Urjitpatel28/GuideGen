"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

const LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/products", label: "Products" },
  { href: "/orders", label: "Orders" },
  { href: "/customers", label: "Customers" },
  { href: "/settings", label: "Settings" },
];

export default function Nav({ userEmail }) {
  const path = usePathname();
  const router = useRouter();
  if (path === "/login") return null;

  async function signOut() {
    await fetch("/api/logout", { method: "POST" });
    router.push("/login");
  }

  return (
    <aside className="nav">
      <div className="nav-brand">
        <img src="/logo.svg" alt="" width="32" height="32" />
        <span>Acme Shop</span>
      </div>
      <nav aria-label="Main">
        {LINKS.map((l) => {
          const active = l.href === "/" ? path === "/" : path.startsWith(l.href);
          return (
            <Link key={l.href} href={l.href} className={active ? "active" : ""} aria-current={active ? "page" : undefined} data-testid={`nav-${l.label.toLowerCase()}`}>
              {l.label}
            </Link>
          );
        })}
      </nav>
      <div className="nav-user">
        <span className="user-email">{userEmail}</span>
        <button type="button" className="btn link" onClick={signOut} data-testid="sign-out">Sign out</button>
      </div>
    </aside>
  );
}
