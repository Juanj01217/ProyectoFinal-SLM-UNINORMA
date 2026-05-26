"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import ChatMessage, { Message } from "./components/ChatMessage";
import ModelSelector from "./components/ModelSelector";
import StatusBar from "./components/StatusBar";
import Image from "next/image";
import {
  fetchStatus,
  fetchModels,
  loadModel,
  sendQueryStream,
  StatusResponse,
} from "./lib/api";

const EXAMPLE_QUESTIONS = [
  "¿Cuáles son los derechos de los egresados de Uninorte?",
  "¿Qué dice el reglamento sobre propiedad intelectual de los profesores?",
  "¿Cuál es la jornada laboral en el reglamento interno de trabajo?",
  "¿Qué establece la política de derechos humanos de la universidad?",
];

let messageIdCounter = 0;
function newId() {
  return `msg-${++messageIdCounter}`;
}

function UninorteLogo() {
  return (
    <div className="flex items-center gap-3">
      <Image
        src="/uninortelogo.png"
        alt="Universidad del Norte"
        width={160}
        height={42}
        className="h-10 w-auto object-contain"
      />
      <div className="h-6 w-px bg-white/30 hidden sm:block" />
      <div className="hidden sm:flex flex-col leading-none">
        <span className="text-white font-semibold tracking-[0.14em] text-sm uppercase">Uninorma</span>
        <span className="text-white/50 text-[10px] tracking-wider mt-0.5">Normatividad con IA</span>
      </div>
    </div>
  );
}

function GoldenTree() {
  return (
    <Image
      src="/uninorte_tree.svg"
      alt="Árbol Uninorte"
      width={120}
      height={120}
      className="w-16 h-16 sm:w-28 sm:h-28"
    />
  );
}

function BlobCard({ question, onClick }: Readonly<{ question: string; onClick: () => void }>) {
  return (
    <button
      onClick={onClick}
      className="group text-left w-full h-full focus:outline-none bg-transparent border-none pb-3.5 pr-3.5 cursor-pointer"
    >
      <div className="transition-all duration-300 ease-out group-hover:-translate-y-2 h-full relative">
        {/* Capa roja detrás */}
        <div className="absolute inset-0 bg-[#8B1111] rounded-[28px_14px_28px_14px] translate-x-1.5 translate-y-1.5 rotate-2 opacity-[0.95] z-0" />

        {/* Tarjeta */}
        <div className="relative bg-[#F7F5F2] rounded-[28px_14px_28px_14px] py-4 px-4 sm:py-5 sm:px-5 border border-[#e8e8e8] shadow-[0_8px_28px_rgba(0,0,0,0.18)] group-hover:shadow-[0_14px_40px_rgba(139,17,17,0.22)] transition-shadow duration-300 z-1 font-sans h-full box-border flex items-start gap-3">
          <div className="w-5 h-5 rounded-full bg-[#9D1B1E]/10 flex items-center justify-center shrink-0 mt-0.5">
            <span className="text-[#9D1B1E] text-xs font-bold leading-none">?</span>
          </div>
          <p className="text-[0.8rem] sm:text-[0.88rem] font-medium leading-[1.5] text-[#1A1A1A] m-0">
            {question}
          </p>
        </div>
      </div>
    </button>
  );
}

