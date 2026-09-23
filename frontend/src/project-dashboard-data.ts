import Decimal from "decimal.js";

export type DocumentAmount = { total: string; status: string };
export function projectAmounts(data: {
  quotes: DocumentAmount[];
  orders: DocumentAmount[];
  invoices: DocumentAmount[];
}) {
  const sum = (rows: DocumentAmount[]) =>
    rows.reduce((n, r) => n.plus(r.total), new Decimal(0)).toFixed(0);
  return {
    quoted: sum(data.quotes),
    ordered: sum(data.orders.filter((r) => r.status !== "cancelled")),
    invoiced: sum(
      data.invoices.filter((r) => ["issued", "paid"].includes(r.status)),
    ),
    unpaid: sum(data.invoices.filter((r) => r.status === "issued")),
    paid: sum(data.invoices.filter((r) => r.status === "paid")),
  };
}
