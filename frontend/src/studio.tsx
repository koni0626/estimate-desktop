import { useEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import Decimal from "decimal.js";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  CheckCheck,
  Coffee,
  FileText,
  Flower2,
  FolderOpen,
  NotebookPen,
  Plus,
  Sprout,
  Wallet,
  X,
} from "lucide-react";
import { api, dateText, navigate, yen, type QuoteSummary } from "./api";
import { StudioScene } from "./studio-scene";

export const projectStates: Record<string, string> = {
  consulting: "相談中",
  estimating: "見積中",
  in_progress: "進行中",
  review: "検収待ち",
  completed: "完了",
  on_hold: "保留",
  cancelled: "中止",
};
type Project = {
  id: number;
  title: string;
  customer_name: string;
  purpose: string;
  status: string;
  due_on: string | null;
  owner_name: string;
  request_count: number;
  unresolved_count: number;
};
type Invoice = { id: number; status: string; total: string; overdue: boolean };
type Props = {
  boot: any;
  quotes: QuoteSummary[];
  approvals: any[];
};
const phases = [
  "consulting",
  "estimating",
  "in_progress",
  "review",
  "completed",
];

export function ProjectProgress({ status }: { status: string }) {
  const position = phases.indexOf(status);
  return (
    <div
      className="studio-progress"
      aria-label={`案件の状態：${projectStates[status]}`}
    >
      <div aria-hidden="true">
        {phases.map((p, i) => (
          <span key={p} className={position >= i ? "filled" : ""} />
        ))}
      </div>
      <small>{projectStates[status]}</small>
    </div>
  );
}

export function StudioProjectCard({ project: p }: { project: Project }) {
  return (
    <button
      className={`studio-job studio-job-${p.status}`}
      onClick={() => navigate(`/projects/${p.id}`)}
    >
      <div className="studio-job-top">
        <span className="studio-job-icon">
          <FolderOpen size={23} />
        </span>
        <span className="studio-job-code">
          PROJECT {String(p.id).padStart(3, "0")}
        </span>
        <ArrowUpRight size={17} />
      </div>
      <small className="studio-job-client">{p.customer_name}</small>
      <h3>{p.title}</h3>
      <p>{p.purpose || "要望のメモから、少しずつ仕事をかたちに。"}</p>
      <ProjectProgress status={p.status} />
      <div className="studio-job-foot">
        <span>
          <NotebookPen size={14} /> 要望 {p.request_count} 件
        </span>
        <span>
          {p.unresolved_count
            ? `確認 ${p.unresolved_count} 件`
            : "確認事項なし"}
        </span>
      </div>
      <small className="studio-job-due">
        目標納期 {p.due_on ? dateText(p.due_on) : "未設定"} · {p.owner_name}
      </small>
    </button>
  );
}

