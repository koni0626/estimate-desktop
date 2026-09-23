import { useEffect, useRef, useState, type DragEvent } from "react";
import {
  Check,
  Download,
  File as PlainFileIcon,
  FileArchive,
  FileImage,
  FileText,
  FolderUp,
  Paperclip,
  RefreshCw,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import { api, dateText } from "./api";
import "./attachments.css";

export type Attachment = {
  id: number;
  filename: string;
  size_bytes: number;
  created_at: string;
  uploaded_by: string;
  download_url: string;
};
type Limits = {
  file_bytes: number;
  project_bytes: number;
  project_files: number;
};
type UploadEntry = {
  id: string;
  file: File;
  status: "queued" | "uploading" | "done" | "error";
  error?: string;
};

function sizeText(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024)
    return `${(bytes / 1024).toLocaleString("ja-JP", { maximumFractionDigits: 1 })} KB`;
  return `${(bytes / (1024 * 1024)).toLocaleString("ja-JP", { maximumFractionDigits: 1 })} MB`;
}
function FileIcon({ filename }: { filename: string }) {
  const ext = filename.split(".").at(-1)?.toLowerCase() || "";
  const Icon = ["png", "jpg", "jpeg", "gif", "webp", "svg", "heic"].includes(
    ext,
  )
    ? FileImage
    : ["zip", "7z", "gz", "tar"].includes(ext)
      ? FileArchive
      : [
            "pdf",
            "txt",
            "md",
            "doc",
            "docx",
            "csv",
            "xlsx",
            "xls",
            "pptx",
          ].includes(ext)
        ? FileText
        : PlainFileIcon;
  return <Icon size={22} />;
}
function isFileDrag(event: globalThis.DragEvent | DragEvent) {
  return Array.from(event.dataTransfer?.types || []).includes("Files");
}

