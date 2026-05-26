"use client";

import { useEffect, useRef, useState } from "react";

interface Props {
  readonly models: string[];
  readonly selected: string;
  readonly onSelect: (model: string) => void;
  readonly loading: boolean;
}

export default function ModelSelector({ models, selected, onSelect, loading }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleOutsideClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => !loading && setOpen((o) => !o)}
        disabled={loading}
        className="flex items-center gap-2 text-sm font-medium tracking-wide pl-3 pr-2.5 py-1.5 bg-white/15 text-white border border-white/25 rounded-lg hover:bg-white/20 transition-colors duration-150 disabled:opacity-50 cursor-pointer select-none"
      >
        <span className="max-w-32 truncate text-xs sm:text-sm">{selected}</span>
        <svg
          className={`w-3 h-3 text-white/60 shrink-0 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
          viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
          strokeLinecap="round" strokeLinejoin="round"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 min-w-44 bg-[#7D1315] border border-white/15 rounded-xl shadow-[0_12px_40px_rgba(0,0,0,0.55)] overflow-hidden z-50">
          {/* Gold accent line */}
          <div className="h-px bg-linear-to-r from-transparent via-[#C9A227]/40 to-transparent" />
          <div className="py-1">
            {models.map((m) => {
              const isSelected = m === selected;
              return (
                <button
                  key={m}
                  onClick={() => { onSelect(m); setOpen(false); }}
                  className={`w-full text-left flex items-center gap-2.5 px-4 py-2.5 text-sm transition-colors duration-100 cursor-pointer ${
                    isSelected
                      ? "bg-white/15 text-white font-semibold"
                      : "text-white/70 hover:bg-white/10 hover:text-white"
                  }`}
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full shrink-0 transition-colors ${
                      isSelected ? "bg-[#C9A227]" : "bg-white/20"
                    }`}
                  />
                  {m}
                </button>
              );
            })}
          </div>
          <div className="h-px bg-linear-to-r from-transparent via-white/8 to-transparent" />
        </div>
      )}
    </div>
  );
}
