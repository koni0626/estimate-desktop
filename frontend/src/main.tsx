import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useRef,
  lazy,
  Suspense,
  type FormEvent,
  type PropsWithChildren,
} from "react";
import { createRoot } from "react-dom/client";
import {
  FileText,
  Plus,
  Search,
  ChevronRight,
  ChevronLeft,
  ArrowUpRight,
  ArrowLeft,
  ArrowUp,
  ArrowDown,
  Check,
  X,
  LogOut,
  Building2,
  Users,
  Settings,
  History,
  CheckCheck,
  Clock3,
  CircleHelp,
  Download,
  Copy,
  Pencil,
  Trash2,
  Send,
  ShieldCheck,
  Sparkles,
  LayoutGrid,
  CircleCheck,
  BriefcaseBusiness,
  RefreshCw,
  House,
  Leaf,
} from "lucide-react";
import {
  api,
  post,
  put,
  yen,
  unitYen,
  calculate,
  dateText,
  statuses,
  roles,
  navigate,
  type QuoteSummary,
} from "./api";
import { Commerce, QuoteSales, SalesBadge, SealSettings } from "./commerce";
import { Projects, QuoteScopeEditor, QuoteScope } from "./projects";
import { StudioHome, StudioPanel } from "./studio";
const Manual = lazy(() =>
  import("./manual").then((module) => ({ default: module.Manual })),
);
import "./styles.css";
import "./studio.css";

type Context = {
  boot: any;
  quotes: QuoteSummary[];
  customers: any[];
  approvals: any[];
  refresh: () => Promise<void>;
  notify: (s: string) => void;
};
const AppContext = createContext<Context>(null!);
const useApp = () => useContext(AppContext);
const Badge = ({ status }: { status: string }) => (
  <span className={`badge ${status}`}>
    <i />
    {statuses[status] || status}
  </span>
);
const Logo = () => (
  <div className="logo">
    <span className="logo-icon">
      <Leaf size={24} />
    </span>
    <span>
      見積管理 <small>demo</small>
    </span>
  </div>
);
const Empty = ({
  title,
  description,
  children,
}: PropsWithChildren<{ title: string; description: string }>) => (
  <div className="empty">
    <div className="empty-icon">
      <FileText size={26} />
    </div>
    <h3>{title}</h3>
    <p>{description}</p>
    {children}
  </div>
);
const ErrorBox = ({ error }: { error: string }) =>
  error ? (
    <div className="error" role="alert">
      {error}
    </div>
  ) : null;
