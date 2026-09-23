import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { ArrowLeft, BriefcaseBusiness, Plus, Search } from "lucide-react";
import { api, post, put, navigate, yen, dateText, statuses } from "./api";
import { ProjectProgress, StudioProjectCard, projectStates } from "./studio";
import { ProjectAttachments, type Attachment } from "./attachments";
import { ProjectDashboard } from "./project-dashboard";
const requestStates: Record<string, string> = {
  consulting: "相談中",
  estimated: "見積提示",
  agreed: "合意済み",
  in_progress: "対応中",
  review: "顧客確認",
  done: "完了",
};
export const scopes: Record<string, string> = {
  undecided: "未整理",
  included: "今回の対象",
  excluded: "対象外",
  on_hold: "保留",
  additional: "追加見積",
};
const priorities: Record<string, string> = {
  high: "高",
  normal: "通常",
  low: "低",
};
const options = (map: Record<string, string>) =>
  Object.entries(map).map(([v, l]) => (
    <option key={v} value={v}>
      {l}
    </option>
  ));
const Field = ({ label, children }: { label: string; children: ReactNode }) => (
  <label className="field">
    <span>{label}</span>
    {children}
  </label>
);
const ErrorBox = ({ error }: { error: string }) =>
  error ? (
    <div className="error-box" role="alert">
      {error}
    </div>
  ) : null;
type Props = {
  id?: number;
  initialCreate?: boolean;
  inPanel?: boolean;
  customers: any[];
  boot: any;
  notify: (s: string) => void;
  refresh: () => Promise<void>;
};