export function StudioHome({ boot, quotes, approvals }: Props) {
  const [data, setData] = useState<{
    projects: Project[];
    invoices: Invoice[];
  }>();
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setError("");
    setData(undefined);
    Promise.all([api<Project[]>("/projects"), api<Invoice[]>("/invoices")])
      .then(([projects, invoices]) => {
        if (active) setData({ projects, invoices });
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [boot, retry]);
  const projects = data?.projects || [];
  const activeProjects = projects.filter(
    (p) => !["completed", "cancelled", "on_hold"].includes(p.status),
  );
  const unpaid = (data?.invoices || []).filter((i) => i.status === "issued");
  const totalUnpaid = unpaid
    .reduce((sum, i) => sum.plus(i.total), new Decimal(0))
    .toFixed(0);
  const unresolved = projects.filter((p) => p.unresolved_count > 0);
  const drafts = quotes.filter((q) => ["draft", "returned"].includes(q.status));
  const tasks = [
    {
      count: approvals.length,
      label: "あなたの承認を待つ見積",
      description: "内容を確認して、次の人へ。",
      to: "/approvals",
      icon: CheckCheck,
    },
    {
      count: unresolved.length,
      label: "確認したい要望のある案件",
      description: "未整理の範囲や確認事項をひとつずつ。",
      to:
        unresolved.length === 1 ? `/projects/${unresolved[0].id}` : "/projects",
      icon: NotebookPen,
    },
    {
      count: drafts.length,
      label: "作成途中・差戻しの見積",
      description: "書きかけの続きを、ここから。",
      to:
        drafts.length === 1 ? `/revisions/${drafts[0].revision_id}` : "/quotes",
      icon: FileText,
    },
    {
      count: unpaid.length,
      label: "入金を確認する請求書",
      description: "実際の入金を確認してから記録します。",
      to: "/invoices",
      icon: Wallet,
    },
  ];
  const taskCount = tasks.reduce((n, t) => n + t.count, 0);
  const today = new Date().toLocaleDateString("ja-JP", {
    month: "long",
    day: "numeric",
    weekday: "short",
  });
  return (
    <div className="studio-home">
      <div className="page-title studio-heading">
        <div>
          <span className="eyebrow">MY LITTLE STUDIO</span>
          <h1>
            <span>おかえりなさい、</span>
            <span className="studio-greeting-name">
              {boot.me.name}さん <Flower2 className="studio-flower" size={25} />
            </span>
          </h1>
          <p>相談も、ものづくりも。あなたの仕事を育てる場所。</p>
        </div>
        <button
          className="button primary"
          onClick={() => navigate("/projects/new")}
        >
          <Plus size={17} /> 新しい案件をはじめる
        </button>
      </div>
      <section className="studio-hero" aria-label="あなたのアトリエ">
        <div className="studio-hero-copy">
          <span className="studio-today">
            <Coffee size={15} /> {today} のアトリエ
          </span>
          <h2>
            今日も、ひとつずつ。
            <br />
            いい仕事を、ここから。
          </h2>
          <p>
            お客さまの「こうしたい」をメモして、
            <br />
            見積から入金まで、つないでいきましょう。
          </p>
          <button
            className="button primary"
            onClick={() => navigate("/projects")}
          >
            <FolderOpen size={17} /> 案件ノートをひらく <ArrowRight size={16} />
          </button>
          <small>
            <Sprout size={13} /> 自分のペースで、大丈夫。
          </small>
        </div>
        <StudioScene
          onDesk={() => navigate("/projects")}
          onPost={() =>
            document.getElementById("studio-next")?.scrollIntoView({
              behavior: window.matchMedia("(prefers-reduced-motion: reduce)")
                .matches
                ? "instant"
                : "smooth",
              block: "start",
            })
          }
          unread={data ? taskCount : null}
        />
      </section>
      {error ? (
        <div className="error-box studio-load-error" role="alert">
          <p>アトリエの情報を読み込めませんでした。{error}</p>
          <button
            className="button secondary"
            onClick={() => setRetry((n) => n + 1)}
          >
            再試行
          </button>
        </div>
      ) : !data ? (
        <div className="loading" role="status">
          仕事のノートを準備しています…
        </div>
      ) : (
        <>
          <div className="studio-resources" aria-label="仕事の状況">
            <button onClick={() => navigate("/projects")}>
              <span className="studio-resource-icon">
                <FolderOpen size={23} />
              </span>
              <span>
                <small>動いている案件</small>
                <strong>
                  {activeProjects.length}
                  <em>件</em>
                </strong>
                <small>相談中から検収待ちまで</small>
              </span>
            </button>
            <button onClick={() => navigate("/quotes")}>
              <span className="studio-resource-icon peach">
                <FileText size={23} />
              </span>
              <span>
                <small>作成途中の見積</small>
                <strong>
                  {drafts.length}
                  <em>件</em>
                </strong>
                <small>下書き・差戻し</small>
              </span>
            </button>
            <button onClick={() => navigate("/invoices")}>
              <span className="studio-resource-icon gold">
                <Wallet size={23} />
              </span>
              <span>
                <small>請求済み・未入金（税込）</small>
                <strong>{yen(totalUnpaid)}</strong>
                <small>
                  {unpaid.length} 件
                  {unpaid.some((i) => i.overdue)
                    ? ` · うち期限超過 ${unpaid.filter((i) => i.overdue).length} 件`
                    : " · 下書き・無効分を除く"}
                </small>
              </span>
            </button>
          </div>
          <div className="studio-work-grid">
            <section className="studio-projects-section">
              <div className="studio-section-heading">
                <div>
                  <span className="eyebrow">ON MY DESK</span>
                  <h2>
                    最近の案件ノート <span>{projects.length}</span>
                  </h2>
                </div>
                <a href="#/projects">
                  すべて見る <ArrowRight size={14} />
                </a>
              </div>
              <div className="studio-jobs">
                {projects.slice(0, 4).map((p) => (
                  <StudioProjectCard key={p.id} project={p} />
                ))}
                <button
                  className="studio-new-job"
                  onClick={() => navigate("/projects/new")}
                >
                  <span>
                    <Plus size={24} />
                  </span>
                  <strong>次の相談を、ノートに。</strong>
                  <small>新しい案件をはじめる</small>
                </button>
              </div>
            </section>
            <section className="studio-next" id="studio-next" tabIndex={-1}>
              <span className="studio-note-tape" aria-hidden="true" />
              <span className="eyebrow">A SMALL NEXT STEP</span>
              <h2>
                <NotebookPen size={20} /> 次の一歩メモ
              </h2>
              <p>気になるところから、進めましょう。</p>
              <div className="studio-task-list">
                {tasks.map((t) => (
                  <button
                    key={t.to + t.label}
                    onClick={() => navigate(t.to)}
                    className={t.count ? "" : "is-clear"}
                  >
                    <span className="studio-task-icon">
                      <t.icon size={18} />
                    </span>
                    <span>
                      <strong>{t.label}</strong>
                      <small>
                        {t.count
                          ? t.description
                          : "今のところ、確認待ちはありません。"}
                      </small>
                    </span>
                    <b>{t.count}</b>
                  </button>
                ))}
              </div>
              <a className="studio-guide" href="#/manual/first-steps">
                <BookOpen size={18} />
                <span>
                  使い方を知りたいときは<small>アトリエのガイドをひらく</small>
                </span>
                <ArrowUpRight size={17} />
              </a>
            </section>
          </div>
          <section className="studio-drawers" aria-label="書類の引き出し">
            <div>
              <span className="eyebrow">PAPERWORK</span>
              <h2>書類の引き出し</h2>
            </div>
            {[
              { label: "見積書", to: "quotes", note: "提案を、かたちに" },
              { label: "受注管理", to: "orders", note: "約束した仕事を確認" },
              { label: "請求・入金", to: "invoices", note: "仕事の締めくくり" },
            ].map((d) => (
              <a href={`#/${d.to}`} key={d.to}>
                <FileText size={22} />
                <span>
                  <strong>{d.label}</strong>
                  <small>{d.note}</small>
                </span>
                <ArrowUpRight size={17} />
              </a>
            ))}
          </section>
          <p className="studio-scope-note">
            表示している件数・金額は、あなたが閲覧できるデータの集計です。
          </p>
        </>
      )}
    </div>
  );
}

export function StudioPanel({
  children,
  onClose,
  title,
}: {
  children: ReactNode;
  onClose: () => void;
  title: string;
}) {
  const panel = useRef<HTMLDivElement>(null);
  const [discardPrompt, setDiscardPrompt] = useState(false);
  const [uploadNotice, setUploadNotice] = useState(false);
  const close = useRef(onClose);
  close.current = onClose;
  const requestClose = () => {
    if (panel.current?.querySelector('[data-uploading="true"]')) {
      setUploadNotice(true);
      return;
    }
    setUploadNotice(false);
    if (discardPrompt) {
      setDiscardPrompt(false);
      return;
    }
    if (panel.current?.querySelector('form[data-studio-dirty="true"]')) {
      setDiscardPrompt(true);
      return;
    }
    close.current();
  };
  const closeHandler = useRef(requestClose);
  closeHandler.current = requestClose;
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const root = document.getElementById("root")!;
    const wasInert = root.inert;
    const overflow = document.body.style.overflow;
    root.inert = true;
    document.body.style.overflow = "hidden";
    panel.current
      ?.querySelector<HTMLButtonElement>(".studio-window-close")
      ?.focus();
    const keyboard = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeHandler.current();
      }
      if (event.key !== "Tab") return;
      const elements = Array.from(
        panel.current?.querySelectorAll<HTMLElement>(
          'button:not(:disabled), a[href], input:not(:disabled), textarea:not(:disabled), select:not(:disabled), [tabindex="0"]',
        ) || [],
      ).filter(
        (el) =>
          el.getClientRects().length > 0 &&
          !el.closest("[inert]") &&
          el.tabIndex >= 0,
      );
      const first = elements[0],
        last = elements.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    };
    document.addEventListener("keydown", keyboard);
    return () => {
      root.inert = wasInert;
      document.body.style.overflow = overflow;
      document.removeEventListener("keydown", keyboard);
      if (previous?.isConnected) previous.focus();
    };
  }, []);
  useEffect(() => {
    panel.current
      ?.querySelector<HTMLButtonElement>(
        discardPrompt ? ".studio-continue" : ".studio-window-close",
      )
      ?.focus();
  }, [discardPrompt]);
  return createPortal(
    <div className="studio-backdrop">
      <div
        className="studio-window"
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby="studio-window-title"
        onChangeCapture={(event) => {
          const form = (event.target as HTMLElement).closest("form");
          if (form) form.dataset.studioDirty = "true";
        }}
      >
        <header className="studio-window-header" inert={discardPrompt}>
          <span>
            <FolderOpen size={19} />
            <strong id="studio-window-title">{title}</strong>
          </span>
          <span className="studio-window-hint">
            ひとつの仕事を、ひとつのノートに
          </span>
          <button
            className="studio-window-close icon-button"
            aria-label="案件ノートを閉じる"
            onClick={requestClose}
          >
            <X size={21} />
          </button>
        </header>
        {uploadNotice && (
          <p className="studio-upload-notice" role="status">
            添付処理の完了を待って、もう一度閉じてください。
          </p>
        )}
        <div className="studio-window-body" inert={discardPrompt}>
          {children}
        </div>
        {discardPrompt && (
          <div className="studio-discard-backdrop">
            <div
              className="studio-discard"
              role="alertdialog"
              aria-modal="true"
              aria-labelledby="studio-discard-title"
              aria-describedby="studio-discard-description"
            >
              <NotebookPen size={26} />
              <h2 id="studio-discard-title">書きかけの内容があります</h2>
              <p id="studio-discard-description">
                保存せずに閉じると、入力中の内容は失われます。
              </p>
              <div className="project-actions">
                <button
                  className="button primary studio-continue"
                  onClick={() => setDiscardPrompt(false)}
                >
                  編集を続ける
                </button>
                <button
                  className="button secondary"
                  onClick={() => close.current()}
                >
                  保存せず閉じる
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>,
    document.body,
  );
}