export default function HomePage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState("llama3.1:8b");
  const [modelLoading, setModelLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function init() {
      try {
        const s = await fetchStatus();
        setStatus(s);
        if (s.active_model) setSelectedModel(s.active_model);
      } catch {
        setStatus(null);
      } finally {
        setStatusLoading(false);
      }
      try {
        const m = await fetchModels();
        setModels(m.models);
        if (m.default) setSelectedModel(m.default);
      } catch {
        setModels(["qwen2.5:3b", "qwen2.5:1.5b", "llama3.2:3b", "phi3:mini"]);
      }
    }
    init();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleModelChange(model: string) {
    setSelectedModel(model);
    setModelLoading(true);
    try {
      await loadModel(model);
      const s = await fetchStatus();
      setStatus(s);
    } catch (e) {
      console.error(e);
    } finally {
      setModelLoading(false);
    }
  }

  async function handleSend(question?: string) {
    const text = (question ?? input).trim();
    if (!text || sending) return;

    setInput("");
    setSending(true);

    const userMsg: Message = { id: newId(), role: "user", content: text };
    const loadingMsg: Message = {
      id: newId(),
      role: "assistant",
      content: "",
      loading: true,
    };

    setMessages((prev) => [...prev, userMsg, loadingMsg]);

    try {
      const completedMsgs = messages.filter((m) => !m.loading && m.content);
      const historyToSend = completedMsgs.slice(-4).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      for await (const chunk of sendQueryStream(text, selectedModel, historyToSend)) {
        if (chunk.error) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === loadingMsg.id
                ? { ...m, content: `Error: ${chunk.error}`, loading: false }
                : m
            )
          );
          return;
        }
        if (chunk.token) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === loadingMsg.id
                ? { ...m, content: (m.content ?? "") + chunk.token, loading: false }
                : m
            )
          );
        }
        if (chunk.done) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === loadingMsg.id
                ? { ...m, sources: chunk.sources ?? [], loading: false }
                : m
            )
          );
          fetchStatus().then(setStatus).catch(() => {});
        }
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Error desconocido";
      setMessages((prev) =>
        prev.map((m) =>
          m.id === loadingMsg.id
            ? { ...m, content: `Error: ${msg}`, loading: false }
            : m
        )
      );
    } finally {
      setSending(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="flex flex-col h-screen bg-[url('/bg-Uninorma.png')] bg-cover bg-center bg-no-repeat">
      {/* Header */}
      <header className="shrink-0 relative z-10 bg-linear-to-b from-[#A31C1F] to-[#881518] shadow-[0_4px_28px_rgba(0,0,0,0.35)]">
        {/* Línea dorada de acento */}
        <div className="absolute bottom-0 inset-x-0 h-0.5 bg-linear-to-r from-transparent via-[#C9A227]/55 to-transparent" />

        {/* 3 columnas: [izq] [centro-logo] [der] */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
          {/* Izquierda — Benchmark */}
          <div className="flex items-center">
            <Link
              href="/benchmark"
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-white/80 hover:text-white hover:bg-white/10 transition-all duration-200"
            >
              <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              <span className="hidden sm:inline font-medium tracking-wide text-sm">Benchmark</span>
            </Link>
          </div>

          {/* Centro — Logo de marca */}
          <Link href="/" className="hover:opacity-90 transition-opacity" onClick={(e) => { e.preventDefault(); globalThis.location.href = "/"; }}>
            <UninorteLogo />
          </Link>

          {/* Derecha — Model Selector */}
          <div className="flex items-center justify-end">
            <ModelSelector
              models={models}
              selected={selectedModel}
              onSelect={handleModelChange}
              loading={modelLoading}
            />
          </div>
        </div>

        {(status || statusLoading) && (
          <div className="max-w-7xl mx-auto px-6 pb-1.5">
            <StatusBar status={status} loading={statusLoading} />
          </div>
        )}
      </header>

      {/* Chat / Empty state */}
      <main className="flex-1 overflow-y-auto relative z-1">
        {messages.length === 0 ? (
          /* Empty state — contenedor ancho propio, sin max-w-3xl */
          <div className="flex flex-col items-center justify-center min-h-full py-4 gap-4 sm:gap-5 px-4 w-full max-w-5xl mx-auto">
            <GoldenTree />
            <h1 className="font-bold text-[#1A1A1A] text-[clamp(1.1rem,2.4vw,1.8rem)] leading-[1.3] text-center">
              ¿Tienes alguna consulta sobre normatividad?
            </h1>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 w-full items-stretch">
              {EXAMPLE_QUESTIONS.map((q) => (
                <BlobCard key={q} question={q} onClick={() => handleSend(q)} />
              ))}
            </div>
          </div>
        ) : (
          /* Chat activo — contenedor estrecho estilo GPT */
          <div className="max-w-3xl mx-auto px-4 py-6">
            {messages.map((m) => (
              <ChatMessage key={m.id} message={m} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </main>

      {/* Input bar — flotante sin fondo */}
      <footer className="shrink-0 px-4 pb-4 pt-2 relative z-10 sm:mb-6">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end gap-2 bg-white rounded-2xl pl-4 pr-2 py-2 shadow-[0_8px_40px_rgba(0,0,0,0.14)] ring-1 ring-[#8B1518]/40 focus-within:ring-2 focus-within:ring-[#8B1518] focus-within:shadow-[0_8px_40px_rgba(139,21,24,0.18)] transition-all duration-300">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={sending}
              placeholder="Escribe tu pregunta sobre la normatividad de Uninorte..."
              rows={1}
              className="flex-1 resize-none text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none disabled:opacity-50 overflow-y-auto bg-transparent border-none min-h-9 max-h-28 leading-normal py-1.5"
            />

            {/* Botón con gradiente */}
            <button
              onClick={() => handleSend()}
              disabled={sending || !input.trim()}
              className="shrink-0 flex items-center justify-center w-9 h-9 rounded-xl bg-linear-to-br from-[#B52020] to-[#7A1315] shadow-[0_2px_8px_rgba(139,17,17,0.4)] hover:shadow-[0_4px_14px_rgba(139,17,17,0.5)] hover:scale-105 transition-all duration-200 disabled:opacity-35 disabled:scale-100 disabled:shadow-none border-none cursor-pointer"
            >
              {sending ? (
                <svg className="w-4 h-4 animate-spin text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
              ) : (
                <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                </svg>
              )}
            </button>
          </div>

        </div>
      </footer>
    </div>
  );
}
