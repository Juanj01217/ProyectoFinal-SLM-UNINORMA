import { Source } from "../lib/api";

interface Props {
  sources: Source[];
}

function cleanFilename(raw: string): string {
  try {
    return decodeURIComponent(raw.split("/").pop() || raw).replace(/\.pdf$/i, "");
  } catch {
    return raw;
  }
}

export default function SourceCard({ sources }: Readonly<Props>) {
  if (!sources.length) return null;

  // Group by document, collect unique pages
  const grouped: Record<string, string[]> = {};
  for (const s of sources) {
    const key = cleanFilename(s.title || s.source);
    if (!grouped[key]) grouped[key] = [];
    if (s.page && !grouped[key].includes(s.page)) {
      grouped[key].push(s.page);
    }
  }

  const entries = Object.entries(grouped);
  const docCount = entries.length;

  return (
    <div className="mt-4 pt-3 border-t border-[#9D1B1E]/12">
      <p className="flex items-center gap-1.5 text-[10px] font-semibold text-[#9D1B1E]/50 uppercase tracking-widest mb-2.5">
        <svg className="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round"
            d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
        {docCount} {docCount === 1 ? "fuente consultada" : "fuentes consultadas"}
      </p>

      <div className="flex flex-col gap-1.5">
        {entries.map(([doc, pages]) => {
          const sortedPages = pages.slice().sort((a, b) => Number(a) - Number(b));
          return (
            <div
              key={doc}
              className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-[#9D1B1E]/6 border border-[#9D1B1E]/10 text-xs"
            >
              {/* Doc icon */}
              <svg className="w-3.5 h-3.5 text-[#9D1B1E]/45 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>

              {/* Document name */}
              <span className="font-medium text-[#2D1014] flex-1 min-w-0 truncate">{doc}</span>

              {/* Page badges */}
              {sortedPages.length > 0 && (
                <div className="flex items-center gap-1 shrink-0">
                  {sortedPages.map((p) => (
                    <span
                      key={p}
                      className="px-1.5 py-0.5 rounded bg-[#9D1B1E]/10 text-[#9D1B1E] font-mono font-medium text-[10px] leading-none"
                    >
                      p.{p}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
