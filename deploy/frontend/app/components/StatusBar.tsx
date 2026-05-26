"use client";

import { StatusResponse } from "../lib/api";

interface Props {
  status: StatusResponse | null;
  loading: boolean;
}

export default function StatusBar({ status, loading }: Props) {
  if (loading) {
    return (
      <div className="hidden lg:flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-white/30 animate-pulse" />
        <span className="text-[11px] text-white/40 tracking-wide">Verificando...</span>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="hidden lg:flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
        <span className="text-[11px] text-red-300 tracking-wide">Sin conexión</span>
      </div>
    );
  }

  return (
    <div className="hidden lg:flex items-center gap-2 text-[11px] tracking-wide">
      <span className="flex items-center gap-1">
        <span
          className={`w-1.5 h-1.5 rounded-full ${
            status.ollama_running ? "bg-green-400 shadow-[0_0_5px_#4ade80]" : "bg-red-400"
          }`}
        />
        <span className={status.ollama_running ? "text-green-300" : "text-red-300"}>
          {status.ollama_running ? "Ollama activo" : "Ollama inactivo"}
        </span>
      </span>
      <span className="text-white/20">·</span>
      <span className="flex items-center gap-1">
        <span
          className={`w-1.5 h-1.5 rounded-full ${
            status.vector_store_ready ? "bg-green-400 shadow-[0_0_5px_#4ade80]" : "bg-yellow-400"
          }`}
        />
        <span className={status.vector_store_ready ? "text-green-300" : "text-yellow-300"}>
          {status.vector_store_ready ? "Base lista" : "Cargando..."}
        </span>
      </span>
    </div>
  );
}
