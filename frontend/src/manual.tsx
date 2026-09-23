import { useMemo, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { BookOpen, Download, Search } from "lucide-react";
import index from "../../docs/manual/ja/index.json";

const sources = import.meta.glob("../../docs/manual/ja/*.md", {
  query: "?raw",
  import: "default",
  eager: true,
}) as Record<string, string>;
const articles = index.items
  .map((a) => ({ ...a, body: sources[`../../docs/manual/ja/${a.path}`] || "" }))
  .sort((a, b) => a.order - b.order);
export function Manual({ articleId }: { articleId: string }) {
  const [query, setQuery] = useState("");
  const selected = articles.find((a) => a.id === articleId);
  const matches = useMemo(
    () =>
      articles.filter((a) =>
        `${a.title} ${a.category} ${a.description} ${a.body}`
          .toLowerCase()
          .includes(query.trim().toLowerCase()),
      ),
    [query],
  );
  const headings =
    selected?.body
      .split("\n")
      .filter((l) => l.startsWith("## "))
      .map((l) => l.slice(3)) || [];
  return (
    <>
      <div className="page-title">
        <div>
          <span className="eyebrow">MITORI GUIDE</span>
          <h1>操作マニュアル</h1>
          <p>仕事の流れから探せる、見積管理システムの使い方。</p>
        </div>
        <BookOpen size={32} />
      </div>
      <div className="manual-layout">
        <aside className="panel manual-menu">
          <label className="project-search">
            <Search size={17} />
            <input
              aria-label="マニュアルを検索"
              placeholder="記事の本文も検索"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
          <small>{matches.length} 件の記事</small>
          {[...new Set(matches.map((a) => a.category))].map((category) => (
            <div key={category}>
              <h3>{category}</h3>
              {matches
                .filter((a) => a.category === category)
                .map((a) => (
                  <a
                    className={`manual-item ${a.id === articleId ? "selected" : ""}`}
                    href={`#/manual/${a.id}`}
                    key={a.id}
                  >
                    <strong>{a.title}</strong>
                    <span>{a.description}</span>
                  </a>
                ))}
            </div>
          ))}
          {!matches.length && (
            <p>該当する記事はありません。別の言葉で検索してください。</p>
          )}
        </aside>
        <article className="panel manual-article">
          {selected ? (
            <>
              <div className="project-section-title">
                <small>
                  {selected.category} / 更新 {index.updated_at}
                </small>
                <a
                  className="button subtle"
                  href={`/api/manual/${selected.id}/download`}
                  download={selected.path}
                >
                  <Download size={16} />
                  記事を保存
                </a>
              </div>
              {headings.length > 0 && (
                <nav aria-label="この記事の目次" className="manual-toc">
                  <strong>この記事の目次</strong>
                  {headings.map((title, i) => (
                    <button
                      key={i}
                      onClick={() =>
                        document
                          .getElementById(`manual-heading-${title}`)
                          ?.scrollIntoView({
                            behavior: "smooth",
                            block: "start",
                          })
                      }
                    >
                      {title}
                    </button>
                  ))}
                </nav>
              )}
              <div className="manual-markdown">
                <Markdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h2: ({ children }) => (
                      <h2 id={`manual-heading-${String(children)}`}>
                        {children}
                      </h2>
                    ),
                    a: ({ href, children }) => {
                      const linked = articles.find((a) => a.path === href);
                      return (
                        <a href={linked ? `#/manual/${linked.id}` : href}>
                          {children}
                        </a>
                      );
                    },
                  }}
                >
                  {selected.body}
                </Markdown>
              </div>
              <div className="manual-footer">
                {articles[articles.indexOf(selected) - 1] && (
                  <a
                    className="text-link"
                    href={`#/manual/${articles[articles.indexOf(selected) - 1].id}`}
                  >
                    ← 前の記事
                  </a>
                )}
                {articles[articles.indexOf(selected) + 1] && (
                  <a
                    className="text-link"
                    href={`#/manual/${articles[articles.indexOf(selected) + 1].id}`}
                  >
                    次の記事 →
                  </a>
                )}
              </div>
            </>
          ) : (
            <>
              <h2>記事が見つかりません</h2>
              <a className="text-link" href="#/manual/first-steps">
                はじめに戻る
              </a>
            </>
          )}
        </article>
      </div>
    </>
  );
}
