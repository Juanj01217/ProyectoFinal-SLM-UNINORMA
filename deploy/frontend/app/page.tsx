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
        width={200}
        height={52}
        className="h-13 w-auto object-contain"
      />
      <span className="font-bold text-[1.1rem] text-white tracking-[0.01em]">
        Uninorma
      </span>
    </div>
  );
}

function GoldenTree() {
  return (
    <svg width="180" height="145" viewBox="0 0 451 363" xmlns="http://www.w3.org/2000/svg">
      <polygon fill="#F2B705" points="174,175 182,192 190,192 195,197 207,199 214,208 214,199 210,188 201,178 192,173 177,173" />
      <polygon fill="#F2B705" points="261,155 254,160 254,174 259,173 263,167 264,159" />
      <polygon fill="#F2B705" points="161,79 158,84 160,96 151,102 151,106 166,119 166,122 156,124 155,130 158,134 175,143 172,148 173,153 199,161 225,187 232,203 235,218 234,230 232,231 212,216 190,210 177,203 168,194 157,174 156,150 147,147 144,133 142,132 138,136 128,126 123,130 111,130 110,136 114,142 111,152 124,159 120,165 123,169 136,170 140,174 154,178 159,183 167,201 176,211 168,213 162,210 145,188 142,187 136,192 126,181 120,180 116,187 109,184 100,185 99,191 89,197 89,201 98,208 97,214 99,216 112,215 112,223 116,225 131,218 137,225 143,223 152,216 147,208 169,217 198,219 201,224 193,229 168,227 164,233 153,234 145,250 159,257 165,255 170,250 179,252 186,240 200,230 211,229 222,236 229,255 228,284 222,302 211,308 177,311 165,315 317,315 306,311 267,307 259,300 253,273 254,250 257,243 268,231 278,229 292,235 304,252 312,250 319,256 336,252 337,248 332,242 331,235 319,233 315,227 290,229 283,224 287,220 311,218 331,211 330,216 341,224 347,224 349,219 352,218 366,225 370,223 369,217 371,215 383,216 385,214 385,207 393,201 393,197 384,192 380,184 367,188 364,181 360,180 355,182 346,192 343,188 338,187 326,205 315,213 303,213 300,211 315,198 315,192 308,191 302,195 297,207 292,212 270,219 255,229 252,228 251,224 258,209 268,199 279,193 305,185 324,163 326,165 322,173 330,176 340,175 343,168 359,169 361,164 358,159 370,154 372,151 369,145 372,131 370,129 359,130 355,125 346,131 340,128 336,129 329,146 321,145 318,149 311,173 306,179 295,184 287,182 297,171 299,165 299,158 292,156 285,166 284,183 279,187 274,187 276,159 279,151 285,145 297,142 302,133 321,130 323,124 316,119 316,116 327,110 331,105 331,102 323,95 324,82 322,79 317,78 311,83 304,80 299,81 295,95 289,92 285,93 283,100 285,113 278,118 278,130 280,133 292,124 294,125 275,151 271,175 267,185 259,196 247,206 245,204 246,152 253,141 264,132 268,125 266,121 259,120 257,116 271,102 274,95 272,88 260,88 265,67 263,65 253,66 247,53 244,50 240,50 235,54 230,66 221,64 218,68 223,88 221,90 216,88 209,90 211,101 225,116 223,120 217,121 215,126 233,145 236,146 238,142 239,124 243,120 242,156 238,187 236,189 232,187 221,173 221,168 225,161 224,151 219,153 217,165 213,166 194,149 189,141 188,134 200,144 206,124 206,119 198,115 198,94 194,92 187,95 185,85 181,80 171,83 166,79" />
    </svg>
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
        <div className="relative bg-[#F7F5F2] rounded-[48px_24px_48px_24px] py-8 px-7 border border-[#e8e8e8] shadow-[0_10px_25px_rgba(0,0,0,0.07)] z-1 font-sans h-full box-border flex items-start gap-3">
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
    <div className="flex flex-col h-screen bg-[#F5EFE4] bg-[url('/figurabg.svg')] bg-repeat bg-position-[300px_300px]">
      {/* Header */}
      <header className="shrink-0 bg-[#9D1B1E] border-b border-[#E8DDD0] relative z-10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between flex-wrap gap-3">
          <UninorteLogo />
          <div className="flex items-center gap-3">
            <Link
              href="/benchmark"
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-white transition-opacity hover:opacity-90 bg-[#1A1A2E]"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.8}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              Benchmark
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
            <div className="flex flex-col items-center justify-center min-h-[calc(100vh-140px)] py-10 gap-8">
              <GoldenTree />
              <h1 className="text-center font-bold text-[#1A1A1A] text-[clamp(1.4rem,2.8vw,2rem)] max-w-170 leading-[1.3]">
                ¿Tienes alguna consulta sobre normatividad?
              </h1>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 w-full max-w-5xl items-stretch p-6">
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
          <div className="flex gap-3 items-end bg-white rounded-full pt-2 pr-2 pb-2 pl-5 shadow-[0_2px_12px_rgba(0,0,0,0.08)] border border-[#E0D6C8]">
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