const PageTitle = ({
  eyebrow,
  title,
  description,
  children,
}: PropsWithChildren<{
  eyebrow: string;
  title: string;
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
const Field = ({ label, children }: PropsWithChildren<{ label: string }>) => (
  <label className="field">
    <span>{label}</span>
    {children}
  </label>
);
const Modal = ({
  title,
  onClose,
  children,
}: PropsWithChildren<{ title: string; onClose: () => void }>) => (
  <div
    className="modal-backdrop"
    onMouseDown={(e) => {
      if (e.target === e.currentTarget) onClose();
    }}
  >
    <section
      className="modal"
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div className="modal-title">
        <h2>{title}</h2>
        <button className="icon-button" aria-label="閉じる" onClick={onClose}>
          <X size={20} />
        </button>
      </div>
      {children}
    </section>
  </div>
);

function Login({
  onLogin,
  setupRequired,
  demoAvailable,
  desktopMode,
}: {
  onLogin: () => Promise<void>;
  setupRequired: boolean;
  demoAvailable: boolean;
  desktopMode: boolean;
}) {
  const [companyName, setCompanyName] = useState(""),
    [displayName, setDisplayName] = useState(""),
    [username, setUsername] = useState(""),
    [password, setPassword] = useState(""),
    [passwordConfirm, setPasswordConfirm] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const accounts = [
    ["solo", "個人事業主", "ひだまりデザイン事務所"],
    ["staff", "担当者", "ノースワークス"],
    ["manager", "課長", "ノースワークス"],
    ["director", "部長", "ノースワークス"],
    ["admin", "会社管理者", "ノースワークス"],
  ];
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (setupRequired && desktopMode) {
        await post("/desktop/setup", {
          company_name: companyName,
          display_name: displayName,
        });
      } else if (setupRequired) {
        if (password !== passwordConfirm)
          throw new Error("確認用パスワードが一致しません。");
        await post("/setup", {
          company_name: companyName,
          display_name: displayName,
          username,
          password,
        });
      } else {
        await post("/auth/login", { username, password });
      }
      navigate("/quotes");
      await onLogin();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="login">
      <section className="login-story">
        <Logo />
        <div className="login-copy">
          <div className="eyebrow">FOR YOUR NEXT GOOD WORK</div>
          <h1>
            いい仕事のはじまりを、
            <br />
            一枚の見積から。
          </h1>
          <p>
            つくる、確認する、届ける。
            <br />
            見積から受注・請求・入金まで、ひとつに。
          </p>
          <div className="paper-art">
            <div className="paper-back" />
            <div className="paper-front">
              <div className="art-header">
                <span className="art-logo">m.</span>
                <span>ESTIMATE</span>
              </div>
              <h3>御見積書</h3>
              <div className="art-line w60" />
              <div className="art-line w40" />
              <div className="art-amount">
                ¥ 352,000<span>税込お見積金額</span>
              </div>
              <div className="art-row" />
              <div className="art-row" />
              <div className="art-row" />
              <div className="art-stamp">
                <Check size={22} />
              </div>
            </div>
            <div className="art-label">
              <CircleCheck size={18} /> 次の仕事へ、準備完了。
            </div>
          </div>
        </div>
        <div className="login-foot">小さな商いにも、チームの仕事にも。</div>
      </section>
      <section className="login-panel">
        <div className="login-form">
          <span className="version-tag">
            {setupRequired ? "INITIAL SETUP" : "WORKING PROTOTYPE"}
          </span>
          <h2>{setupRequired ? (desktopMode ? "仕事場を設定" : "最初の管理者を登録") : "おかえりなさい"}</h2>
          <p>
            {setupRequired
              ? desktopMode
                ? "事業者名とお名前を入力してください。次回からはこのアプリを開くだけで使えます。"
                : "事業者と管理者の情報を入力して、仕事場を開きましょう。この画面は初回のみ表示されます。"
              : "アカウントにログインして、仕事をはじめましょう。"}
          </p>
          <form onSubmit={submit}>
            {setupRequired && (
              <>
                <Field label="事業者名・屋号">
                  <input
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    maxLength={120}
                    required
                  />
                </Field>
                <Field label="あなたの名前">
                  <input
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    maxLength={100}
                    required
                  />
                </Field>
              </>
            )}
            {(!setupRequired || !desktopMode) && <Field label="ユーザー名">
              <input
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                minLength={setupRequired ? 3 : undefined}
                maxLength={80}
                pattern={setupRequired ? "[a-zA-Z0-9_.-]+" : undefined}
                title={setupRequired ? "半角英数字と _ . - を使用できます" : undefined}
                required
              />
            </Field>}
            {(!setupRequired || !desktopMode) && <Field label="パスワード">
              <input
                type="password"
                autoComplete={setupRequired ? "new-password" : "current-password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={setupRequired ? 12 : undefined}
                maxLength={200}
                required
              />
            </Field>}
            {setupRequired && !desktopMode && (
              <Field label="パスワード（確認）">
                <input
                  type="password"
                  autoComplete="new-password"
                  value={passwordConfirm}
                  onChange={(e) => setPasswordConfirm(e.target.value)}
                  minLength={12}
                  maxLength={200}
                  required
                />
              </Field>
            )}
            {setupRequired && !desktopMode && (
              <p className="login-note">パスワードは12文字以上で設定してください。</p>
            )}
            <ErrorBox error={error} />
            <button className="button primary full" disabled={busy}>
              {busy
                ? setupRequired
                  ? "設定中…"
                  : "ログイン中…"
                : setupRequired
                  ? desktopMode ? "仕事場を開く" : "登録してはじめる"
                  : "ログイン"}
              <ArrowUpRight size={18} />
            </button>
          </form>
          {!setupRequired && demoAvailable && (
            <>
              <div className="demo-heading">
                <span>デモアカウントを選ぶ</span>
                <small>共通パスワード：demo1234</small>
              </div>
              <div className="demo-accounts">
                {accounts.map(([id, label, company]) => (
                  <button
                    key={id}
                    className={username === id ? "selected" : ""}
                    onClick={() => {
                      setUsername(id);
                      setPassword("demo1234");
                    }}
                  >
                    <span>{label}</span>
                    <small>{company}</small>
                    {username === id && <Check size={15} />}
                  </button>
                ))}
              </div>
            </>
          )}
          <p className="login-note">
            <ShieldCheck size={15} /> 事業者ごとにデータを分けて管理します。
          </p>
        </div>
      </section>
    </main>
  );
}

function Quotes() {
  const { quotes, boot } = useApp();
  const [search, setSearch] = useState(""),
    [status, setStatus] = useState("all"),
    [sales, setSales] = useState("all"),
    [sort, setSort] = useState("recent"),
    [page, setPage] = useState(1);
  useEffect(() => setPage(1), [search, status, sort, sales]);
  const filtered = quotes
    .filter(
      (q) =>
        (status === "all" || q.status === status) &&
        (sales === "all" || q.sales_status === sales) &&
        `${q.title} ${q.customer_name} ${q.number || ""} ${q.owner_name}`
          .toLowerCase()
          .includes(search.toLowerCase()),
    )
    .sort((a, b) =>
      sort === "amount"
        ? Number(b.total) - Number(a.total)
        : b.updated_at.localeCompare(a.updated_at),
    );
  const issued = quotes.filter((q) => q.status === "issued"),
    draft = quotes.filter(
      (q) => q.status === "draft" || q.status === "returned",
    );
  const tabs = ["all", "draft", "pending", "approved", "issued", "returned"];
  const total = quotes.reduce((n, q) => n + Number(q.total), 0);
  return (
    <>
      <PageTitle
        eyebrow="ESTIMATES"
        title="見積書"
        description="ひとつひとつの見積を、次の仕事につなげましょう。"
      >
        <button
          className="button primary"
          onClick={() => navigate("/quotes/new")}
        >
          <Plus size={18} />
          見積書を作成
        </button>
      </PageTitle>
      <div className="stats-grid">
        <div className="stat-card main-stat">
          <div className="stat-label">
            見積総額 <span>税込</span>
            <span className="stat-symbol">
              <ArrowUpRight size={20} />
            </span>
          </div>
          <div className="stat-value">{yen(total)}</div>
          <div className="stat-foot">
            閲覧できる見積の最新版を集計 <span>{quotes.length}件</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">
            <FileText size={17} />
            発行済み
          </div>
          <div className="stat-value">
            {issued.length}
            <small>件</small>
          </div>
          <div className="stat-foot">
            {yen(issued.reduce((n, q) => n + Number(q.total), 0))}
            <span className="tiny-badge">発行完了</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">
            <Pencil size={17} />
            作成中の見積
          </div>
          <div className="stat-value">
            {draft.length}
            <small>件</small>
          </div>
          <div className="stat-foot">
            下書き・差戻しの見積<span className="stat-dots">•••</span>
          </div>
        </div>
      </div>
      <section className="table-panel">
        <div className="table-tabs">
          {tabs.map((tab) => (
            <button
              key={tab}
              className={status === tab ? "active" : ""}
              onClick={() => setStatus(tab)}
            >
              {tab === "all" ? "すべて" : statuses[tab]}
              <span>
                {tab === "all"
                  ? quotes.length
                  : quotes.filter((q) => q.status === tab).length}
              </span>
            </button>
          ))}
        </div>
        <div className="table-tools">
          <div className="search">
            <Search size={18} />
            <input
              aria-label="見積を検索"
              placeholder="件名、取引先、見積番号で検索"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            {search && (
              <button
                className="icon-button"
                aria-label="検索をクリア"
                onClick={() => setSearch("")}
              >
                <X size={14} />
              </button>
            )}
          </div>
          <select
            aria-label="営業状況で絞り込み"
            value={sales}
            onChange={(e) => setSales(e.target.value)}
          >
            <option value="all">すべての営業状況</option>
            <option value="open">未提出</option>
            <option value="sent">回答待ち</option>
            <option value="won">受注</option>
            <option value="lost">失注</option>
          </select>
          <select
            aria-label="並べ替え"
            value={sort}
            onChange={(e) => setSort(e.target.value)}
          >
            <option value="recent">更新日が新しい順</option>
            <option value="amount">金額が大きい順</option>
          </select>
        </div>
        <div className="table-scroll">
          <table className="quote-table">
            <thead>
              <tr>
                <th>見積書 / 件名</th>
                <th>取引先</th>
                <th className="right">見積金額（税込）</th>
                <th>ステータス</th>
                <th>更新日</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filtered.slice((page - 1) * 10, page * 10).map((q) => (
                <tr
                  key={q.id}
                  onClick={() => navigate(`/revisions/${q.revision_id}`)}
                >
                  <td>
                    <div className="document-cell">
                      <span
                        className={`document-icon ${q.status === "issued" ? "done" : ""}`}
                      >
                        <FileText size={20} />
                      </span>
                      <div>
                        <button
                          className="text-link"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/revisions/${q.revision_id}`);
                          }}
                        >
                          {q.title}
                        </button>
                        <small>
                          {q.number || "番号未発行"}
                          <span> · 第{q.version}版</span>
                        </small>
                      </div>
                    </div>
                  </td>
                  <td className="customer-cell">{q.customer_name}</td>
                  <td className="money">{yen(q.total)}</td>
                  <td>
                    <Badge status={q.status} />
                    <div className="commerce-caption">
                      <SalesBadge status={q.sales_status || "open"} />
                    </div>
                  </td>
                  <td className="muted date-cell">{dateText(q.updated_at)}</td>
                  <td>
                    <ChevronRight size={16} className="muted" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!filtered.length && (
          <Empty
            title={
              search || status !== "all"
                ? "条件に合う見積書がありません"
                : "最初の見積書をつくりましょう"
            }
            description="新しい見積を作成すると、ここに一覧で表示されます。"
          >
            <button
              className="button secondary"
              onClick={() => {
                setSearch("");
                setStatus("all");
              }}
            >
              条件をリセット
            </button>
          </Empty>
        )}
        <div className="table-footer">
          <span>
            {filtered.length}件中 {filtered.length ? (page - 1) * 10 + 1 : 0}–
            {Math.min(page * 10, filtered.length)}件を表示
          </span>
          <div>
            <button
              className="icon-button"
              disabled={page === 1}
              aria-label="前のページ"
              onClick={() => setPage(page - 1)}
            >
              <ChevronLeft size={16} />
            </button>
            <span className="page-number">{page}</span>
            <button
              className="icon-button"
              disabled={page * 10 >= filtered.length}
              aria-label="次のページ"
              onClick={() => setPage(page + 1)}
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </section>
      <div className="workspace-note">
        <ShieldCheck size={16} />
        <span>
          {boot.company.name} の
          {boot.me.role === "admin"
            ? "すべての"
            : boot.me.role === "department_manager"
              ? "部内の"
              : boot.me.section_id
                ? "課内の"
                : "担当する"}
          見積書を表示しています。
        </span>
        <span className="saving-dot" />
        データ保存済み
      </div>
    </>
  );
}

function QuoteEditor({ rid, projectId }: { rid?: number; projectId?: number }) {
  const { customers, refresh, notify, boot } = useApp();
  const blank = () => ({
    project_id: projectId || null,
    request_refs: [] as { request_id: number; version: number }[],
    seal_id: boot.company.seal_default ? boot.seal_id : null,
    title: "",
    customer_id: customers[0]?.id || "",
    valid_until: new Date(Date.now() + 30 * 86400000)
      .toISOString()
      .slice(0, 10),
    delivery: "",
    payment: "納品月の翌月末払い",
    notes: "",
    internal_note: "",
    items: [
      { name: "", quantity: "1", unit: "式", unit_price: "0", tax_rate: 10 },
    ],
  });
  const [form, setForm] = useState<any>(blank),
    [lock, setLock] = useState<number>(),
    [loading, setLoading] = useState(!!rid),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    if (!rid && projectId) {
      setLoading(true);
      api(`/projects/${projectId}`)
        .then((p) =>
          setForm((f: any) => ({
            ...f,
            customer_id: p.customer_id,
            title: p.title,
          })),
        )
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }
    if (rid)
      api(`/revisions/${rid}`)
        .then((d) => {
          const p = d.payload;
          setForm(
            Object.fromEntries(
              Object.keys(blank()).map((key) => [
                key,
                p[key] ??
                  (key === "seal_id"
                    ? null
                    : blank()[key as keyof ReturnType<typeof blank>]),
              ]),
            ),
          );
          setLock(d.lock_version);
          if (!d.editable || !["draft", "returned"].includes(d.status))
            setError("この見積は編集できません。詳細画面に戻ってください。");
        })
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
  }, [rid, projectId]);
  const change = (key: string, value: any) =>
    setForm((f: any) => ({ ...f, [key]: value }));
  const item = (index: number, key: string, value: any) =>
    change(
      "items",
      form.items.map((it: any, i: number) =>
        i === index ? { ...it, [key]: value } : it,
      ),
    );
  const { amounts, subtotal, tax, total } = calculate(form.items);
  async function save(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const body = {
        ...form,
        customer_id: Number(form.customer_id),
        items: form.items.map(
          ({ name, quantity, unit, unit_price, tax_rate }: any) => ({
            name,
            quantity,
            unit,
            unit_price,
            tax_rate: Number(tax_rate),
          }),
        ),
        ...(rid ? { lock_version: lock } : {}),
      };
      const d = rid
        ? await put(`/revisions/${rid}`, body)
        : await post("/quotes", body);
      await refresh();
      notify("下書きを保存しました");
      navigate(`/revisions/${d.revision_id}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (loading) return <div className="loading">見積書を読み込んでいます…</div>;
  return (
    <form onSubmit={save}>
      <button
        type="button"
        className="back-link"
        onClick={() => navigate(rid ? `/revisions/${rid}` : "/quotes")}
      >
        <ArrowLeft size={16} /> {rid ? "見積の詳細へ" : "見積書一覧へ"}
      </button>
      <PageTitle
        eyebrow="CREATE ESTIMATE"
        title={rid ? "見積書を編集" : "新しい見積書"}
        description="必要な情報を入力して、見積書をつくりましょう。"
      >
        <button
          type="button"
          className="button secondary"
          onClick={() => navigate("/quotes")}
        >
          キャンセル
        </button>
        <button className="button primary" disabled={busy || !customers.length}>
          <Check size={17} />
          {busy ? "保存中…" : "下書きを保存"}
        </button>
      </PageTitle>
      <ErrorBox error={error} />
      {!customers.length && (
        <div className="notice">
          まず取引先を登録してください。
          <button
            type="button"
            className="text-link"
            onClick={() => navigate("/customers")}
          >
            取引先管理へ
          </button>
        </div>
      )}
      <div className="editor-layout">
        <div>
          <QuoteScopeEditor form={form} setForm={setForm} existing={!!rid} />
          <section className="panel form-section">
            <div className="section-heading">
              <span className="section-number">01</span>
              <div>
                <h2>基本情報</h2>
                <p>宛先と見積の内容を入力してください。</p>
              </div>
            </div>
            <Field label="件名 *">
              <input
                value={form.title}
                maxLength={150}
                placeholder="例：Webサイト リニューアル"
                required
                onChange={(e) => change("title", e.target.value)}
              />
            </Field>
            <div className="form-grid">
              <Field label="取引先 *">
                <select
                  value={form.customer_id}
                  required
                  onChange={(e) => change("customer_id", e.target.value)}
                >
                  <option value="" disabled>
                    取引先を選択
                  </option>
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="見積有効期限 *">
                <input
                  type="date"
                  required
                  value={form.valid_until}
                  onChange={(e) => change("valid_until", e.target.value)}
                />
              </Field>
            </div>
          </section>
          <section className="panel form-section">
            <div className="section-heading">
              <span className="section-number">02</span>
              <div>
                <h2>見積明細</h2>
                <p>品目ごとに数量と単価を入力してください。</p>
              </div>
            </div>
            <div className="table-scroll">
              <table className="line-editor">
                <thead>
                  <tr>
                    <th>品名・内容</th>
                    <th>数量</th>
                    <th>単位</th>
                    <th>単価（税抜）</th>
                    <th>税率</th>
                    <th className="right">金額</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {form.items.map((it: any, i: number) => (
                    <tr key={i}>
                      <td>
                        <textarea
                          aria-label={`品名 ${i + 1}`}
                          required
                          rows={2}
                          maxLength={400}
                          value={it.name}
                          placeholder="品名や作業内容"
                          onChange={(e) => item(i, "name", e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          aria-label={`数量 ${i + 1}`}
                          type="number"
                          min="0.001"
                          step="0.001"
                          max="1000000"
                          required
                          value={it.quantity}
                          onChange={(e) => item(i, "quantity", e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          aria-label={`単位 ${i + 1}`}
                          maxLength={15}
                          value={it.unit}
                          onChange={(e) => item(i, "unit", e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          aria-label={`単価 ${i + 1}`}
                          type="number"
                          min="0"
                          max="1000000000"
                          step="0.01"
                          required
                          value={it.unit_price}
                          onChange={(e) =>
                            item(i, "unit_price", e.target.value)
                          }
                        />
                      </td>
                      <td>
                        <select
                          aria-label={`税率 ${i + 1}`}
                          value={it.tax_rate}
                          onChange={(e) =>
                            item(i, "tax_rate", Number(e.target.value))
                          }
                        >
                          <option value={10}>10%</option>
                          <option value={8}>8%</option>
                          <option value={0}>0%</option>
                        </select>
                      </td>
                      <td className="money">{yen(amounts[i])}</td>
                      <td>
                        <button
                          type="button"
                          className="icon-button danger"
                          aria-label={`明細 ${i + 1} を削除`}
                          disabled={form.items.length === 1}
                          onClick={() =>
                            change(
                              "items",
                              form.items.filter((_: any, n: number) => n !== i),
                            )
                          }
                        >
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button
              type="button"
              className="button dashed"
              disabled={form.items.length >= 100}
              onClick={() =>
                change("items", [
                  ...form.items,
                  {
                    name: "",
                    quantity: "1",
                    unit: "式",
                    unit_price: "0",
                    tax_rate: 10,
                  },
                ])
              }
            >
              <Plus size={17} />
              明細行を追加
            </button>
          </section>
          <section className="panel form-section">
            <div className="section-heading">
              <span className="section-number">03</span>
              <div>
                <h2>条件・備考</h2>
                <p>お取引に必要な条件を添えましょう。</p>
              </div>
            </div>
            <div className="form-grid">
              <Field label="納期・納入条件">
                <input
                  value={form.delivery}
                  maxLength={300}
                  placeholder="例：ご発注から4週間"
                  onChange={(e) => change("delivery", e.target.value)}
                />
              </Field>
              <Field label="お支払条件">
                <input
                  value={form.payment}
                  maxLength={300}
                  onChange={(e) => change("payment", e.target.value)}
                />
              </Field>
            </div>
            <Field label="印鑑画像の表示">
              <select
                value={form.seal_id || ""}
                onChange={(e) =>
                  change(
                    "seal_id",
                    e.target.value ? Number(e.target.value) : null,
                  )
                }
              >
                <option value="">表示しない</option>
                {boot.seal_id && (
                  <option value={boot.seal_id}>
                    現在の会社印・屋号印を表示
                  </option>
                )}
                {form.seal_id && form.seal_id !== boot.seal_id && (
                  <option value={form.seal_id}>
                    この見積で保存した印鑑を表示
                  </option>
                )}
              </select>
            </Field>
            {form.seal_id && (
              <img
                className="seal-preview"
                src={`/api/seals/${form.seal_id}`}
                alt="見積に表示する印鑑"
              />
            )}
            {!boot.seal_id && (
              <p className="muted">
                印鑑を使う場合は会社設定から画像を登録できます。
              </p>
            )}
            <Field label="備考（PDFに表示）">
              <textarea
                rows={3}
                maxLength={3000}
                value={form.notes}
                onChange={(e) => change("notes", e.target.value)}
              />
            </Field>
            <Field label="社内メモ（PDFには表示されません）">
              <textarea
                rows={2}
                maxLength={3000}
                value={form.internal_note}
                onChange={(e) => change("internal_note", e.target.value)}
              />
            </Field>
          </section>
        </div>
        <aside className="editor-summary panel">
          <div className="eyebrow">ESTIMATE SUMMARY</div>
          <h3>お見積金額</h3>
          <div className="summary-line">
            <span>小計</span>
            <strong>{yen(subtotal)}</strong>
          </div>
          <div className="summary-line">
            <span>消費税</span>
            <strong>{yen(tax)}</strong>
          </div>
          <div className="summary-total">
            <span>合計（税込）</span>
            <strong>{yen(total)}</strong>
          </div>
          <p>
            明細金額は四捨五入、税率ごとの消費税は切り捨て。保存時に金額を確定します。
          </p>
          <div className="summary-company">
            <Building2 size={18} />
            <div>
              {boot.company.name}
              <small>{boot.me.name}</small>
            </div>
          </div>
          <div className="summary-flow">
            <ShieldCheck size={18} />
            {boot.company.approval_mode === "none"
              ? "保存後、そのまま発行できます"
              : "保存後、承認を申請できます"}
          </div>
        </aside>
      </div>
    </form>
  );
}

function QuoteDetail({ rid }: { rid: number }) {
  const { refresh, notify, boot } = useApp();
  const [data, setData] = useState<any>(),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [comment, setComment] = useState(""),
    [returning, setReturning] = useState(false);
  useEffect(() => {
    setData(undefined);
    setError("");
    api(`/revisions/${rid}`)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [rid]);
  async function act(action: string) {
    setBusy(true);
    setError("");
    try {
      const d = await post(`/revisions/${rid}/${action}`, {
        lock_version: data.lock_version,
        comment,
      });
      setData(d);
      await refresh();
      setReturning(false);
      setComment("");
      notify(
        (
          {
            issue: "見積書を発行しました",
            submit: "承認を申請しました",
            approve: "承認しました",
            return: "差し戻しました",
            withdraw: "申請を取り下げました",
            reopen: "下書きに戻しました",
            revise: "新しい版を作成しました",
            duplicate: "見積書を複製しました",
          } as any
        )[action],
      );
      if (d.revision_id !== rid) navigate(`/revisions/${d.revision_id}`);
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
        {!error && <div className="loading">見積書を読み込んでいます…</div>}
        <button className="back-link" onClick={() => navigate("/quotes")}>
          <ArrowLeft size={16} />
          一覧へ戻る
        </button>
      </>
    );
  const p = data.payload,
    request = data.approvals[0];
  return (
    <>
      <button className="back-link" onClick={() => navigate("/quotes")}>
        <ArrowLeft size={16} />
        見積書一覧へ
      </button>
      <PageTitle
        eyebrow={data.number || "DRAFT ESTIMATE"}
        title={p.title}
        description={`${p.customer.name} / ${data.owner_name}`}
      >
        <Badge status={data.status} />
        <select
          aria-label="版を切り替え"
          value={rid}
          onChange={(e) => navigate(`/revisions/${e.target.value}`)}
        >
          {data.revisions.map((r: any) => (
            <option key={r.id} value={r.id}>
              第{r.version}版・{statuses[r.status]}
            </option>
          ))}
        </select>
      </PageTitle>
      <ErrorBox error={error} />
      <div className="detail-toolbar">
        <a
          className="button secondary"
          href={`/api/revisions/${rid}/pdf${data.status === "issued" ? "?download=true" : ""}`}
          target="_blank"
          rel="noreferrer"
        >
          <Download size={17} />
          {data.status === "issued" ? "PDFをダウンロード" : "PDFプレビュー"}
        </a>
        <div className="toolbar-right">
          {data.editable && (
            <>
              <button
                className="button subtle"
                disabled={busy}
                onClick={() => act("duplicate")}
              >
                <Copy size={16} />
                複製
              </button>
              {["draft", "returned"].includes(data.status) && (
                <>
                  <button
                    className="button secondary"
                    onClick={() => navigate(`/revisions/${rid}/edit`)}
                  >
                    <Pencil size={16} />
                    編集
                  </button>
                  <button
                    className="button primary"
                    disabled={busy}
                    onClick={() =>
                      act(
                        boot.company.approval_mode === "none"
                          ? "issue"
                          : "submit",
                      )
                    }
                  >
                    <Send size={16} />
                    {boot.company.approval_mode === "none"
                      ? "見積書を発行"
                      : "承認を申請"}
                  </button>
                </>
              )}
              {data.status === "approved" && (
                <>
                  <button
                    className="button secondary"
                    disabled={busy}
                    onClick={() => act("reopen")}
                  >
                    承認を解除して編集
                  </button>
                  <button
                    className="button primary"
                    disabled={busy}
                    onClick={() => act("issue")}
                  >
                    <Send size={16} />
                    見積書を発行
                  </button>
                </>
              )}
              {data.status === "issued" && (
                <button
                  className="button primary"
                  disabled={busy}
                  onClick={() => act("revise")}
                >
                  <Plus size={16} />
                  改訂版を作成
                </button>
              )}
            </>
          )}
          {data.can_withdraw && (
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => act("withdraw")}
            >
              申請を取下げ
            </button>
          )}
          {data.can_approve && (
            <>
              <button
                className="button secondary"
                disabled={busy}
                onClick={() => setReturning(true)}
              >
                差し戻す
              </button>
              <button
                className="button primary"
                disabled={busy}
                onClick={() => act("approve")}
              >
                <CheckCheck size={18} />
                この段階を承認
              </button>
            </>
          )}
        </div>
      </div>
      <QuoteScope data={data} />
      <QuoteSales
        data={data}
        boot={boot}
        refresh={refresh}
        notify={notify}
        onChange={() =>
          api(`/revisions/${rid}`)
            .then(setData)
            .catch((e) => setError(e.message))
        }
      />
      <div className="detail-layout">
        <article className="estimate-paper">
          <div className="paper-heading">
            <div>
              <span className="eyebrow">ESTIMATE</span>
              <h2>御見積書</h2>
            </div>
            <div>
              <strong>{data.number || "下書き"}</strong>
              <span>第{data.version}版</span>
              <span>有効期限：{dateText(p.valid_until)}</span>
            </div>
          </div>
          <div className="paper-parties">
            <div>
              <h3>
                {p.customer.name} <small>御中</small>
              </h3>
              <p>
                {p.customer.address}
                <br />
                {p.customer.contact}
              </p>
            </div>
            <div>
              <strong>{p.issuer.name}</strong>
              <p>
                {p.issuer.address}
                <br />
                {p.issuer.phone}
                <br />
                {p.organization}
                <br />
                担当：{p.owner_name}
              </p>
              {p.seal_id && (
                <img
                  className="seal-preview paper-seal"
                  src={`/api/seals/${p.seal_id}`}
                  alt="会社印・屋号印"
                />
              )}
            </div>
          </div>
          <p className="paper-subject">件名：{p.title}</p>
          <p className="paper-greeting">
            下記のとおり、お見積もり申し上げます。
          </p>
          <div className="paper-total">
            <span>
              お見積金額 <small>税込</small>
            </span>
            <strong>{yen(p.total)}</strong>
          </div>
          <div className="table-scroll">
            <table className="paper-lines">
              <thead>
                <tr>
                  <th>品名・内容</th>
                  <th>数量</th>
                  <th>単位</th>
                  <th className="right">単価</th>
                  <th>税率</th>
                  <th className="right">金額</th>
                </tr>
              </thead>
              <tbody>
                {p.items.map((it: any, i: number) => (
                  <tr key={i}>
                    <td>{it.name}</td>
                    <td>{it.quantity}</td>
                    <td>{it.unit}</td>
                    <td className="right">{unitYen(it.unit_price)}</td>
                    <td>{it.tax_rate}%</td>
                    <td className="money">{yen(it.amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="paper-sums">
            <div>
              <span>小計</span>
              <span>{yen(p.subtotal)}</span>
            </div>
            {Object.entries(p.taxes).map(([rate, value]) => (
              <div key={rate}>
                <span>消費税（{rate}%）</span>
                <span>{yen(value as string)}</span>
              </div>
            ))}
            <div className="grand">
              <strong>合計（税込）</strong>
              <strong>{yen(p.total)}</strong>
            </div>
          </div>
          <div className="paper-conditions">
            {[
              ["納期・納入条件", p.delivery],
              ["お支払条件", p.payment],
              ["備考", p.notes],
            ].map(
              ([label, value]) =>
                value && (
                  <div key={label}>
                    <strong>{label}</strong>
                    <p>{value}</p>
                  </div>
                ),
            )}
          </div>
        </article>
        <aside className="detail-aside">
          <section className="panel side-section">
            <h3>
              <ShieldCheck size={17} />
              承認状況
            </h3>
            {request ? (
              <>
                <span className="muted small">
                  申請 #{request.id} · {dateText(request.created_at)}
                </span>
                <div className="approval-timeline">
                  {request.steps.map((s: any) => (
                    <div className={`approval-step ${s.status}`} key={s.id}>
                      <span className="step-dot">
                        {s.status === "approved" ? (
                          <Check size={14} />
                        ) : (
                          s.position
                        )}
                      </span>
                      <div>
                        <strong>{s.name}</strong>
                        <span>{s.approver_name}</span>
                        <small>
                          {
                            (
                              {
                                approved: "承認済み",
                                pending: "承認待ち",
                                waiting: "前の段階を待っています",
                                returned: "差戻し",
                                cancelled: "終了",
                              } as any
                            )[s.status]
                          }
                        </small>
                        {s.comment && <p>{s.comment}</p>}
                      </div>
                    </div>
                  ))}
                </div>
                {data.approvals.length > 1 && (
                  <details>
                    <summary>
                      以前の申請（{data.approvals.length - 1}件）
                    </summary>
                    {data.approvals.slice(1).map((a: any) => (
                      <div className="past-request" key={a.id}>
                        <strong>申請 #{a.id}</strong>
                        {a.steps.map((s: any) => (
                          <p key={s.id}>
                            {s.name} / {s.approver_name}
                            <br />
                            {
                              (
                                {
                                  approved: "承認済み",
                                  pending: "承認待ち",
                                  waiting: "未開始",
                                  returned: "差戻し",
                                  cancelled: "終了",
                                } as any
                              )[s.status]
                            }{" "}
                            {s.comment}
                          </p>
                        ))}
                      </div>
                    ))}
                  </details>
                )}
              </>
            ) : (
              <div className="no-approval">
                <CircleCheck size={26} />
                <strong>
                  {boot.company.approval_mode === "none"
                    ? "承認は不要です"
                    : "まだ申請されていません"}
                </strong>
                <p>
                  {boot.company.approval_mode === "none"
                    ? "内容を確認したら、そのまま発行できます。"
                    : "内容を確認して承認を申請してください。"}
                </p>
              </div>
            )}
          </section>
          {p.internal_note && (
            <section className="panel side-section">
              <h3>社内メモ</h3>
              <p className="pre-wrap">{p.internal_note}</p>
              <small className="muted">PDFには表示されません</small>
            </section>
          )}
          <section className="panel side-section">
            <h3>
              <History size={17} />
              操作履歴
            </h3>
            <div className="history-list">
              {data.history.map((h: any) => (
                <div key={h.id}>
                  <i />
                  <strong>{h.action}</strong>
                  <p>
                    {h.actor} · {dateText(h.created_at)}
                  </p>
                  {h.detail && <small>{h.detail}</small>}
                </div>
              ))}
              {!data.history.length && (
                <p className="muted">表示できる操作履歴はありません。</p>
              )}
            </div>
          </section>
        </aside>
      </div>
      {returning && (
        <Modal title="見積書を差し戻す" onClose={() => setReturning(false)}>
          <p className="muted">修正してほしい内容を申請者に伝えてください。</p>
          <Field label="差戻し理由 *">
            <textarea
              autoFocus
              rows={4}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
          </Field>
          <button
            className="button primary full"
            disabled={!comment.trim() || busy}
            onClick={() => act("return")}
          >
            理由を添えて差し戻す
          </button>
        </Modal>
      )}
    </>
  );
}

function Approvals() {
  const { approvals } = useApp();
  return (
    <>
      <PageTitle
        eyebrow="APPROVALS"
        title="承認待ち"
        description="あなたの確認を待っている見積書です。順番に承認を進めましょう。"
      />
      <div className="approval-cards">
        {approvals.map((q) => (
          <button
            className="panel approval-card"
            key={q.revision_id}
            onClick={() => navigate(`/revisions/${q.revision_id}`)}
          >
            <div className="approval-card-top">
              <span className="badge pending">
                <Clock3 size={13} />
                {q.step_name}
              </span>
              <span className="muted small">
                {q.position} / {q.step_count} 段階
              </span>
            </div>
            <h3>{q.title}</h3>
            <p>{q.customer_name}</p>
            <strong className="approval-amount">{yen(q.total)}</strong>
            <div className="approval-card-bottom">
              <span>申請者：{q.requester_name}</span>
              <span>
                内容を確認
                <ArrowUpRight size={16} />
              </span>
            </div>
          </button>
        ))}
      </div>
      {!approvals.length && (
        <section className="panel">
          <Empty
            title="承認待ちの見積はありません"
            description="あなたの承認段階に進むと、ここに表示されます。"
          />
        </section>
      )}
    </>
  );
}

function Customers() {
  const { customers, refresh, notify } = useApp();
  const [editing, setEditing] = useState<any>(null),
    [search, setSearch] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function save(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const { id, ...body } = editing;
      id ? await put(`/customers/${id}`, body) : await post("/customers", body);
      await refresh();
      setEditing(null);
      notify("取引先を保存しました");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="CUSTOMERS"
        title="取引先"
        description="大切なお取引先の情報を、ひとつの場所に。"
      >
        <button
          className="button primary"
          onClick={() => {
            setEditing({ name: "", contact: "", address: "", email: "" });
            setError("");
          }}
        >
          <Plus size={18} />
          取引先を追加
        </button>
      </PageTitle>
      <div className="search standalone">
        <Search size={18} />
        <input
          aria-label="取引先を検索"
          placeholder="取引先を検索"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      <div className="customer-grid">
        {customers
          .filter((c) => c.name.includes(search) || c.contact.includes(search))
          .map((c, i) => (
            <article className="panel customer-card" key={c.id}>
              <div className="customer-card-top">
                <span className={`customer-avatar color-${i % 4}`}>
                  {c.name.replace(/株式会社|合同会社|\s/g, "").slice(0, 1)}
                </span>
                <button
                  className="icon-button"
                  aria-label={`${c.name}を編集`}
                  onClick={() => {
                    setEditing({ ...c });
                    setError("");
                  }}
                >
                  <Pencil size={16} />
                </button>
              </div>
              <h3>{c.name}</h3>
              <p>{c.contact || "担当者未設定"}</p>
              <div className="customer-address">
                {c.address || "住所未設定"}
                {c.email && <span>{c.email}</span>}
              </div>
            </article>
          ))}
      </div>
      {!customers.length && (
        <Empty
          title="取引先を登録しましょう"
          description="登録した情報を見積書に自動入力できます。"
        />
      )}
      {editing && (
        <Modal
          title={editing.id ? "取引先を編集" : "取引先を追加"}
          onClose={() => setEditing(null)}
        >
          <form onSubmit={save}>
            {[
              ["name", "会社名・屋号 *"],
              ["contact", "担当者名"],
              ["address", "住所"],
              ["email", "メールアドレス"],
            ].map(([key, label]) => (
              <Field key={key} label={label}>
                <input
                  required={key === "name"}
                  type={key === "email" ? "email" : "text"}
                  value={editing[key]}
                  onChange={(e) =>
                    setEditing({ ...editing, [key]: e.target.value })
                  }
                />
              </Field>
            ))}
            <ErrorBox error={error} />
            <button className="button primary full" disabled={busy}>
              保存する
            </button>
          </form>
        </Modal>
      )}
    </>
  );
}

function SettingsPage() {
  const { boot, refresh, notify } = useApp();
  const [form, setForm] = useState({ ...boot.company }),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  useEffect(() => setForm({ ...boot.company }), [boot.company]);
  const set = (key: string, value: any) =>
    setForm((f: any) => ({ ...f, [key]: value }));
  const updateStep = (index: number, key: string, value: any) =>
    set(
      "route",
      form.route.map((s: any, i: number) =>
        i === index ? { ...s, [key]: value } : s,
      ),
    );
  function move(i: number, delta: number) {
    const rows = [...form.route];
    [rows[i], rows[i + delta]] = [rows[i + delta], rows[i]];
    set("route", rows);
  }
  async function save(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const { id, ...body } = form;
      const c = await put("/settings", body);
      setForm(c);
      await refresh();
      notify("会社設定を保存しました");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (boot.me.role !== "admin")
    return (
      <Empty
        title="会社管理者のみ操作できます"
        description="会社設定の変更は管理者に依頼してください。"
      />
    );
  return (
    <form onSubmit={save}>
      <PageTitle
        eyebrow="WORKSPACE SETTINGS"
        title="会社設定"
        description="あなたの仕事に合う、ちょうどよい運用に。"
      >
        <button className="button primary" disabled={busy}>
          <Check size={17} />
          {busy ? "保存中…" : "設定を保存"}
        </button>
      </PageTitle>
      <ErrorBox error={error} />
      <div className="settings-layout">
        <div>
          <section className="panel form-section">
            <div className="section-heading">
              <Building2 size={22} />
              <div>
                <h2>事業者情報</h2>
                <p>新しく作成する見積書に表示されます。</p>
              </div>
            </div>
            <Field label="登録番号（登録済みの事業者のみ）">
              <input
                pattern="T[0-9]{13}"
                maxLength={14}
                value={form.registration_number || ""}
                placeholder="T＋13桁の数字（任意）"
                onChange={(e) => set("registration_number", e.target.value)}
              />
            </Field>
            <Field label="請求書のお振込先（初期値）">
              <textarea
                rows={3}
                maxLength={500}
                value={form.bank_details || ""}
                onChange={(e) => set("bank_details", e.target.value)}
              />
            </Field>
            <Field label="新規見積での印鑑表示">
              <select
                value={String(form.seal_default)}
                onChange={(e) => set("seal_default", e.target.value === "true")}
              >
                <option value="false">表示しない</option>
                <option value="true">登録した印鑑を表示</option>
              </select>
            </Field>
            <Field label="会社名・屋号・氏名 *">
              <input
                required
                maxLength={120}
                value={form.name}
                onChange={(e) => set("name", e.target.value)}
              />
            </Field>
            <div className="form-grid">
              <Field label="住所">
                <input
                  maxLength={300}
                  value={form.address}
                  onChange={(e) => set("address", e.target.value)}
                />
              </Field>
              <Field label="電話番号">
                <input
                  maxLength={60}
                  value={form.phone}
                  onChange={(e) => set("phone", e.target.value)}
                />
              </Field>
            </div>
          </section>
          <SealSettings boot={boot} refresh={refresh} notify={notify} />
          <section className="panel form-section">
            <div className="section-heading">
              <ShieldCheck size={22} />
              <div>
                <h2>承認フロー</h2>
                <p>事業者ごとに、必要な確認の段階を設定できます。</p>
              </div>
            </div>
            <div className="mode-options">
              <button
                type="button"
                className={
                  form.approval_mode === "none"
                    ? "mode-option selected"
                    : "mode-option"
                }
                onClick={() => set("approval_mode", "none")}
              >
                <span className="radio-circle" />
                <div>
                  <strong>承認なし</strong>
                  <p>
                    作成した担当者がそのまま発行。
                    <br />
                    個人での利用におすすめです。
                  </p>
                </div>
                <Sparkles size={20} />
              </button>
              <button
                type="button"
                className={
                  form.approval_mode === "sequential"
                    ? "mode-option selected"
                    : "mode-option"
                }
                onClick={() => set("approval_mode", "sequential")}
              >
                <span className="radio-circle" />
                <div>
                  <strong>多段階承認</strong>
                  <p>
                    指定した順序で確認してから発行。
                    <br />
                    1段階から設定できます。
                  </p>
                </div>
                <Users size={20} />
              </button>
            </div>
            {form.approval_mode === "sequential" && (
              <div className="route-builder">
                <div className="route-header">
                  <strong>承認の順序</strong>
                  <small>最大10段階</small>
                </div>
                {form.route.map((s: any, i: number) => (
                  <div className="route-step" key={i}>
                    <span className="route-number">{i + 1}</span>
                    <div className="route-fields">
                      <Field label="段階名">
                        <input
                          required
                          placeholder="例：課長確認"
                          value={s.name}
                          onChange={(e) =>
                            updateStep(i, "name", e.target.value)
                          }
                        />
                      </Field>
                      <Field label="承認者">
                        <select
                          required
                          value={s.approver_id || ""}
                          onChange={(e) =>
                            updateStep(i, "approver_id", Number(e.target.value))
                          }
                        >
                          <option value="" disabled>
                            選択してください
                          </option>
                          {boot.members
                            .filter((m: any) => m.active)
                            .map((m: any) => (
                              <option key={m.id} value={m.id}>
                                {m.name}
                              </option>
                            ))}
                        </select>
                      </Field>
                      <Field label="代理承認者（任意）">
                        <select
                          value={s.backup_id || ""}
                          onChange={(e) =>
                            updateStep(
                              i,
                              "backup_id",
                              e.target.value ? Number(e.target.value) : null,
                            )
                          }
                        >
                          <option value="">設定しない</option>
                          {boot.members
                            .filter((m: any) => m.active)
                            .map((m: any) => (
                              <option key={m.id} value={m.id}>
                                {m.name}
                              </option>
                            ))}
                        </select>
                      </Field>
                    </div>
                    <div className="route-buttons">
                      <button
                        type="button"
                        className="icon-button"
                        aria-label={`第${i + 1}段階を上へ`}
                        disabled={i === 0}
                        onClick={() => move(i, -1)}
                      >
                        <ArrowUp size={14} />
                      </button>
                      <button
                        type="button"
                        className="icon-button"
                        aria-label={`第${i + 1}段階を下へ`}
                        disabled={i === form.route.length - 1}
                        onClick={() => move(i, 1)}
                      >
                        <ArrowDown size={14} />
                      </button>
                      <button
                        type="button"
                        className="icon-button danger"
                        aria-label={`第${i + 1}段階を削除`}
                        onClick={() =>
                          set(
                            "route",
                            form.route.filter((_: any, n: number) => n !== i),
                          )
                        }
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
                <button
                  type="button"
                  className="button dashed"
                  disabled={form.route.length >= 10}
                  onClick={() =>
                    set("route", [
                      ...form.route,
                      {
                        name: "",
                        approver_id: boot.members[0]?.id,
                        backup_id: null,
                      },
                    ])
                  }
                >
                  <Plus size={17} />
                  承認段階を追加
                </button>
                <div className="notice">
                  <CircleHelp size={18} />
                  <span>
                    自己承認はできません。承認者自身が申請する場合は代理承認者を設定してください。差戻し後は最初の段階から再申請します。
                  </span>
                </div>
              </div>
            )}
          </section>
        </div>
        <aside className="settings-note">
          <div className="note-illustration">
            <ShieldCheck size={30} />
          </div>
          <h3>ひとりでも、チームでも。</h3>
          <p>組織や承認フローは、仕事に必要になったときに設定すれば大丈夫。</p>
          <div className="note-divider" />
          <strong>進行中の申請はそのまま</strong>
          <p>経路の変更は、新しく申請する見積から適用されます。</p>
          <strong>発行済みの内容を保持</strong>
          <p>会社情報を変更しても、保存済みのPDFは変わりません。</p>
        </aside>
      </div>
    </form>
  );
}

function Team() {
  const { boot, refresh, notify } = useApp();
  const [modal, setModal] = useState(""),
    [form, setForm] = useState<any>({}),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function save(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await post(modal === "member" ? "/members" : "/organizations", form);
      await refresh();
      notify("登録しました");
      setModal("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const start = (type: string) => {
    setModal(type);
    setError("");
    setForm(
      type === "member"
        ? {
            username: "",
            display_name: "",
            password: "",
            role: "member",
            section_id: null,
          }
        : type === "department"
          ? { name: "", department_id: null }
          : { name: "", department_id: boot.departments[0]?.id },
    );
  };
  return (
    <>
      <PageTitle
        eyebrow="PEOPLE & ORGANIZATION"
        title="メンバー・組織"
        description="一緒に働くメンバーと、仕事を共有する範囲を管理します。"
      >
        {boot.me.role === "admin" && (
          <button className="button primary" onClick={() => start("member")}>
            <Plus size={18} />
            メンバーを追加
          </button>
        )}
      </PageTitle>
      <section className="panel">
        <div className="panel-heading">
          <h2>
            メンバー <span className="count">{boot.members.length}</span>
          </h2>
        </div>
        <div className="table-scroll">
          <table className="members-table">
            <thead>
              <tr>
                <th>メンバー</th>
                <th>ユーザー名</th>
                <th>所属</th>
                <th>権限</th>
                <th>状態</th>
              </tr>
            </thead>
            <tbody>
              {boot.members.map((m: any) => (
                <tr key={m.id}>
                  <td>
                    <div className="member-cell">
                      <span className="avatar">{m.name.slice(0, 1)}</span>
                      <strong>{m.name}</strong>
                      {m.id === boot.me.id && (
                        <small className="you-tag">あなた</small>
                      )}
                    </div>
                  </td>
                  <td className="muted">{m.username}</td>
                  <td>
                    {boot.sections.find((s: any) => s.id === m.section_id)
                      ?.name || "所属なし"}
                  </td>
                  <td>
                    <span className="role-tag">{roles[m.role]}</span>
                  </td>
                  <td>
                    <span className="active-user">
                      <i />
                      {m.active ? "利用中" : "停止中"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="panel organization-panel">
        <div className="panel-heading">
          <div>
            <h2>部・課</h2>
            <p>個人で利用する場合、組織の登録は不要です。</p>
          </div>
          {boot.me.role === "admin" && (
            <div className="page-actions">
              <button
                className="button secondary"
                onClick={() => start("department")}
              >
                <Plus size={15} />
                部を追加
              </button>
              <button
                className="button secondary"
                disabled={!boot.departments.length}
                onClick={() => start("section")}
              >
                <Plus size={15} />
                課を追加
              </button>
            </div>
          )}
        </div>
        {!boot.departments.length ? (
          <div className="organization-empty">
            <Building2 size={30} />
            <p>部・課は設定されていません</p>
            <small>このまま見積を作成・発行できます。</small>
          </div>
        ) : (
          <div className="org-grid">
            {boot.departments.map((d: any) => (
              <div className="org-department" key={d.id}>
                <strong>
                  <Building2 size={18} />
                  {d.name}
                </strong>
                {boot.sections
                  .filter((s: any) => s.department_id === d.id)
                  .map((s: any) => (
                    <div key={s.id}>
                      <span className="branch-line" />
                      {s.name}
                      <small>
                        {
                          boot.members.filter((m: any) => m.section_id === s.id)
                            .length
                        }
                        名
                      </small>
                    </div>
                  ))}
              </div>
            ))}
          </div>
        )}
      </section>
      {modal && (
        <Modal
          title={
            modal === "member"
              ? "メンバーを追加"
              : modal === "department"
                ? "部を追加"
                : "課を追加"
          }
          onClose={() => setModal("")}
        >
          <form onSubmit={save}>
            {modal === "member" ? (
              <>
                <Field label="氏名 *">
                  <input
                    required
                    value={form.display_name}
                    onChange={(e) =>
                      setForm({ ...form, display_name: e.target.value })
                    }
                  />
                </Field>
                <Field label="ユーザー名 *（半角英数字・_.-）">
                  <input
                    required
                    pattern="[a-zA-Z0-9_.\-]{3,80}"
                    value={form.username}
                    onChange={(e) =>
                      setForm({ ...form, username: e.target.value })
                    }
                  />
                </Field>
                <Field label="パスワード *（8文字以上）">
                  <input
                    type="password"
                    required
                    minLength={8}
                    autoComplete="new-password"
                    value={form.password}
                    onChange={(e) =>
                      setForm({ ...form, password: e.target.value })
                    }
                  />
                </Field>
                <Field label="権限">
                  <select
                    value={form.role}
                    onChange={(e) => setForm({ ...form, role: e.target.value })}
                  >
                    {Object.entries(roles).map(([id, label]) => (
                      <option key={id} value={id}>
                        {label}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="所属課">
                  <select
                    value={form.section_id || ""}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        section_id: e.target.value
                          ? Number(e.target.value)
                          : null,
                      })
                    }
                  >
                    <option value="">所属なし</option>
                    {boot.sections.map((s: any) => (
                      <option key={s.id} value={s.id}>
                        {
                          boot.departments.find(
                            (d: any) => d.id === s.department_id,
                          )?.name
                        }{" "}
                        / {s.name}
                      </option>
                    ))}
                  </select>
                </Field>
              </>
            ) : (
              <>
                <Field label="名前 *">
                  <input
                    required
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                  />
                </Field>
                {modal === "section" && (
                  <Field label="所属する部">
                    <select
                      required
                      value={form.department_id}
                      onChange={(e) =>
                        setForm({
                          ...form,
                          department_id: Number(e.target.value),
                        })
                      }
                    >
                      {boot.departments.map((d: any) => (
                        <option key={d.id} value={d.id}>
                          {d.name}
                        </option>
                      ))}
                    </select>
                  </Field>
                )}
              </>
            )}
            <ErrorBox error={error} />
            <button className="button primary full" disabled={busy}>
              登録する
            </button>
          </form>
        </Modal>
      )}
    </>
  );
}

function Activity() {
  const [data, setData] = useState<any[]>([]),
    [error, setError] = useState("");
  useEffect(() => {
    api("/audit")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <>
      <PageTitle
        eyebrow="ACTIVITY"
        title="操作履歴"
        description="見積や設定の変更を、時系列で確認できます。"
      />
      <ErrorBox error={error} />
      <section className="panel">
        <div className="activity-list">
          {data.map((h) => (
            <div key={h.id}>
              <span className="activity-icon">
                <History size={17} />
              </span>
              <div>
                <strong>{h.action}</strong>
                <p>{h.detail || "—"}</p>
              </div>
              <span>{h.actor}</span>
              <time>{new Date(h.created_at).toLocaleString("ja-JP")}</time>
            </div>
          ))}
        </div>
        {!data.length && !error && (
          <Empty
            title="操作履歴はまだありません"
            description="見積書を作成すると、ここに履歴が表示されます。"
          />
        )}
      </section>
    </>
  );
}

function App() {
  const [boot, setBoot] = useState<any>(),
    [quotes, setQuotes] = useState<QuoteSummary[]>([]),
    [customers, setCustomers] = useState<any[]>([]),
    [approvals, setApprovals] = useState<any[]>([]),
    [loading, setLoading] = useState(true),
    [setupRequired, setSetupRequired] = useState(false),
    [desktopMode, setDesktopMode] = useState(false),
    [demoAvailable, setDemoAvailable] = useState(false),
    [hash, setHash] = useState(window.location.hash.slice(1) || "/quotes"),
    [toast, setToast] = useState("");
  const projectReturn = useRef("/studio");
  const desktopModeRef = useRef(false);
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [hash]);
  async function refresh() {
    const b = await api("/bootstrap");
    const [q, c, a] = await Promise.all([
      api("/quotes"),
      api("/customers"),
      api("/approvals"),
    ]);
    setBoot(b);
    setQuotes(q);
    setCustomers(c);
    setApprovals(a);
  }
  useEffect(() => {
    api<{ required: boolean; demo_available: boolean; desktop_mode?: boolean }>("/setup/status")
      .then(async (status) => {
        setSetupRequired(status.required);
        setDemoAvailable(status.demo_available);
        setDesktopMode(!!status.desktop_mode);
        desktopModeRef.current = !!status.desktop_mode;
        if (!status.required) {
          if (status.desktop_mode) {
            try {
              await post("/desktop/resume", {});
            } catch {
              // Multi-user desktop databases retain the normal login screen.
              setDesktopMode(false);
              desktopModeRef.current = false;
            }
          }
          await refresh().catch(() => setBoot(null));
        }
      })
      .catch(() => setBoot(null))
      .finally(() => setLoading(false));
    const change = () =>
      setHash((previous) => {
        const next = window.location.hash.slice(1) || "/quotes";
        if (
          /^\/projects\/(\d+|new)$/.test(next) &&
          ["/projects", "/studio"].includes(previous)
        )
          projectReturn.current = previous;
        return next;
      });
    const expired = async () => {
      if (desktopModeRef.current) {
        try {
          await post("/desktop/resume", {});
          await refresh();
          return;
        } catch {
          // Show the login screen if the desktop session cannot be restored.
        }
      }
      setBoot(null);
    };
    window.addEventListener("hashchange", change);
    window.addEventListener("session-expired", expired);
    return () => {
      window.removeEventListener("hashchange", change);
      window.removeEventListener("session-expired", expired);
    };
  }, []);
  useEffect(() => {
    if (toast) {
      const t = setTimeout(() => setToast(""), 4500);
      return () => clearTimeout(t);
    }
  }, [toast]);
  async function logout() {
    await post("/auth/logout", {});
    setBoot(null);
    setQuotes([]);
    setCustomers([]);
    setApprovals([]);
  }
  if (loading)
    return (
      <div className="app-loading">
        <Logo />
        <span>ワークスペースを開いています…</span>
      </div>
    );
  if (!boot)
    return (
      <Login
        onLogin={async () => {
          await refresh();
          setSetupRequired(false);
        }}
        setupRequired={setupRequired}
        demoAvailable={demoAvailable}
        desktopMode={desktopMode}
      />
    );
  const match = hash.match(/^\/revisions\/(\d+)(\/edit)?$/);
  const section =
    match || hash.startsWith("/quotes/new") ? "quotes" : hash.split("/")[1];
  const nav = [
    { id: "studio", label: "アトリエ", icon: House },
    { id: "projects", label: "案件管理", icon: BriefcaseBusiness },
    { id: "quotes", label: "見積書", icon: FileText },
    { id: "orders", label: "受注管理", icon: BriefcaseBusiness },
    { id: "invoices", label: "請求・入金", icon: FileText },
    { id: "approvals", label: "承認待ち", icon: CheckCheck },
    { id: "customers", label: "取引先", icon: BriefcaseBusiness },
  ];
  const manage = [
    { id: "manual", label: "操作マニュアル", icon: CircleHelp },
    { id: "team", label: "メンバー・組織", icon: Users },
    ...(boot.me.role === "admin"
      ? [
          { id: "settings", label: "会社設定", icon: Settings },
          { id: "activity", label: "操作履歴", icon: History },
        ]
      : []),
  ];
  const studio = (
    <StudioHome boot={boot} quotes={quotes} approvals={approvals} />
  );
  const projectId = Number(hash.split("/")[2]) || undefined;
  const newProject = hash === "/projects/new";
  const projects = (
    <Projects
      key={hash}
      id={projectId}
      initialCreate={newProject}
      inPanel={!!projectId || newProject}
      customers={customers}
      boot={boot}
      refresh={refresh}
      notify={setToast}
    />
  );
  const page =
    section === "studio" || !section ? (
      studio
    ) : match ? (
      match[2] ? (
        <QuoteEditor key={hash} rid={Number(match[1])} />
      ) : (
        <QuoteDetail key={hash} rid={Number(match[1])} />
      )
    ) : hash.startsWith("/quotes/new") ? (
      <QuoteEditor
        key={hash}
        projectId={
          Number(new URLSearchParams(hash.split("?")[1]).get("project")) ||
          undefined
        }
      />
    ) : section === "projects" ? (
      projectId || newProject ? (
        <>
          {projectReturn.current === "/projects" ? (
            <Projects
              customers={customers}
              boot={boot}
              refresh={refresh}
              notify={setToast}
            />
          ) : (
            studio
          )}
          <StudioPanel
            key={hash}
            title={newProject ? "新しい案件ノート" : "案件ノート"}
            onClose={() => navigate(projectReturn.current)}
          >
            {projects}
          </StudioPanel>
        </>
      ) : (
        projects
      )
    ) : section === "manual" ? (
      <Suspense
        fallback={<div className="loading">マニュアルを読み込んでいます…</div>}
      >
        <Manual articleId={hash.split("/")[2] || "first-steps"} />
      </Suspense>
    ) : section === "orders" || section === "invoices" ? (
      <Commerce
        key={hash}
        kind={section}
        id={Number(hash.split("/")[2]) || undefined}
        boot={boot}
        refresh={refresh}
        notify={setToast}
      />
    ) : section === "approvals" ? (
      <Approvals />
    ) : section === "customers" ? (
      <Customers />
    ) : section === "team" ? (
      <Team />
    ) : section === "settings" ? (
      <SettingsPage />
    ) : section === "activity" ? (
      <Activity />
    ) : (
      <Quotes />
    );
  return (
    <AppContext.Provider
      value={{ boot, quotes, customers, approvals, refresh, notify: setToast }}
    >
      <div className="app-shell">
        <aside className="sidebar">
          <div className="sidebar-brand">
            <Logo />
            <span className="brand-caption">小さな仕事を、大切に育てる。</span>
          </div>
          <div className="workspace">
            <span className="workspace-icon">
              <Building2 size={19} />
            </span>
            <div>
              <strong>{boot.company.name}</strong>
              <span>ワークスペース</span>
            </div>
          </div>
          <div className="nav-group">
            <div className="nav-caption">日々のおしごと</div>
            {nav.map((n) => (
              <button
                key={n.id}
                aria-label={n.label}
                title={n.label}
                className={`nav-item ${section === n.id ? "active" : ""}`}
                onClick={() => navigate(`/${n.id}`)}
              >
                <n.icon size={19} />
                <span>{n.label}</span>
                {n.id === "approvals" && approvals.length > 0 && (
                  <b>{approvals.length}</b>
                )}
                {section === n.id && <span className="nav-active-dot" />}
              </button>
            ))}
          </div>
          <div className="nav-group">
            <div className="nav-caption">アトリエの道具</div>
            {manage.map((n) => (
              <button
                key={n.id}
                aria-label={n.label}
                title={n.label}
                className={`nav-item ${section === n.id ? "active" : ""}`}
                onClick={() => navigate(`/${n.id}`)}
              >
                <n.icon size={19} />
                <span>{n.label}</span>
                {section === n.id && <span className="nav-active-dot" />}
              </button>
            ))}
          </div>
          <div className="sidebar-bottom">
            <button
              className="help-card"
              onClick={() => navigate("/manual/first-steps")}
            >
              <span className="help-spark">
                <Sparkles size={19} />
              </span>
              <strong>はじめての方へ</strong>
              <p>見積管理システムの使い方をご紹介</p>
              <ArrowUpRight size={17} />
            </button>
            <div className="profile">
              <span className="avatar">{boot.me.name.slice(0, 1)}</span>
              <div>
                <strong>{boot.me.name}</strong>
                <small>{roles[boot.me.role]}</small>
              </div>
              {!desktopMode && <button
                className="icon-button"
                title="ログアウト"
                aria-label="ログアウト"
                onClick={logout}
              >
                <LogOut size={18} />
              </button>}
            </div>
          </div>
        </aside>
        <div className="main-shell">
          <header className="topbar">
            <div>
              <span className="topbar-symbol">
                <LayoutGrid size={15} />
              </span>
              <span>ワークスペース</span>
              <ChevronRight size={13} />
              <strong>
                {[...nav, ...manage].find((n) => n.id === section)?.label ||
                  "見積書"}
              </strong>
            </div>
            <div>
              <span className="mode-pill">
                <span />
                {boot.company.approval_mode === "none"
                  ? "承認なしで利用中"
                  : "多段階承認を利用中"}
              </span>
              <button
                className="icon-button"
                title="再読み込み"
                aria-label="データを再読み込み"
                onClick={() =>
                  refresh()
                    .then(() => setToast("最新のデータを表示しています"))
                    .catch((e) => setToast(e.message))
                }
              >
                <RefreshCw size={17} />
              </button>
            </div>
          </header>
          <main className="main-content" key={boot.company.id}>
            {page}
          </main>
          <footer className="app-footer">
            <span>見積管理システム · 設計書と動作サンプル</span>
            <span>LOCAL DEMO · v0.4</span>
          </footer>
        </div>
      </div>
      {toast && (
        <div className="toast" role="status">
          <CircleCheck size={20} />
          {toast}
          <button
            className="icon-button"
            aria-label="通知を閉じる"
            onClick={() => setToast("")}
          >
            <X size={16} />
          </button>
        </div>
      )}
    </AppContext.Provider>
  );
}

const appRoot =
  import.meta.hot?.data.appRoot ?? createRoot(document.getElementById("root")!);
if (import.meta.hot) import.meta.hot.data.appRoot = appRoot;
appRoot.render(<App />);
