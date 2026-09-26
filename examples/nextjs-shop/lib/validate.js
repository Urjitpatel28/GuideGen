// User-facing validation messages (GuideGen collects these for the Troubleshooting chapter).
export const MESSAGES = {
  nameRequired: "Name is required",
  skuRequired: "SKU is required",
  priceInvalid: "Price must be greater than 0",
  stockNegative: "Stock cannot be negative",
  customerRequired: "Select a customer",
  productRequired: "Select a product",
  quantityInvalid: "Quantity must be greater than 0",
  notEnoughStock: "Not enough stock for this quantity",
  emailInvalid: "Email is not valid",
  thresholdInvalid: "Low-stock threshold must be between 0 and 1000",
  loginFailed: "Invalid email or password",
};

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateProduct(p) {
  const e = {};
  if (!p.name?.trim()) e.name = MESSAGES.nameRequired;
  if (!p.sku?.trim()) e.sku = MESSAGES.skuRequired;
  if (!(Number(p.price) > 0)) e.price = MESSAGES.priceInvalid;
  if (Number(p.stock) < 0 || p.stock === "" || isNaN(Number(p.stock))) e.stock = MESSAGES.stockNegative;
  return e;
}

export function validateOrder(o, product) {
  const e = {};
  if (!o.customerId) e.customerId = MESSAGES.customerRequired;
  if (!o.productId) e.productId = MESSAGES.productRequired;
  const q = Number(o.quantity);
  if (!(q > 0)) e.quantity = MESSAGES.quantityInvalid;
  else if (product && q > product.stock) e.quantity = MESSAGES.notEnoughStock;
  return e;
}

export function validateCustomer(c) {
  const e = {};
  if (!c.name?.trim()) e.name = MESSAGES.nameRequired;
  if (!EMAIL.test(c.email || "")) e.email = MESSAGES.emailInvalid;
  return e;
}

export function validateSettings(s) {
  const e = {};
  if (!s.storeName?.trim()) e.storeName = MESSAGES.nameRequired;
  const t = Number(s.lowStockThreshold);
  if (isNaN(t) || t < 0 || t > 1000) e.lowStockThreshold = MESSAGES.thresholdInvalid;
  return e;
}
