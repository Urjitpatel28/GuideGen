// Demo-only auth: one fake account, a plain cookie. Credentials are documented in README.md.
export const SESSION_COOKIE = "shop_session";
export const DEMO_USER = { email: "demo@shop.test", password: "demo1234", name: "Dana Demo" };

export function checkLogin(email, password) {
  return email?.toLowerCase() === DEMO_USER.email && password === DEMO_USER.password;
}
