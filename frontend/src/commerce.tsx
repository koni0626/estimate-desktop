import {
  useEffect,
  useState,
  type FormEvent,
  type PropsWithChildren,
} from "react";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Download,
  FileText,
  Plus,
  Search,
} from "lucide-react";
import { api, post, put, yen, dateText, navigate } from "./api";

type Props = {
  boot: any;
  refresh: () => Promise<void>;
  notify: (text: string) => void;
};
const today = () => new Date().toLocaleDateString("sv-SE");
const dueDate = () => {
  const d = new Date();
  d.setDate(d.getDate() + 30);
  return d.toLocaleDateString("sv-SE");
};
const labels: Record<string, string> = {
  open: "未提出",
  sent: "回答待ち",
  won: "受注",
  lost: "失注",
  received: "進行中",
  completed: "納品・完了",
  cancelled: "受注取消",
  draft: "下書き",
  issued: "未入金",
  paid: "入金済み",
  void: "取消済み",
};
export const SalesBadge = ({ status }: { status: string }) => (
  <span className={`badge ${status}`}>
    <i />
    {labels[status] || status}
  </span>
);
const Field = ({ label, children }: PropsWithChildren<{ label: string }>) => (
  <label className="field">
    <span>{label}</span>
    {children}
  </label>
);
const ErrorBox = ({ error }: { error: string }) =>
  error ? (
    <div className="error" role="alert">
      {error}
    </div>
  ) : null;
const Title = ({
  title,
  eyebrow,
  description,
  children,
}: PropsWithChildren<{
  title: string;
  eyebrow: string;
  description: string;
}>) => (
  <div className="page-title">
    <div>
      <div className="eyebrow">{eyebrow}</div>
      <h1>{title}</h1>
      <p>{description}</p>
    </div>
    <div className="page-actions">{children}</div>
  </div>
);
const Back = ({ to, children }: PropsWithChildren<{ to: string }>) => (
  <button className="back-link" onClick={() => navigate(to)}>
    <ArrowLeft size={16} />
    {children}
  </button>
);

