import {
  FileText,
  PackageCheck,
  Receipt,
  Wallet,
  ArrowRight,
} from "lucide-react";
import { yen, dateText, statuses } from "./api";
import { projectAmounts } from "./project-dashboard-data";
import "./project-dashboard.css";

const orderStates: Record<string, string> = {
  received: "受注",
  completed: "納品済み",
  cancelled: "取消",
};
const invoiceStates: Record<string, string> = {
  draft: "下書き",
  issued: "未入金",
  paid: "入金済み",
  void: "無効",
};
const salesStates: Record<string, string> = {
  open: "未提出",
  sent: "回答待ち",
  won: "受注済み",
  lost: "失注",
};

export function ProjectDashboard({ data }: { data: any }) {
  const amounts = projectAmounts(data);
  const overdue = data.invoices.filter((i: any) => i.overdue);
  const cards = [
    {
      title: "見積額",
      amount: amounts.quoted,
      note: `${data.quotes.length}件・各見積の最新版（下書き含む）`,
      icon: FileText,
    },
    {
      title: "受注額",
      amount: amounts.ordered,
      note: `${data.orders.filter((o: any) => o.status !== "cancelled").length}件・取消を除く`,
      icon: PackageCheck,
    },
    {
      title: "請求済み",
      amount: amounts.invoiced,
      note: "発行済み＋入金済み",
      icon: Receipt,
    },
    {
      title: "未入金",
      amount: amounts.unpaid,
      note: `入金済み ${yen(amounts.paid)}`,
      icon: Wallet,
    },
  ];
  return (
    <div className="project-dashboard">
      <section className="project-client-info" aria-label="相手先の会社情報">
        <h3>相手先の会社情報</h3>
        <dl>
          <div>
            <dt>会社名・屋号</dt>
            <dd>{data.customer_name}</dd>
          </div>
          <div>
            <dt>担当者</dt>
            <dd>{data.customer_contact || "未登録"}</dd>
          </div>
          <div>
            <dt>法人番号</dt>
            <dd>{data.customer_corporate_number || "未登録"}</dd>
          </div>
        </dl>
        {data.editable && (
          <small>「案件を編集」から担当者・法人番号を登録できます。</small>
        )}
      </section>
      <div className="project-money-grid" aria-label="案件の金額サマリー">
        {cards.map((card) => (
          <article className="project-money-card" key={card.title}>
            <span>
              <card.icon size={19} />
              {card.title}
            </span>
            <strong>{yen(card.amount)}</strong>
            <small>{card.note}</small>
          </article>
        ))}
      </div>
      <p className="project-dashboard-note">
        金額はすべて税込。見積・受注・請求は同じ取引の各段階のため、合算しません。閲覧できる書類のみ表示しています。
      </p>
      {overdue.length > 0 && (
        <aside className="project-overdue" aria-label="支払期限を過ぎた請求">
          <strong>支払期限を過ぎた請求が {overdue.length} 件あります</strong>
          {overdue.map((i: any) => (
            <a key={i.id} href={`#/invoices/${i.id}`}>
              {i.number} · {yen(i.total)} · 支払期限 {dateText(i.due_on)}{" "}
              <ArrowRight size={14} />
            </a>
          ))}
        </aside>
      )}
      <div className="project-flow-heading">
        <h3>仕事とお金の流れ</h3>
        <span>見積から請求まで、ひと続きで確認</span>
      </div>
      {!data.quotes.length && (
        <div className="project-flow-empty">
          まだ見積はありません。「案件の見積を作成」から、この仕事の見積をはじめましょう。
        </div>
      )}
      {data.quotes.map((q: any) => {
        const orders = data.orders.filter((o: any) => o.quote_id === q.id);
        const invoices = data.invoices.filter((i: any) =>
          orders.some((o: any) => o.id === i.order_id),
        );
        return (
          <article
            className="project-flow"
            key={q.id}
            aria-label={`${q.title}の取引の流れ`}
          >
            <div className="project-flow-stage">
              <h4>
                <FileText size={16} />
                見積
              </h4>
              <a
                className="project-flow-document"
                href={`#/revisions/${q.revision_id}`}
              >
                <strong>{q.title}</strong>
                <small>
                  {q.number || "採番前"} · 第{q.version}版
                </small>
                <b>{yen(q.total)}</b>
                <span className="project-flow-status">
                  {statuses[q.status] || q.status} ·{" "}
                  {salesStates[q.sales_status] || q.sales_status}
                </span>
              </a>
            </div>
            <div className="project-flow-stage">
              <h4>
                <PackageCheck size={16} />
                受注
              </h4>
              {!orders.length && (
                <p className="project-flow-placeholder">受注はまだありません</p>
              )}
              {orders.map((o: any) => (
                <a
                  key={o.id}
                  className={`project-flow-document ${o.status === "cancelled" ? "is-inactive" : ""}`}
                  href={`#/orders/${o.id}`}
                >
                  <strong>{o.title}</strong>
                  <small>
                    受注元：第{o.version}版 · {dateText(o.ordered_on)}
                  </small>
                  <b>{yen(o.total)}</b>
                  <span className="project-flow-status">
                    {orderStates[o.status] || o.status}
                  </span>
                  {o.delivery_on && (
                    <small>納品予定 {dateText(o.delivery_on)}</small>
                  )}
                </a>
              ))}
            </div>
            <div className="project-flow-stage">
              <h4>
                <Receipt size={16} />
                請求・入金
              </h4>
              {!invoices.length && (
                <p className="project-flow-placeholder">
                  請求書はまだありません
                </p>
              )}
              {invoices.map((i: any) => (
                <a
                  key={i.id}
                  className={`project-flow-document ${i.overdue ? "is-overdue" : ""} ${i.status === "void" ? "is-inactive" : ""}`}
                  href={`#/invoices/${i.id}`}
                >
                  <strong>{i.number || "請求書の下書き"}</strong>
                  <b>{yen(i.total)}</b>
                  <span className="project-flow-status">
                    {invoiceStates[i.status] || i.status}
                    {i.overdue ? " · 期限超過" : ""}
                  </span>
                  <small>支払期限 {dateText(i.due_on)}</small>
                  {i.paid_on && <small>入金日 {dateText(i.paid_on)}</small>}
                </a>
              ))}
            </div>
          </article>
        );
      })}
    </div>
  );
}
