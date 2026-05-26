"use client";

interface Props {
  readonly models: string[];
  readonly selected: string;
  readonly onSelect: (model: string) => void;
  readonly loading: boolean;
}

export default function ModelSelector({ models, selected, onSelect, loading }: Props) {
  return (
    <div className="relative flex items-center">
      <select
        id="model-select"
        value={selected}
        onChange={(e) => onSelect(e.target.value)}
        disabled={loading}
        className="appearance-none text-xs sm:text-sm font-medium tracking-wide pr-6 pl-3 py-1.5 bg-white/15 text-white border border-white/25 rounded-lg focus:outline-none focus:ring-1 focus:ring-white/40 disabled:opacity-50 cursor-pointer hover:bg-white/20 transition-colors duration-150 max-w-40 sm:max-w-50 truncate"
      >
        {models.map((m) => (
          <option key={m} value={m} className="bg-[#8B1518] text-white">
            {m}
          </option>
        ))}
      </select>
      <svg
        className="pointer-events-none absolute right-2 text-white/70"
        width="12"
        height="12"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <polyline points="6 9 12 15 18 9" />
      </svg>
    </div>
  );
}