function ProjectForm({
  data,
  customers,
  onSave,
  onCancel,
}: {
  data?: any;
  customers: any[];
  onSave: (x: any) => Promise<void>;
  onCancel: () => void;
}) {
  const [form, setForm] = useState(
    data
      ? {
          title: data.title,
          customer_id: data.customer_id,
          customer_contact: data.customer_contact || "",
          customer_corporate_number: data.customer_corporate_number || "",
          purpose: data.purpose,
          status: data.status,
          due_on: data.due_on || "",
          external_url: data.external_url,
          lock_version: data.lock_version,
        }
      : {
          title: "",
          customer_id: customers[0]?.id || "",
          customer_contact: customers[0]?.contact || "",
          customer_corporate_number: "",
          purpose: "",
          status: "consulting",
          due_on: "",
          external_url: "",
        },
  );
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const change = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));
  async function save(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await onSave({
        ...form,
        customer_id: Number(form.customer_id),
        due_on: form.due_on || null,
      });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form onSubmit={save} className="panel form-section project-form">
      <h2>{data ? "案件を編集" : "新しい案件"}</h2>
      <ErrorBox error={error} />
      <Field label="案件名 *">
        <input
          required
          maxLength={150}
          value={form.title}
          onChange={(e) => change("title", e.target.value)}
          placeholder="例：予約管理システムの開発"
        />
      </Field>
      <div className="form-grid">
        <Field label="相手先の会社名・屋号（取引先） *">
          <select
            required
            value={form.customer_id}
            onChange={(e) =>
              setForm((f: any) => ({
                ...f,
                customer_id: e.target.value,
                customer_contact:
                  customers.find((c) => c.id === Number(e.target.value))
                    ?.contact || "",
                customer_corporate_number: "",
              }))
            }
          >
            <option value="" disabled>
              取引先を選択
            </option>
            {customers.map((c) => (
              <option value={c.id} key={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="案件の状態">
          <select
            value={form.status}
            onChange={(e) => change("status", e.target.value)}
          >
            {options(projectStates)}
          </select>
        </Field>
      </div>
      <div className="form-grid">
        <Field label="相手先の担当者名">
          <input
            maxLength={120}
            value={form.customer_contact}
            onChange={(e) => change("customer_contact", e.target.value)}
            placeholder="例：山田 太郎"
          />
        </Field>
        <Field label="相手先の法人番号（任意）">
          <input
            inputMode="numeric"
            pattern="[0-9]{13}"
            maxLength={13}
            title="半角数字13桁で入力してください"
            value={form.customer_corporate_number}
            onChange={(e) =>
              change("customer_corporate_number", e.target.value)
            }
            placeholder="半角数字13桁"
          />
        </Field>
      </div>
      <p className="project-dashboard-note">
        会社名・屋号は「取引先」で登録・変更できます。担当者名と法人番号はこの案件用に保存します。法人番号がない場合は空欄のままで構いません。
      </p>
      <Field label="目的・背景">
        <textarea
          rows={3}
          maxLength={5000}
          value={form.purpose}
          onChange={(e) => change("purpose", e.target.value)}
          placeholder="誰の、どんな課題を解決する案件ですか？"
        />
      </Field>
      <div className="form-grid">
        <Field label="目標納期">
          <input
            type="date"
            value={form.due_on}
            onInput={(e) => change("due_on", e.currentTarget.value)}
          />
        </Field>
        <Field label="開発管理の外部リンク">
          <input
            type="url"
            maxLength={1000}
            value={form.external_url}
            onChange={(e) => change("external_url", e.target.value)}
            placeholder="https://github.com/…"
          />
        </Field>
      </div>
      <div className="project-actions">
        <button type="button" className="button secondary" onClick={onCancel}>
          キャンセル
        </button>
        <button className="button primary" disabled={busy || !customers.length}>
          {busy ? "保存中…" : "案件を保存"}
        </button>
      </div>
      {!customers.length && <p>先に「取引先」で顧客を登録してください。</p>}
    </form>
  );
}

function RequestEditor({
  projectId,
  data,
  onDone,
  onCancel,
}: {
  projectId: number;
  data?: any;
  onDone: () => Promise<void>;
  onCancel: () => void;
}) {
  const [form, setForm] = useState({
    title: data?.title || "",
    description: data?.description || "",
    acceptance: data?.acceptance || "",
    questions: data?.questions || "",
    priority: data?.priority || "normal",
    scope: data?.scope || "undecided",
    status: data?.status || "consulting",
    change_note: "",
  });
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const change = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));
  async function save(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const url = `/projects/${projectId}/requests`;
      if (data)
        await put(`${url}/${data.id}`, {
          ...form,
          lock_version: data.lock_version,
        });
      else await post(url, form);
      await onDone();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form onSubmit={save} className="panel form-section project-form">
      <h2>{data ? `要望 #${data.id} を編集` : "要望を追加"}</h2>
      <ErrorBox error={error} />
      {data?.agreement && (
        <div className="notice">
          合意した件名・内容・完了条件・対象範囲を変更すると「相談中」に戻ります。以前の合意は履歴に残ります。
        </div>
      )}
      <Field label="要望名 *">
        <input
          required
          maxLength={150}
          value={form.title}
          onChange={(e) => change("title", e.target.value)}
          placeholder="例：空き時間から予約できる"
        />
      </Field>
      <Field label="要望の内容">
        <textarea
          rows={3}
          maxLength={5000}
          value={form.description}
          onChange={(e) => change("description", e.target.value)}
        />
      </Field>
      <Field label="完了条件">
        <textarea
          rows={2}
          maxLength={3000}
          value={form.acceptance}
          onChange={(e) => change("acceptance", e.target.value)}
          placeholder="どこまでできたら完了とするか"
        />
      </Field>
      <Field label="確認事項">
        <textarea
          rows={2}
          maxLength={3000}
          value={form.questions}
          onChange={(e) => change("questions", e.target.value)}
          placeholder="未確認の点。解決したら消して保存します。"
        />
      </Field>
      <div className="form-grid">
        <Field label="対象範囲">
          <select
            value={form.scope}
            onChange={(e) => change("scope", e.target.value)}
          >
            {options(scopes)}
          </select>
        </Field>
        <Field label="優先度">
          <select
            value={form.priority}
            onChange={(e) => change("priority", e.target.value)}
          >
            {options(priorities)}
          </select>
        </Field>
        <Field label="要望の状態">
          <select
            value={form.status}
            onChange={(e) => change("status", e.target.value)}
          >
            {options(
              data?.agreement
                ? requestStates
                : { consulting: "相談中", estimated: "見積提示" },
            )}
          </select>
        </Field>
      </div>
      <Field label="変更理由・記録">
        <input
          maxLength={1000}
          value={form.change_note}
          onChange={(e) => change("change_note", e.target.value)}
          placeholder="例：9/19 打ち合わせで対象を追加"
        />
      </Field>
      <div className="project-actions">
        <button type="button" className="button secondary" onClick={onCancel}>
          キャンセル
        </button>
        <button className="button primary" disabled={busy}>
          要望を保存
        </button>
      </div>
    </form>
  );
}

function RequestHistory({
  pid,
  rid,
  onClose,
}: {
  pid: number;
  rid: number;
  onClose: () => void;
}) {
  const [items, setItems] = useState<any[]>(),
    [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    api(`/projects/${pid}/requests/${rid}/history`)
      .then((d) => {
        if (active) setItems(d);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [pid, rid]);
  return (
    <section className="panel form-section">
      <div className="project-section-title">
        <h2>要望 #{rid} の変更履歴</h2>
        <button className="button secondary" onClick={onClose}>
          履歴を閉じる
        </button>
      </div>
      <ErrorBox error={error} />
      {!items && !error && <p>読み込み中…</p>}
      {items?.map((h) => (
        <details className="request-history" key={h.version}>
          <summary>
            v{h.version} · {h.note}{" "}
            <small>
              {dateText(h.created_at)} / {h.actor_name}
            </small>
          </summary>
          <RequestContent r={h.payload} />
        </details>
      ))}
    </section>
  );
}
function RequestContent({ r }: { r: any }) {
  return (
    <div className="request-content">
      <strong>{r.title}</strong>
      <p>{r.description || "内容は未入力です。"}</p>
      <dl>
        <dt>完了条件</dt>
        <dd>{r.acceptance || "未設定"}</dd>
        <dt>確認事項</dt>
        <dd>{r.questions || "なし"}</dd>
        <dt>対象範囲 / 状態</dt>
        <dd>
          {scopes[r.scope]} / {requestStates[r.status]}
        </dd>
      </dl>
      {r.agreement && (
        <div className="notice">
          合意記録：{r.agreement.note}
          <br />
          <small>
            {dateText(r.agreement.recorded_at)} · 記録者{" "}
            {r.agreement.recorded_by}
          </small>
        </div>
      )}
    </div>
  );
}

export function Projects({
  id,
  initialCreate = false,
  inPanel = false,
  customers,
  boot,
  notify,
  refresh,
}: Props) {
  const [list, setList] = useState<any[]>([]),
    [data, setData] = useState<any>(),
    [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  const [query, setQuery] = useState(""),
    [filter, setFilter] = useState(""),
    [editing, setEditing] = useState(initialCreate),
    [requestEdit, setRequestEdit] = useState<any>(null),
    [history, setHistory] = useState<number>(),
    [agreement, setAgreement] = useState<any>(null),
    [note, setNote] = useState(""),
    [busy, setBusy] = useState(false),
    [scopeFilter, setScopeFilter] = useState("");
  const [tab, setTab] = useState("documents");
  const tabs = [
    {
      id: "documents",
      label: "ダッシュボード",
      count: data
        ? data.quotes.length + data.orders.length + data.invoices.length
        : undefined,
    },
    { id: "requests", label: "要望のメモ", count: data?.requests.length },
    { id: "overview", label: "案件の概要" },
    {
      id: "attachments",
      label: "添付ファイル",
      count: data?.attachments?.length,
    },
  ];
  async function load() {
    if (id) setData(await api(`/projects/${id}`));
    else setList(await api("/projects"));
  }
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    api(id ? `/projects/${id}` : "/projects")
      .then((d) => {
        if (active) {
          if (id) setData(d);
          else setList(d);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [id, boot]);
  async function changed() {
    await load();
    setError("");
    setRequestEdit(null);
    setEditing(false);
    setAgreement(null);
    notify("案件の情報を保存しました");
  }
  async function agree(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await post(`/projects/${id}/requests/${agreement.id}/agree`, {
        lock_version: agreement.lock_version,
        comment: note,
      });
      await changed();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (loading) return <div className="loading">案件を読み込んでいます…</div>;
  if (id && !data)
    return <ErrorBox error={error || "案件が見つかりません。"} />;
  const visible = list.filter(
    (p) =>
      (!filter || p.status === filter) &&
      `${p.title} ${p.customer_name} ${p.purpose}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  return (
    <>
      {id && !inPanel && (
        <button className="back-link" onClick={() => navigate("/projects")}>
          <ArrowLeft size={16} />
          案件一覧へ
        </button>
      )}
      <div className="page-title">
        <div>
          <span className="eyebrow">
            {id ? `PROJECT / ${String(id).padStart(4, "0")}` : "PROJECTS"}
          </span>
          <h1>
            {data?.title ||
              (initialCreate ? "新しい案件をはじめましょう" : "案件ノート")}
          </h1>
          <p>
            {data
              ? `${data.customer_name} / 担当 ${data.owner_name}`
              : "相談から入金まで。仕事の全体像を、ひとつの案件に。"}
          </p>
        </div>
        <div className="project-actions">
          <a className="button subtle" href="#/manual/projects">
            使い方
          </a>
          {!initialCreate && (!id || data.editable) && (
            <button
              className="button primary"
              onClick={() =>
                id ? setEditing(!editing) : navigate("/projects/new")
              }
            >
              <Plus size={16} />
              {id ? "案件を編集" : "案件を作成"}
            </button>
          )}
        </div>
      </div>
      <ErrorBox error={error} />
      {editing && (
        <ProjectForm
          key={data?.lock_version || "new"}
          data={data}
          customers={customers}
          onCancel={() =>
            initialCreate ? navigate("/studio") : setEditing(false)
          }
          onSave={async (form) => {
            const p = id
              ? await put(`/projects/${id}`, form)
              : await post("/projects", form);
            if (id) await changed();
            else {
              setEditing(false);
              navigate(`/projects/${p.id}`);
            }
            await refresh();
          }}
        />
      )}
      {!id ? (
        initialCreate ? (
          <p className="studio-form-tip">
            取引先の登録がまだのときは、
            <a className="text-link" href="#/customers">
              取引先を登録
            </a>
            してからはじめましょう。
          </p>
        ) : (
          <>
            <div className="project-stats">
              <div>
                <small>案件</small>
                <strong>
                  {list.length}
                  <em>件</em>
                </strong>
              </div>
              <div>
                <small>進行中・検収待ち</small>
                <strong>
                  {
                    list.filter((p) =>
                      ["in_progress", "review"].includes(p.status),
                    ).length
                  }
                  <em>件</em>
                </strong>
              </div>
              <div>
                <small>未整理・確認事項あり</small>
                <strong>
                  {list.reduce((n, p) => n + p.unresolved_count, 0)}
                  <em>要望</em>
                </strong>
              </div>
            </div>
            <div className="project-filters">
              <label className="project-search">
                <Search size={17} />
                <input
                  aria-label="案件を検索"
                  placeholder="案件名・取引先・目的で検索"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </label>
              <select
                aria-label="案件の状態で絞り込み"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              >
                <option value="">すべての状態</option>
                {options(projectStates)}
              </select>
            </div>
            <div className="project-cards">
              {visible.map((p) => (
                <StudioProjectCard key={p.id} project={p} />
              ))}
            </div>
            {!visible.length && (
              <div className="panel project-empty">
                <BriefcaseBusiness size={32} />
                <h2>
                  {list.length
                    ? "条件に合う案件はありません"
                    : "最初の相談を、案件にしてみましょう"}
                </h2>
                <p>
                  取引先と目的を登録したら、要望を整理して見積につなげられます。
                </p>
              </div>
            )}
          </>
        )
      ) : (
        <>
          <ProjectProgress status={data.status} />
          <div
            className="studio-tabs"
            role="tablist"
            aria-label="案件ノートのページ"
          >
            {tabs.map((item, index) => (
              <button
                key={item.id}
                id={`project-tab-${item.id}`}
                role="tab"
                aria-selected={tab === item.id}
                aria-controls={`project-page-${item.id}`}
                tabIndex={tab === item.id ? 0 : -1}
                onClick={() => setTab(item.id)}
                onKeyDown={(event) => {
                  let next = index;
                  if (event.key === "ArrowRight")
                    next = (index + 1) % tabs.length;
                  else if (event.key === "ArrowLeft")
                    next = (index + tabs.length - 1) % tabs.length;
                  else if (event.key === "Home") next = 0;
                  else if (event.key === "End") next = tabs.length - 1;
                  else return;
                  event.preventDefault();
                  setTab(tabs[next].id);
                  document
                    .getElementById(`project-tab-${tabs[next].id}`)
                    ?.focus();
                }}
              >
                {item.label}
                {item.count !== undefined && <span>{item.count}</span>}
              </button>
            ))}
          </div>
          <div
            id="project-page-attachments"
            role="tabpanel"
            aria-labelledby="project-tab-attachments"
            hidden={tab !== "attachments"}
            tabIndex={0}
          >
            {data.attachment_limits && (
              <ProjectAttachments
                projectId={id}
                editable={data.editable}
                files={data.attachments}
                limits={data.attachment_limits}
                notify={notify}
                onAdd={(file) =>
                  setData((current: any) => ({
                    ...current,
                    attachments: [
                      file,
                      ...current.attachments.filter(
                        (item: Attachment) => item.id !== file.id,
                      ),
                    ].sort(
                      (a: Attachment, b: Attachment) =>
                        b.created_at.localeCompare(a.created_at) || b.id - a.id,
                    ),
                  }))
                }
                onRemove={(fileId) =>
                  setData((current: any) => ({
                    ...current,
                    attachments: current.attachments.filter(
                      (item: Attachment) => item.id !== fileId,
                    ),
                  }))
                }
              />
            )}
          </div>
          <div
            id="project-page-overview"
            role="tabpanel"
            aria-labelledby="project-tab-overview"
            hidden={tab !== "overview"}
            tabIndex={0}
          >
            <div className="project-stats">
              <div>
                <small>案件の状態</small>
                <strong className="text-stat">
                  {projectStates[data.status]}
                </strong>
              </div>
              <div>
                <small>受注額（税込）</small>
                <strong>{yen(data.ordered_total)}</strong>
              </div>
              <div>
                <small>請求済み・未入金</small>
                <strong>{yen(data.unpaid_total)}</strong>
              </div>
            </div>
            <section className="panel form-section">
              <div className="project-section-title">
                <h2>案件の概要</h2>
                {data.external_url && (
                  <a
                    className="text-link"
                    href={data.external_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    開発管理を開く ↗
                  </a>
                )}
              </div>
              <p className="pre-wrap">
                {data.purpose || "目的・背景はまだ登録されていません。"}
              </p>
              <p>
                目標納期：{data.due_on ? dateText(data.due_on) : "未設定"}
                　／　未整理・確認事項あり：{data.unresolved_count} 件
              </p>
            </section>
          </div>
          <section
            className="project-section"
            id="project-page-requests"
            role="tabpanel"
            aria-labelledby="project-tab-requests"
            hidden={tab !== "requests"}
            tabIndex={0}
          >
            <div className="project-section-title">
              <div>
                <h2>
                  要望を整理する <small>{data.requests.length} 件</small>
                </h2>
                <p>相談内容と、引き受ける範囲を分けて記録します。</p>
              </div>
              {data.editable && (
                <button
                  className="button primary"
                  onClick={() => {
                    setRequestEdit({});
                    setHistory(undefined);
                  }}
                >
                  <Plus size={16} />
                  要望を追加
                </button>
              )}
            </div>
            {requestEdit && (
              <RequestEditor
                key={requestEdit.id || "new"}
                projectId={id!}
                data={requestEdit.id ? requestEdit : undefined}
                onDone={changed}
                onCancel={() => setRequestEdit(null)}
              />
            )}
            {history && (
              <RequestHistory
                key={history}
                pid={id!}
                rid={history}
                onClose={() => setHistory(undefined)}
              />
            )}
            {agreement && (
              <form className="panel form-section" onSubmit={agree}>
                <h3>「{agreement.title}」の合意を記録</h3>
                <p>
                  顧客と確認した結果を手動で記録します。顧客への通知は行いません。
                </p>
                <Field label="合意相手・確認方法 *">
                  <textarea
                    required
                    maxLength={1000}
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder="例：9/19 田中様からメールで範囲と完了条件の確認済み"
                  />
                </Field>
                <div className="project-actions">
                  <button
                    type="button"
                    className="button secondary"
                    onClick={() => setAgreement(null)}
                  >
                    キャンセル
                  </button>
                  <button className="button primary" disabled={busy}>
                    合意を記録
                  </button>
                </div>
              </form>
            )}
            <div className="project-filters">
              <select
                aria-label="要望の対象範囲で絞り込み"
                value={scopeFilter}
                onChange={(e) => setScopeFilter(e.target.value)}
              >
                <option value="">すべての対象範囲</option>
                {options(scopes)}
              </select>
            </div>
            <div className="request-list">
              {data.requests
                .filter((r: any) => !scopeFilter || r.scope === scopeFilter)
                .map((r: any) => (
                  <article className="panel request-card" key={r.id}>
                    <div className="project-section-title">
                      <small>
                        REQ-{String(r.id).padStart(3, "0")} / v{r.lock_version}{" "}
                        · 優先度 {priorities[r.priority]}
                      </small>
                      <span className={`scope-tag scope-${r.scope}`}>
                        {scopes[r.scope]}
                      </span>
                    </div>
                    <RequestContent r={r} />
                    <div className="project-actions">
                      <button
                        className="button subtle"
                        onClick={() => {
                          setHistory(r.id);
                          setRequestEdit(null);
                        }}
                      >
                        変更履歴
                      </button>
                      {data.editable && (
                        <>
                          <button
                            className="button secondary"
                            onClick={() => {
                              setRequestEdit(r);
                              setHistory(undefined);
                            }}
                          >
                            要望を編集
                          </button>
                          {!r.agreement &&
                            ["included", "additional"].includes(r.scope) && (
                              <button
                                className="button secondary"
                                onClick={() => {
                                  setAgreement(r);
                                  setNote("");
                                }}
                              >
                                合意を記録
                              </button>
                            )}
                        </>
                      )}
                    </div>
                  </article>
                ))}
            </div>
            {!data.requests.length && (
              <div className="panel project-empty">
                <h3>まずは、顧客からの要望を書き留めましょう</h3>
                <p>まだ決まっていないことは「未整理」のまま登録できます。</p>
              </div>
            )}
          </section>
          <section
            className="panel form-section"
            id="project-page-documents"
            role="tabpanel"
            aria-labelledby="project-tab-documents"
            hidden={tab !== "documents"}
            tabIndex={0}
          >
            <div className="project-section-title">
              <div>
                <h2>案件のダッシュボード</h2>
                <p>見積から入金まで、この仕事の現在地を確認します。</p>
              </div>
              {data.editable && (
                <button
                  className="button primary"
                  onClick={() => navigate(`/quotes/new?project=${id}`)}
                >
                  <Plus size={16} />
                  案件の見積を作成
                </button>
              )}
            </div>
            <ProjectDashboard data={data} />
          </section>
        </>
      )}
    </>
  );
}

export function QuoteScopeEditor({
  form,
  setForm,
  existing,
}: {
  form: any;
  setForm: (f: any) => void;
  existing: boolean;
}) {
  const [projects, setProjects] = useState<any[]>([]),
    [project, setProject] = useState<any>(),
    [error, setError] = useState("");
  useEffect(() => {
    api("/projects")
      .then(setProjects)
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    let active = true;
    setProject(undefined);
    setError("");
    if (form.project_id)
      api(`/projects/${form.project_id}`)
        .then((p) => {
          if (active) setProject(p);
        })
        .catch((e) => {
          if (active) setError(e.message);
        });
    return () => {
      active = false;
    };
  }, [form.project_id]);
  function selectProject(value: string) {
    const p = projects.find((p) => p.id === Number(value));
    setForm((f: any) => ({
      ...f,
      project_id: p?.id || null,
      request_refs: [],
      customer_id: p?.customer_id || f.customer_id,
      title: f.title || p?.title || "",
    }));
  }
  function choose(r: any, checked: boolean) {
    setForm((f: any) => ({
      ...f,
      request_refs: checked
        ? [...f.request_refs, { request_id: r.id, version: r.lock_version }]
        : f.request_refs.filter((x: any) => x.request_id !== r.id),
    }));
  }
  return (
    <section className="panel form-section">
      <h2>案件と対象の要望</h2>
      <p>
        選択した版の内容を、この見積の記録として保存します。要望の詳細はPDFには載りません。
      </p>
      <ErrorBox error={error} />
      <Field label="関連する案件">
        <select
          value={form.project_id || ""}
          disabled={existing}
          onChange={(e) => selectProject(e.target.value)}
        >
          <option value="">案件に紐付けず作成</option>
          {projects
            .filter((p) => p.editable || p.id === form.project_id)
            .map((p) => (
              <option key={p.id} value={p.id}>
                {p.title}
              </option>
            ))}
        </select>
      </Field>
      {project && (
        <>
          <a className="text-link" href={`#/projects/${project.id}`}>
            案件を確認 →
          </a>
          <p>
            「今回の対象」「追加見積」の要望を選択できます。金額は明細に入力してください。
          </p>
          <div className="scope-checks">
            {project.requests
              .filter(
                (r: any) =>
                  ["included", "additional"].includes(r.scope) ||
                  form.request_refs.some((x: any) => x.request_id === r.id),
              )
              .map((r: any) => {
                const selected = form.request_refs.find(
                  (x: any) => x.request_id === r.id,
                );
                return (
                  <div className="scope-check" key={r.id}>
                    <label>
                      <input
                        type="checkbox"
                        checked={!!selected}
                        disabled={
                          !selected &&
                          !["included", "additional"].includes(r.scope)
                        }
                        onChange={(e) => choose(r, e.target.checked)}
                      />
                      <span>
                        {r.title}
                        <small>
                          {scopes[r.scope]} ·{" "}
                          {selected
                            ? `選択した版 v${selected.version}`
                            : `現在 v${r.lock_version}`}
                        </small>
                      </span>
                    </label>
                    {selected &&
                      selected.version !== r.lock_version &&
                      ["included", "additional"].includes(r.scope) && (
                        <button
                          type="button"
                          className="button subtle"
                          onClick={() =>
                            setForm((f: any) => ({
                              ...f,
                              request_refs: f.request_refs.map((x: any) =>
                                x.request_id === r.id
                                  ? {
                                      request_id: r.id,
                                      version: r.lock_version,
                                    }
                                  : x,
                              ),
                            }))
                          }
                        >
                          現在の版を取り込む
                        </button>
                      )}
                  </div>
                );
              })}
          </div>
          {!project.requests.length && (
            <p>案件に要望を登録すると、ここで選択できます。</p>
          )}
        </>
      )}
    </section>
  );
}

export function QuoteScope({ data }: { data: any }) {
  if (!data.project_id) return null;
  return (
    <section className="panel form-section">
      <div className="project-section-title">
        <h2>この見積の対象要望</h2>
        {data.business_editable && (
          <a className="text-link" href={`#/projects/${data.project_id}`}>
            案件を開く →
          </a>
        )}
      </div>
      <p>見積に取り込んだ時点の記録です。要望の詳細はPDFには載りません。</p>
      {data.payload.request_snapshots?.map((r: any) => (
        <details className="request-history" key={r.id}>
          <summary>
            REQ-{r.id} / v{r.lock_version} · {r.title}
          </summary>
          <RequestContent r={r} />
        </details>
      ))}
      {!data.payload.request_snapshots?.length && (
        <p>この見積に選択した要望はありません。</p>
      )}
    </section>
  );
}