export function QuoteSales({
  data,
  onChange,
  ...props
}: Props & { data: any; onChange: () => void }) {
  const [show, setShow] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [form, setForm] = useState({
    ordered_on: today(),
    delivery_on: "",
    note: "",
  });
  const [sentOn, setSentOn] = useState(data.sent_on || today());
  async function outcome(status: string) {
    setBusy(true);
    setError("");
    try {
      await put(`/quotes/${data.id}/sales`, {
        sales_status: status,
        sent_on: status === "sent" ? sentOn : data.sent_on,
        lock_version: data.sales_version,
      });
      await props.refresh();
      onChange();
      props.notify("営業状況を更新しました");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function order(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const o = await post("/orders", {
        ...form,
        delivery_on: form.delivery_on || null,
        revision_id: data.revision_id,
      });
      await props.refresh();
      props.notify("受注を登録しました");
      navigate(`/orders/${o.id}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (!data.business_editable) return null;
  return (
    <section className="panel commerce-strip">
      <div className="commerce-heading">
        <div>
          <div className="eyebrow">NEXT STEP</div>
          <h2>お客様との進み具合</h2>
          <p>社内承認とは別に、提出後の結果を記録します。</p>
        </div>
        <SalesBadge status={data.sales_status} />
      </div>
      <ErrorBox error={error} />
      {data.order_id ? (
        <button
          className="button primary"
          onClick={() => navigate(`/orders/${data.order_id}`)}
        >
          受注・請求を確認 <ArrowRight size={16} />
        </button>
      ) : (
        <>
          <div className="commerce-actions">
            <Field label="提出日">
              <input
                type="date"
                value={sentOn}
                max={today()}
                onInput={(e) => setSentOn(e.currentTarget.value)}
              />
            </Field>
            <button
              className="button secondary"
              disabled={busy || data.status !== "issued"}
              onClick={() => outcome("sent")}
            >
              提出済み・回答待ち
            </button>
            <button
              className="button subtle"
              disabled={busy || data.status !== "issued"}
              onClick={() => outcome("lost")}
            >
              失注を記録
            </button>
            {data.sales_status !== "open" && (
              <button
                className="button subtle"
                disabled={busy}
                onClick={() => outcome("open")}
              >
                未提出に戻す
              </button>
            )}
            <button
              className="button primary"
              disabled={busy || data.status !== "issued"}
              onClick={() => setShow(!show)}
            >
              <Check size={16} />
              この版で受注を登録
            </button>
          </div>
          {data.status !== "issued" && (
            <p className="muted">
              正式発行した見積の版から受注を登録できます。
            </p>
          )}
          {show && (
            <form onSubmit={order} className="commerce-inline">
              <p>
                {data.number} 第{data.version}版・{yen(data.total)}
                で受注します。
              </p>
              <div className="form-grid">
                <Field label="受注日 *">
                  <input
                    type="date"
                    required
                    max={today()}
                    value={form.ordered_on}
                    onInput={(e) =>
                      setForm({ ...form, ordered_on: e.currentTarget.value })
                    }
                  />
                </Field>
                <Field label="納期">
                  <input
                    type="date"
                    min={form.ordered_on}
                    value={form.delivery_on}
                    onInput={(e) =>
                      setForm({ ...form, delivery_on: e.currentTarget.value })
                    }
                  />
                </Field>
              </div>
              <Field label="社内メモ">
                <input
                  value={form.note}
                  maxLength={1000}
                  onChange={(e) => setForm({ ...form, note: e.target.value })}
                />
              </Field>
              <button className="button primary" disabled={busy}>
                受注を確定
              </button>
            </form>
          )}
        </>
      )}
    </section>
  );
}

export function Commerce({
  kind,
  id,
  ...props
}: Props & { kind: "orders" | "invoices"; id?: number }) {
  if (id)
    return kind === "orders" ? (
      <OrderDetail key={id} id={id} {...props} />
    ) : (
      <InvoiceDetail key={id} id={id} {...props} />
    );
  return <CommerceList key={kind} kind={kind} {...props} />;
}

function CommerceList({ kind, boot }: Props & { kind: "orders" | "invoices" }) {
  const [rows, setRows] = useState<any[]>([]),
    [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  const [search, setSearch] = useState(""),
    [filter, setFilter] = useState("all");
  const invoice = kind === "invoices";
  useEffect(() => {
    api(`/${kind}`)
      .then(setRows)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [kind, boot]);
  const filtered = rows.filter(
    (r) =>
      (filter === "all" ||
        (filter === "overdue"
          ? r.overdue
          : filter === "unbilled"
            ? r.status !== "cancelled" &&
              !r.invoices.some((i: any) =>
                ["issued", "paid"].includes(i.status),
              )
            : r.status === filter)) &&
      `${r.number || r.quote_number || ""} ${r.title || r.payload?.title} ${r.customer_name || r.payload?.customer.name}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  const unpaid = rows.filter((r) => r.status === "issued"),
    overdue = rows.filter((r) => r.overdue);
  const unbilled = rows.filter(
    (r) =>
      r.status !== "cancelled" &&
      !r.invoices?.some((i: any) => ["issued", "paid"].includes(i.status)),
  );
  return (
    <>
      <Title
        title={invoice ? "請求・入金" : "受注管理"}
        eyebrow={invoice ? "INVOICES & PAYMENTS" : "ORDERS"}
        description={
          invoice
            ? "請求から入金まで、ひと目で確認。"
            : "決まった仕事を、納品と請求につなげましょう。"
        }
      >
        <button
          className="button secondary"
          onClick={() => navigate(invoice ? "/orders" : "/quotes")}
        >
          {invoice ? "受注から請求書を作成" : "見積から受注を登録"}
          <ArrowRight size={16} />
        </button>
      </Title>
      <ErrorBox error={error} />
      <div className="commerce-stats">
        {(invoice
          ? [
              [
                "未入金",
                unpaid.length,
                yen(unpaid.reduce((n, r) => n + Number(r.total), 0)),
              ],
              [
                "支払期限超過",
                overdue.length,
                yen(overdue.reduce((n, r) => n + Number(r.total), 0)),
              ],
              [
                "入金済み",
                rows.filter((r) => r.status === "paid").length,
                "全額入金を確認済み",
              ],
            ]
          : [
              [
                "進行中",
                rows.filter((r) => r.status === "received").length,
                "納品・完了までの仕事",
              ],
              ["未請求", unbilled.length, "下書きのみの請求も含みます"],
              [
                "納品・完了",
                rows.filter((r) => r.status === "completed").length,
                "完了した仕事",
              ],
            ]
        ).map(([label, count, sub]) => (
          <div className="panel commerce-stat" key={label}>
            <span>{label}</span>
            <strong>
              {count}
              <small>件</small>
            </strong>
            <p>{sub}</p>
          </div>
        ))}
      </div>
      <section className="panel">
        <div className="commerce-list-tools">
          <div className="search-box">
            <Search size={17} />
            <input
              aria-label="案件・取引先を検索"
              placeholder="案件名・取引先・番号で検索"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select
            aria-label="状態で絞り込み"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="all">すべての状態</option>
            {(invoice
              ? ["draft", "issued", "overdue", "paid", "void"]
              : ["received", "unbilled", "completed", "cancelled"]
            ).map((s) => (
              <option key={s} value={s}>
                {s === "overdue"
                  ? "支払期限超過"
                  : s === "unbilled"
                    ? "未請求"
                    : labels[s]}
              </option>
            ))}
          </select>
        </div>
        {loading ? (
          <div className="loading">読み込んでいます…</div>
        ) : filtered.length ? (
          <div className="table-scroll">
            <table className="quote-table">
              <thead>
                <tr>
                  <th>案件・書類</th>
                  <th>取引先</th>
                  <th>状態</th>
                  <th>{invoice ? "支払期限" : "納期"}</th>
                  <th className="right">税込金額</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <button
                        className="commerce-link"
                        onClick={() => navigate(`/${kind}/${r.id}`)}
                      >
                        {r.title || r.payload.title}
                      </button>
                      <small className="commerce-caption">
                        {r.number ||
                          (invoice
                            ? "請求書の下書き"
                            : `${r.quote_number} 第${r.version}版`)}
                      </small>
                    </td>
                    <td>{r.customer_name || r.payload.customer.name}</td>
                    <td>
                      <SalesBadge status={r.status} />
                      {r.overdue && (
                        <span className="overdue-note">期限超過</span>
                      )}
                      {!invoice &&
                        !r.invoices.some((i: any) => i.status !== "void") && (
                          <small className="commerce-caption">
                            請求書未作成
                          </small>
                        )}
                    </td>
                    <td>
                      {r.due_on || r.delivery_on
                        ? dateText(r.due_on || r.delivery_on)
                        : "未設定"}
                    </td>
                    <td className="money">{yen(r.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty">
            <FileText size={30} />
            <h3>
              {search || filter !== "all"
                ? "条件に合うデータがありません"
                : invoice
                  ? "請求書はまだありません"
                  : "受注はまだありません"}
            </h3>
            <p>
              {invoice
                ? "受注した案件から、見積の内容を引き継いで作成できます。"
                : "見積詳細の「この版で受注を登録」からはじめましょう。"}
            </p>
          </div>
        )}
        <div className="table-footer">{filtered.length}件を表示</div>
      </section>
    </>
  );
}

function OrderDetail({ id, boot, refresh, notify }: Props & { id: number }) {
  const [data, setData] = useState<any>(),
    [form, setForm] = useState<any>(),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  function apply(d: any) {
    setData(d);
    setForm({
      ordered_on: d.ordered_on,
      delivery_on: d.delivery_on || "",
      status: d.status,
      note: d.note,
    });
  }
  useEffect(() => {
    api(`/orders/${id}`)
      .then(apply)
      .catch((e) => setError(e.message));
  }, [id, boot]);
  async function save(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      apply(
        await put(`/orders/${id}`, {
          ...form,
          delivery_on: form.delivery_on || null,
          lock_version: data.lock_version,
        }),
      );
      await refresh();
      notify("受注を更新しました");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function invoice() {
    setBusy(true);
    setError("");
    try {
      const i = await post(`/orders/${id}/invoices`, {
        issue_on: today(),
        transaction_on: data.delivery_on || today(),
        due_on: dueDate(),
        bank_details: boot.company.bank_details,
        registration_number: boot.company.registration_number,
      });
      notify("請求書の下書きを作成しました");
      navigate(`/invoices/${i.id}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (!data)
    return (
      <>
        <ErrorBox error={error} />
        <Back to="/orders">受注一覧へ</Back>
        {!error && <div className="loading">読み込んでいます…</div>}
      </>
    );
  const active = data.invoices.find((i: any) => i.status !== "void");
  return (
    <>
      <Back to="/orders">受注一覧へ</Back>
      <Title
        eyebrow={`ORDER ${id}`}
        title={data.title}
        description={data.customer_name}
      >
        <SalesBadge status={data.status} />
      </Title>
      <ErrorBox error={error} />
      <div className="commerce-detail-grid">
        <form className="panel form-section" onSubmit={save}>
          <h2>受注内容</h2>
          <p className="muted">合意した見積の金額・明細を保持しています。</p>
          <div className="commerce-amount">
            {yen(data.total)}
            <small>税込受注金額</small>
          </div>
          <button
            type="button"
            className="commerce-link"
            onClick={() => navigate(`/revisions/${data.revision_id}`)}
          >
            {data.quote_number} 第{data.version}版を見る{" "}
            <ArrowRight size={14} />
          </button>
          <fieldset disabled={busy || !data.editable}>
            <div className="form-grid">
              <Field label="受注日 *">
                <input
                  type="date"
                  required
                  max={today()}
                  value={form.ordered_on}
                  onInput={(e) =>
                    setForm({ ...form, ordered_on: e.currentTarget.value })
                  }
                />
              </Field>
              <Field label="納期">
                <input
                  type="date"
                  min={form.ordered_on}
                  value={form.delivery_on}
                  onInput={(e) =>
                    setForm({ ...form, delivery_on: e.currentTarget.value })
                  }
                />
              </Field>
            </div>
            <Field label="進行状況">
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
              >
                {["received", "completed", "cancelled"].map((s) => (
                  <option key={s} value={s}>
                    {labels[s]}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="社内メモ・取消理由">
              <textarea
                rows={3}
                maxLength={1000}
                value={form.note}
                onChange={(e) => setForm({ ...form, note: e.target.value })}
              />
            </Field>
            {data.editable && (
              <button className="button primary" disabled={busy}>
                受注内容を保存
              </button>
            )}
          </fieldset>
        </form>
        <section className="panel form-section">
          <div className="eyebrow">BILLING</div>
          <h2>この受注の請求書</h2>
          <p className="muted">
            受注額を一括で請求します。発行後に入金を記録できます。
          </p>
          {data.invoices.map((i: any) => (
            <button
              className="invoice-card"
              key={i.id}
              onClick={() => navigate(`/invoices/${i.id}`)}
            >
              <span>
                <strong>{i.number || "請求書の下書き"}</strong>
                <small>支払期限：{dateText(i.due_on)}</small>
              </span>
              <SalesBadge status={i.status} />
              <ArrowRight size={17} />
            </button>
          ))}
          {!active && data.editable && data.status !== "cancelled" && (
            <button
              className="button primary"
              disabled={busy}
              onClick={invoice}
            >
              <Plus size={16} />
              請求書を作成
            </button>
          )}
          {!data.invoices.length && (
            <p className="muted">まだ請求書は作成されていません。</p>
          )}
        </section>
      </div>
    </>
  );
}

function InvoiceDetail({ id, boot, notify }: Props & { id: number }) {
  const [data, setData] = useState<any>(),
    [form, setForm] = useState<any>(),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [paidOn, setPaidOn] = useState(today()),
    [note, setNote] = useState(""),
    [reason, setReason] = useState(""),
    [correction, setCorrection] = useState("");
  function apply(d: any) {
    setData(d);
    setForm({
      issue_on: d.issue_on,
      transaction_on: d.transaction_on,
      due_on: d.due_on,
      bank_details: d.payload.bank_details || "",
      registration_number: d.payload.registration_number || "",
      notes: d.payload.notes || "",
    });
  }
  useEffect(() => {
    api(`/invoices/${id}`)
      .then(apply)
      .catch((e) => setError(e.message));
  }, [id, boot]);
  async function run(action: string) {
    setBusy(true);
    setError("");
    try {
      let d = data;
      if (["save", "issue"].includes(action) && data.status === "draft")
        d = await put(`/invoices/${id}`, {
          ...form,
          lock_version: data.lock_version,
        });
      apply(d);
      if (action === "payment")
        d = await post(`/invoices/${id}/payment`, {
          lock_version: d.lock_version,
          paid_on: paidOn,
          note,
        });
      else if (action !== "save")
        d = await post(`/invoices/${id}/${action}`, {
          lock_version: d.lock_version,
          comment: reason,
        });
      apply(d);
      setCorrection("");
      setReason("");
      notify(
        (
          {
            save: "下書きを保存しました",
            issue: "請求書を発行しました",
            payment: "全額入金を記録しました",
            unpay: "入金記録を訂正しました",
            void: "請求書を取り消しました",
          } as any
        )[action],
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (!data)
    return (
      <>
        <ErrorBox error={error} />
        <Back to="/invoices">請求一覧へ</Back>
        {!error && <div className="loading">読み込んでいます…</div>}
      </>
    );
  const draft = data.status === "draft",
    edit = data.editable;
  return (
    <>
      <Back to="/invoices">請求・入金一覧へ</Back>
      <Title
        eyebrow={data.number || "DRAFT INVOICE"}
        title={data.payload.title}
        description={data.payload.customer.name}
      >
        <SalesBadge status={data.status} />
        {data.overdue && (
          <span className="overdue-note">支払期限を過ぎています</span>
        )}
      </Title>
      <ErrorBox error={error} />
      <div className="detail-toolbar">
        <a
          className="button secondary"
          href={`/api/invoices/${id}/pdf${draft ? "" : "?download=true"}`}
          target="_blank"
          rel="noreferrer"
        >
          <Download size={16} />
          {draft ? "保存済みPDFプレビュー" : "PDFをダウンロード"}
        </a>
        <button
          className="button subtle"
          onClick={() => navigate(`/orders/${data.order_id}`)}
        >
          元の受注を確認 <ArrowRight size={16} />
        </button>
      </div>
      {data.status === "void" && (
        <div className="error">
          この請求書は取消済みです。保存済みPDFは当時の内容を保持しています。
        </div>
      )}
      <div className="commerce-detail-grid">
        <form
          className="panel form-section"
          onSubmit={(e) => {
            e.preventDefault();
            run("save");
          }}
        >
          <h2>請求内容</h2>
          <div className="commerce-amount">
            {yen(data.total)}
            <small>税込請求金額</small>
          </div>
          <p className="muted">
            {data.payload.source_quote}から引き継いだ金額です。
          </p>
          <fieldset disabled={busy || !draft || !edit}>
            <div className="form-grid">
              <Field label="請求日 *">
                <input
                  type="date"
                  required
                  value={form.issue_on}
                  onInput={(e) =>
                    setForm({ ...form, issue_on: e.currentTarget.value })
                  }
                />
              </Field>
              <Field label="取引年月日 *">
                <input
                  type="date"
                  required
                  value={form.transaction_on}
                  onInput={(e) =>
                    setForm({ ...form, transaction_on: e.currentTarget.value })
                  }
                />
              </Field>
              <Field label="支払期限 *">
                <input
                  type="date"
                  required
                  min={form.issue_on}
                  value={form.due_on}
                  onInput={(e) =>
                    setForm({ ...form, due_on: e.currentTarget.value })
                  }
                />
              </Field>
              <Field label="登録番号（登録済みの事業者のみ）">
                <input
                  pattern="T[0-9]{13}"
                  maxLength={14}
                  placeholder="T＋13桁の数字（任意）"
                  value={form.registration_number}
                  onChange={(e) =>
                    setForm({ ...form, registration_number: e.target.value })
                  }
                />
              </Field>
            </div>
            <Field label="お振込先">
              <textarea
                rows={3}
                maxLength={500}
                value={form.bank_details}
                onChange={(e) =>
                  setForm({ ...form, bank_details: e.target.value })
                }
              />
            </Field>
            <Field label="備考（PDFに表示）">
              <textarea
                rows={3}
                maxLength={3000}
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
              />
            </Field>
            {draft && edit && (
              <div className="commerce-actions">
                <button className="button secondary" disabled={busy}>
                  下書きを保存
                </button>
                <button
                  className="button primary"
                  type="button"
                  disabled={busy}
                  onClick={(e) => {
                    if (e.currentTarget.form?.reportValidity()) run("issue");
                  }}
                >
                  保存して請求書を発行
                </button>
              </div>
            )}
          </fieldset>
          <div className="table-scroll">
            <table className="quote-table">
              <thead>
                <tr>
                  <th>明細</th>
                  <th>税率</th>
                  <th className="right">金額</th>
                </tr>
              </thead>
              <tbody>
                {data.payload.items.map((it: any, n: number) => (
                  <tr key={n}>
                    <td>{it.name}</td>
                    <td>{it.tax_rate}%</td>
                    <td className="money">{yen(it.amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </form>
        <section className="panel form-section">
          <div className="eyebrow">PAYMENT</div>
          <h2>入金確認</h2>
          {data.status === "issued" ? (
            <>
              <p className="muted">
                銀行などで全額の入金を確認したら記録します。
              </p>
              <p>
                確認する金額：<strong>{yen(data.total)}</strong>
              </p>
              {edit && (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    run("payment");
                  }}
                >
                  <Field label="入金日 *">
                    <input
                      required
                      type="date"
                      max={today()}
                      value={paidOn}
                      onInput={(e) => setPaidOn(e.currentTarget.value)}
                    />
                  </Field>
                  <Field label="入金メモ">
                    <input
                      maxLength={1000}
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                      placeholder="例：振込人名・照合内容"
                    />
                  </Field>
                  <button className="button primary" disabled={busy}>
                    <Check size={16} />
                    全額入金を記録
                  </button>
                </form>
              )}
            </>
          ) : data.status === "paid" ? (
            <div className="payment-done">
              <Check size={27} />
              <h3>全額入金を確認済み</h3>
              <p>
                {dateText(data.paid_on)} / {yen(data.total)}
              </p>
              <p>{data.payment_note}</p>
            </div>
          ) : (
            <p className="muted">
              発行済みの請求書に対して入金を記録できます。
            </p>
          )}
          {edit && data.status !== "void" && (
            <div className="commerce-correction">
              <button
                className="button subtle"
                disabled={busy}
                onClick={() =>
                  setCorrection(data.status === "paid" ? "unpay" : "void")
                }
              >
                {data.status === "paid"
                  ? "入金記録を訂正する"
                  : "この請求書を取り消す"}
              </button>
              {correction && (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    run(correction);
                  }}
                >
                  <Field label="理由 *">
                    <textarea
                      required
                      maxLength={1000}
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                    />
                  </Field>
                  <p className="muted">
                    {correction === "unpay"
                      ? "未入金に戻し、訂正理由を履歴に残します。返金処理ではありません。"
                      : "取消履歴を残します。必要な場合は受注から請求書を作り直せます。"}
                  </p>
                  <button className="button secondary" disabled={busy}>
                    理由を記録して{correction === "unpay" ? "訂正" : "取消"}
                  </button>
                </form>
              )}
            </div>
          )}
        </section>
      </div>
    </>
  );
}

export function SealSettings({ boot, refresh, notify }: Props) {
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function upload(file?: File) {
    if (!file) return;
    setError("");
    if (file.size > 2 * 1024 * 1024) {
      setError("2MB以下の画像を選択してください。");
      return;
    }
    setBusy(true);
    try {
      const bytes = new Uint8Array(await file.arrayBuffer());
      let binary = "";
      for (const b of bytes) binary += String.fromCharCode(b);
      await post("/seals", { image_base64: btoa(binary) });
      await refresh();
      notify("印鑑画像を登録しました");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function disable() {
    setBusy(true);
    setError("");
    try {
      await api("/seals/current", { method: "DELETE" });
      await refresh();
      notify("新しい見積での印鑑利用を停止しました");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel form-section">
      <h2>会社印・屋号印</h2>
      <p className="muted">
        登録は任意です。画像を選ぶとすぐに保存されます。過去の帳票は変わりません。
      </p>
      <ErrorBox error={error} />
      {boot.seal_id && (
        <img
          className="seal-preview"
          src={`/api/seals/${boot.seal_id}`}
          alt="登録中の印鑑"
        />
      )}
      <Field label="印鑑画像を登録・差替え">
        <input
          disabled={busy}
          type="file"
          accept="image/png,image/jpeg"
          onChange={(e) => {
            upload(e.target.files?.[0]);
            e.target.value = "";
          }}
        />
      </Field>
      <p className="muted">
        PNG・JPEG / 2MB以下 / 各辺10〜2000px。透過PNGがおすすめです。
      </p>
      {boot.seal_id && (
        <button
          type="button"
          className="button subtle"
          disabled={busy}
          onClick={disable}
        >
          今後の利用を停止
        </button>
      )}
    </section>
  );
}