export function ProjectAttachments({
  projectId,
  editable,
  files,
  limits,
  onAdd,
  onRemove,
  notify,
}: {
  projectId: number;
  editable: boolean;
  files: Attachment[];
  limits: Limits;
  onAdd: (file: Attachment) => void;
  onRemove: (id: number) => void;
  notify: (message: string) => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  const abort = useRef<AbortController | null>(null);
  const busy = useRef(false);
  const depth = useRef(0);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [queue, setQueue] = useState<UploadEntry[]>([]);
  const [notice, setNotice] = useState("");
  const [deleting, setDeleting] = useState<number>();
  const [confirmDelete, setConfirmDelete] = useState<Attachment>();
  const used = files.reduce((sum, file) => sum + file.size_bytes, 0);

  useEffect(() => {
    // Keep an accidental file drop outside the dropzone from navigating away.
    const preventFileNavigation = (event: globalThis.DragEvent) => {
      if (isFileDrag(event)) event.preventDefault();
    };
    window.addEventListener("dragover", preventFileNavigation);
    window.addEventListener("drop", preventFileNavigation);
    return () => {
      abort.current?.abort();
      window.removeEventListener("dragover", preventFileNavigation);
      window.removeEventListener("drop", preventFileNavigation);
    };
  }, []);

  async function upload(entries: UploadEntry[], retry = false) {
    if (busy.current || !editable || deleting !== undefined) return;
    const controller = new AbortController();
    abort.current = controller;
    busy.current = true;
    setUploading(true);
    setNotice("");
    const update = (id: string, patch: Partial<UploadEntry>) =>
      setQueue((old) =>
        old.map((entry) => (entry.id === id ? { ...entry, ...patch } : entry)),
      );
    if (retry)
      setQueue((old) =>
        old.map((entry) =>
          entries.some((e) => e.id === entry.id)
            ? { ...entry, status: "queued", error: undefined }
            : entry,
        ),
      );
    else setQueue(entries);
    let completed = 0;
    try {
      for (const entry of entries) {
        if (controller.signal.aborted) break;
        if (!entry.file.size || entry.file.size > limits.file_bytes) {
          update(entry.id, {
            status: "error",
            error: !entry.file.size
              ? "空のファイルは添付できません。"
              : `1ファイルは${sizeText(limits.file_bytes)}までです。`,
          });
          continue;
        }
        update(entry.id, { status: "uploading", error: undefined });
        try {
          const saved = await api<Attachment>(
            `/projects/${projectId}/attachments/${entry.id}`,
            {
              method: "PUT",
              body: entry.file,
              signal: controller.signal,
              headers: {
                "Content-Type": "application/octet-stream",
                "X-File-Name": encodeURIComponent(entry.file.name),
              },
            },
          );
          if (controller.signal.aborted) break;
          onAdd(saved);
          update(entry.id, { status: "done" });
          completed++;
        } catch (error) {
          if (controller.signal.aborted) break;
          update(entry.id, {
            status: "error",
            error:
              error instanceof TypeError
                ? "通信を確認し、もう一度添付してください。"
                : (error as Error).message,
          });
        }
      }
      if (!controller.signal.aborted && completed)
        notify(`${completed}件のファイルを添付しました`);
    } finally {
      busy.current = false;
      if (!controller.signal.aborted) setUploading(false);
    }
  }

  function selectFiles(selected: File[]) {
    if (!selected.length) return;
    if (busy.current) {
      setNotice("今の添付が終わってから、次のファイルを追加してください。");
      return;
    }
    if (selected.length > limits.project_files) {
      setNotice(`一度に選べるファイルは${limits.project_files}件までです。`);
      return;
    }
    void upload(
      selected.map((file) => ({
        id: crypto.randomUUID(),
        file,
        status: "queued",
      })),
    );
  }

  async function removeFile(file: Attachment) {
    setDeleting(file.id);
    setNotice("");
    try {
      await api(`/projects/${projectId}/attachments/${file.id}`, {
        method: "DELETE",
      });
      onRemove(file.id);
      setConfirmDelete(undefined);
      notify("添付ファイルを削除しました");
    } catch (error) {
      setNotice((error as Error).message);
    } finally {
      setDeleting(undefined);
    }
  }

  return (
    <section
      className="project-attachments"
      data-uploading={uploading || deleting !== undefined ? "true" : undefined}
      aria-label="案件の添付ファイル"
    >
      <div className="project-section-title">
        <div>
          <h2>
            <Paperclip size={19} /> 資料を、このノートに。
          </h2>
          <p>相談メモや画面イメージ、仕様書をまとめておけます。</p>
        </div>
        <span className="attachment-usage">
          {files.length} / {limits.project_files} 件 · {sizeText(used)} /{" "}
          {sizeText(limits.project_bytes)}
        </span>
      </div>
      {editable ? (
        <>
          <input
            ref={input}
            type="file"
            multiple
            className="attachment-file-input"
            aria-label="添付するファイルを選択"
            tabIndex={-1}
            disabled={uploading || deleting !== undefined}
            onChange={(event) => {
              selectFiles(Array.from(event.target.files || []));
              event.target.value = "";
            }}
          />
          <div
            className={`attachment-dropzone ${dragging ? "is-dragging" : ""} ${uploading ? "is-uploading" : ""}`}
            onDragEnter={(event) => {
              if (!isFileDrag(event)) return;
              event.preventDefault();
              depth.current++;
              if (!busy.current) setDragging(true);
            }}
            onDragLeave={(event) => {
              if (!isFileDrag(event)) return;
              event.preventDefault();
              depth.current = Math.max(0, depth.current - 1);
              if (!depth.current) setDragging(false);
            }}
            onDragOver={(event) => {
              if (!isFileDrag(event)) return;
              event.preventDefault();
              event.dataTransfer.dropEffect = busy.current ? "none" : "copy";
            }}
            onDrop={(event) => {
              event.preventDefault();
              depth.current = 0;
              setDragging(false);
              const items = Array.from(event.dataTransfer.items);
              if (
                items.some((item) => item.webkitGetAsEntry?.()?.isDirectory)
              ) {
                setNotice("フォルダーはZIPにまとめてから添付してください。");
                return;
              }
              selectFiles(Array.from(event.dataTransfer.files));
            }}
          >
            <span className="attachment-drop-icon">
              <FolderUp size={30} />
            </span>
            <strong>
              {uploading
                ? "ノートにファイルを添付しています…"
                : dragging
                  ? "ここにドロップして添付"
                  : "ファイルをここにドラッグ＆ドロップ"}
            </strong>
            <p>PDF・画像・Excel・ZIPなど、複数まとめて添付できます。</p>
            <button
              className="button secondary"
              disabled={uploading || deleting !== undefined}
              onClick={() => input.current?.click()}
            >
              <Upload size={16} /> ファイルを選ぶ
            </button>
            <small>
              1ファイル {sizeText(limits.file_bytes)} まで ·
              同じ名前でも別の資料として保存
            </small>
          </div>
        </>
      ) : (
        <p className="notice">
          この案件は閲覧のみ可能です。添付された資料をダウンロードできます。
        </p>
      )}
      {notice && (
        <div className="error-box attachment-notice" role="alert">
          {notice}
          <button
            className="icon-button"
            aria-label="添付ファイルのメッセージを閉じる"
            onClick={() => setNotice("")}
          >
            <X size={16} />
          </button>
        </div>
      )}
      {queue.length > 0 && (
        <div
          className="attachment-queue"
          aria-label="添付の進行状況"
          aria-live="polite"
        >
          <div className="attachment-queue-heading">
            <strong>
              {uploading ? "添付中" : "添付の結果"} ·{" "}
              {queue.filter((q) => q.status === "done").length} / {queue.length}{" "}
              件完了
            </strong>
            {!uploading && (
              <div>
                {queue.some((q) => q.status === "error") && (
                  <button
                    className="button subtle"
                    onClick={() =>
                      void upload(
                        queue.filter((q) => q.status === "error"),
                        true,
                      )
                    }
                    disabled={deleting !== undefined}
                  >
                    <RefreshCw size={14} /> 失敗したファイルを再試行
                  </button>
                )}
                <button
                  className="icon-button"
                  aria-label="添付の結果を閉じる"
                  onClick={() => setQueue([])}
                >
                  <X size={16} />
                </button>
              </div>
            )}
          </div>
          {queue.map((entry) => (
            <div
              className={`attachment-queue-row ${entry.status}`}
              key={entry.id}
            >
              {entry.status === "done" ? (
                <Check size={17} />
              ) : entry.status === "uploading" ? (
                <RefreshCw size={17} className="attachment-spinner" />
              ) : entry.status === "error" ? (
                <X size={17} />
              ) : (
                <Upload size={17} />
              )}
              <span>
                <strong>{entry.file.name}</strong>
                {entry.error && <small>{entry.error}</small>}
              </span>
              <small>
                {
                  {
                    queued: "待機中",
                    uploading: "添付中…",
                    done: "保存済み",
                    error: "添付できませんでした",
                  }[entry.status]
                }
              </small>
            </div>
          ))}
        </div>
      )}
      <div className="attachment-list-heading">
        <h3>
          保存した資料 <span>{files.length}</span>
        </h3>
        <small>追加した日時が新しい順</small>
      </div>
      {!files.length ? (
        <div className="attachment-empty">
          <Paperclip size={25} />
          <p>資料を添えると、相談の内容が伝わりやすくなります。</p>
          <small>添付したファイルはここに並びます。</small>
        </div>
      ) : (
        <ul className="attachment-list">
          {files.map((file) => (
            <li key={file.id}>
              <div className="attachment-file-row">
                <span className="attachment-file-icon">
                  <FileIcon filename={file.filename} />
                </span>
                <div className="attachment-file-info">
                  <strong>{file.filename}</strong>
                  <small>
                    {sizeText(file.size_bytes)} · {dateText(file.created_at)} ·{" "}
                    {file.uploaded_by}
                  </small>
                </div>
                <div className="attachment-file-actions">
                  <a
                    className="button secondary"
                    href={file.download_url}
                    download={file.filename}
                    aria-label={`${file.filename}をダウンロード`}
                  >
                    <Download size={16} />
                    <span>保存</span>
                  </a>
                  {editable && (
                    <button
                      className="icon-button"
                      aria-label={`${file.filename}を削除`}
                      disabled={uploading || deleting !== undefined}
                      onClick={() => setConfirmDelete(file)}
                    >
                      <Trash2 size={17} />
                    </button>
                  )}
                </div>
              </div>
              {confirmDelete?.id === file.id && (
                <div
                  className="attachment-delete-confirm"
                  role="group"
                  aria-label={`${file.filename}の削除確認`}
                >
                  <p>
                    この添付ファイルを削除しますか？ 削除後は元に戻せません。
                  </p>
                  <div className="project-actions">
                    <button
                      className="button secondary"
                      disabled={deleting !== undefined}
                      onClick={() => setConfirmDelete(undefined)}
                    >
                      残す
                    </button>
                    <button
                      className="button primary"
                      disabled={deleting !== undefined}
                      onClick={() => void removeFile(file)}
                    >
                      {deleting === file.id ? "削除中…" : "削除する"}
                    </button>
                  </div>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
      <p className="attachment-footer">
        案件の閲覧権限があるメンバーと共有されます。見積書や請求書のPDFには含まれません。
      </p>
    </section>
  );
}
