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
    <div className="flex items-center">
      <Image
        src="/uninortelogo.png"
        alt="Universidad del Norte"
        width={200}
        height={52}
        className="h-13 w-auto object-contain"
      />
      <span className="text-xl text-white tracking-[0.01em]">
        Uninorma
      </span>
    </div>
  );
}

function GoldenTree() {
  return (
    <Image src="/uninorte_tree.svg" alt="Árbol Uninorte" width={200} height={200} />
  );
}

function BlobCard({ question, onClick }: Readonly<{ question: string; onClick: () => void }>) {
  return (
    <button
      onClick={onClick}
      className="group text-left w-full h-full focus:outline-none bg-transparent border-none pb-3.5 pr-3.5 cursor-pointer"
    >
      <div className="transition-transform duration-300 ease-out group-hover:-translate-y-2 h-full relative">
        {/* Capa roja detrás */}
        <div className="absolute inset-0 bg-[#8B1111] rounded-[48px_24px_48px_24px] translate-x-1.5 translate-y-1.5 rotate-2 opacity-[0.95] z-0" />

        {/* Tarjeta */}
        <div className="relative bg-[#F7F5F2] rounded-[48px_24px_48px_24px] py-8 px-7 border border-[#e8e8e8] shadow-[0_12px_40px_rgba(0,0,0,0.22)] z-1 font-sans h-full box-border flex items-start gap-3">
          <div className="w-2.5 h-2.5 bg-[#8B1111] rounded-full shrink-0 mt-1" />
          <p className="text-[0.92rem] font-medium leading-[1.55] text-[#1A1A1A] m-0">
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
    <div className="flex flex-col h-screen bg-[#F5EFE4] bg-[url('/figurabg.svg')] bg-repeat bg-size-[300px_300px] bg-center">
      {/* Header */}
      <header className="shrink-0 bg-[#9D1B1E]  relative z-10 shadow-[0_4px_20px_rgba(0,0,0,0.25)]">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 py-3 sm:py-4 flex items-center justify-between gap-2 sm:gap-3">
          <Link href="/" className="hover:opacity-90 transition-opacity" onClick={(e) => { e.preventDefault(); globalThis.location.href = "/"; }}>
            <UninorteLogo />
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href="/benchmark"
              className="flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg text-sm text-white transition-opacity hover:opacity-90 bg-[#1A1A2E] shadow-[0_2px_10px_rgba(0,0,0,0.3)]"
            >
              <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.8}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              <span className="hidden sm:inline">Benchmark</span>
            </Link>
            <ModelSelector
              models={models}
              selected={selectedModel}
              onSelect={handleModelChange}
              loading={modelLoading}
            />
          </div>
        </div>
        {(status || statusLoading) && (
          <div className="max-w-7xl mx-auto px-6 pb-2">
            <StatusBar status={status} loading={statusLoading} />
          </div>
        )}
      </header>

      {/* Chat / Empty state */}
      <main className="flex-1 overflow-y-auto relative z-1">
        <div className="max-w-6xl mx-auto px-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center min-h-[calc(100vh-140px)] py-6 sm:py-10 gap-4 sm:gap-8">
              <div className="hidden sm:block">
                <GoldenTree />
              </div>
              <h1 className="text-center font-bold text-[#1A1A1A] text-[clamp(1.2rem,2.8vw,2rem)] max-w-[90vw] sm:max-w-170 leading-[1.3] px-4 sm:px-0">
                ¿Tienes alguna consulta sobre normatividad?
              </h1>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 w-full max-w-5xl items-stretch px-3 py-2 sm:p-6">
                {EXAMPLE_QUESTIONS.map((q) => (
                  <BlobCard key={q} question={q} onClick={() => handleSend(q)} />
                ))}
              </div>
            </div>
          ) : (
            <div className="py-6">
              {messages.map((m) => (
                <ChatMessage key={m.id} message={m} />
              ))}
              <div ref={bottomRef} />
            </div>
          )}
        </div>
      </main>

      {/* Input bar */}
      <footer className="shrink-0 px-4 py-4 relative z-10">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-3 items-end bg-white rounded-full pt-2 pr-2 pb-2 pl-5 shadow-[0_4px_24px_rgba(0,0,0,0.12)] border border-[#E0D6C8]">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={sending}
              placeholder="Escribe tu pregunta sobre la normatividad de Uninorte..."
              rows={1}
              className="flex-1 resize-none text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none disabled:opacity-50 overflow-y-auto bg-transparent border-none min-h-10 max-h-30 leading-normal pt-2.5"
            />
            <button
              onClick={() => handleSend()}
              disabled={sending || !input.trim()}
              className="shrink-0 flex items-center justify-center transition-opacity hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed w-11 h-11 rounded-full bg-[#8B1C1C] border-none cursor-pointer"
            >
              {sending ? (
                <svg className="w-5 h-5 animate-spin text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                </svg>
              )}
            </button>
          </div>
          <p className="text-center text-xs mt-2 text-[#9C8E80]">
            Enter para enviar · Shift+Enter para nueva línea · Prototipo SLM — Uninorte 2025
          </p>
        </div>
      </footer>
    </div>
  );
}
