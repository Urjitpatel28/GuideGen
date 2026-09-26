import "./globals.css";
import { cookies } from "next/headers";
import Nav from "../components/Nav";
import { DEMO_USER, SESSION_COOKIE } from "../lib/auth";

export const metadata = { title: "Acme Shop", icons: { icon: "/favicon.svg" } };

export default async function RootLayout({ children }) {
  const signedIn = (await cookies()).get(SESSION_COOKIE);
  return (
    <html lang="en">
      <body>
        <div className="shell">
          {signedIn && <Nav userEmail={DEMO_USER.email} />}
          <main className="content">{children}</main>
        </div>
      </body>
    </html>
  );
}
