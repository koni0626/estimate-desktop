import Decimal from "decimal.js";

export function calculate(
  items: { quantity: string; unit_price: string; tax_rate: number }[],
) {
  const bases: Record<string, Decimal> = {};
  const amounts = items.map((item) => {
    const amount = new Decimal(item.quantity || 0)
      .mul(item.unit_price || 0)
      .toDecimalPlaces(0, Decimal.ROUND_HALF_UP);
    bases[item.tax_rate] = (bases[item.tax_rate] || new Decimal(0)).plus(
      amount,
    );
    return amount.toFixed(0);
  });
  const subtotal = amounts.reduce((a, b) => a.plus(b), new Decimal(0));
  const tax = Object.entries(bases).reduce(
    (a, [rate, value]) => a.plus(value.mul(rate).div(100).floor()),
    new Decimal(0),
  );
  return {
    amounts,
    subtotal: subtotal.toFixed(0),
    tax: tax.toFixed(0),
    total: subtotal.plus(tax).toFixed(0),
  };
}

export const unitYen = (value: string | number) =>
  new Intl.NumberFormat("ja-JP", {
    style: "currency",
    currency: "JPY",
    maximumFractionDigits: 2,
  }).format(Number(value));

export async function api<T = any>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...init.headers },
  });
  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => ({ detail: "通信に失敗しました。" }));
    if (response.status === 401 && path != "/auth/login")
      window.dispatchEvent(new Event("session-expired"));
    const message = Array.isArray(body.detail)
      ? body.detail
          .map((e: any) => `${e.loc.slice(1).join(".")}: ${e.msg}`)
          .join(" / ")
      : body.detail;
    throw new Error(message || "処理に失敗しました。");
  }
  return response.json();
}
export const post = (path: string, data: any) =>
  api(path, { method: "POST", body: JSON.stringify(data) });
export const put = (path: string, data: any) =>
  api(path, { method: "PUT", body: JSON.stringify(data) });
export const yen = (value: string | number) =>
  new Intl.NumberFormat("ja-JP", {
    style: "currency",
    currency: "JPY",
    maximumFractionDigits: 0,
  }).format(Number(value));
export const dateText = (value: string) =>
  new Date(value).toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
export const statuses: Record<string, string> = {
  draft: "下書き",
  pending: "承認待ち",
  approved: "承認済み",
  issued: "発行済み",
  returned: "差戻し",
};
export const roles: Record<string, string> = {
  admin: "会社管理者",
  member: "一般担当者",
  section_manager: "課管理者",
  department_manager: "部管理者",
};
export function navigate(path: string) {
  window.location.hash = path;
}
export type QuoteSummary = {
  sales_status: string;
  id: number;
  revision_id: number;
  number: string | null;
  version: number;
  status: string;
  title: string;
  customer_name: string;
  total: string;
  valid_until: string;
  updated_at: string;
  owner_name: string;
  organization: string;
};
