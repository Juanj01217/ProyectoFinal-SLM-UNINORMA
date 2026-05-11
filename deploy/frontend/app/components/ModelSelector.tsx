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
        className="appearance-none text-sm pr-8 pl-3 sm:pl-4 py-2 bg-white focus:outline-none focus:ring-2 disabled:opacity-50 cursor-pointer shadow-[0_2px_10px_rgba(0,0,0,0.12)]"
        style={{
          border: "1px solid #D1C9BE",
          borderRadius: 8,
          color: "#1A1A1A",
          fontWeight: 500,
          minWidth: 130,
          maxWidth: 200,
        }}
      >
        {models.map((m) => (
          <option key={m} value={m}>
            Modelo SLM: {m}
          </option>
        ))}
      </select>
      {/* Custom dropdown arrow */}
      <svg
        className="pointer-events-none absolute right-2.5"
        style={{ color: "#6B5E52" }}
        width="14"
        height="14"
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
