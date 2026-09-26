import { NextResponse } from "next/server";
import { checkLogin, SESSION_COOKIE } from "../../../lib/auth";
import { MESSAGES } from "../../../lib/validate";

export async function POST(req) {
  const { email, password } = await req.json();
  if (!checkLogin(email, password)) return NextResponse.json({ errors: { form: MESSAGES.loginFailed } }, { status: 400 });
  const res = NextResponse.json({ ok: true });
  res.cookies.set(SESSION_COOKIE, "demo", { httpOnly: true, sameSite: "lax", path: "/" });
  return res;
}
