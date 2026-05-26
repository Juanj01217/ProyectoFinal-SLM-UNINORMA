"use client";

import Image from "next/image";
import SourceCard from "./SourceCard";
import { Source } from "../lib/api";
import { useState } from "react";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  loading?: boolean;
}

interface Props {
  readonly message: Message;
}

function CopyButton({ text }: { readonly text: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard not available
    }
  }

  return (
    <button
      onClick={handleCopy}
      title={copied ? "Copiado" : "Copiar respuesta"}
      className="flex items-center justify-center w-7 h-7 rounded-lg text-[#9D1B1E]/35 hover:text-[#9D1B1E]/70 hover:bg-[#9D1B1E]/8 transition-all duration-150 cursor-pointer border-none bg-transparent"
    >
      {copied ? (
        <svg className="w-3.5 h-3.5 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      ) : (
        <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
          <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
        </svg>
      )}
    </button>
  );
}

export default function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end mb-4 message-enter">
        <div className="max-w-[75%] sm:max-w-[65%] bg-[#9D1B1E] text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-md">
          <p className="whitespace-pre-wrap leading-relaxed text-sm">{message.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start mb-4 gap-3 message-enter">
      <div className="w-7 h-7 rounded-full bg-[#9D1B1E] ring-2 ring-[#9D1B1E]/20 flex items-center justify-center shrink-0 mt-1 overflow-hidden">
        <Image src="/uninorte_tree.svg" alt="Uninorma" width={18} height={18} className="object-contain" />
      </div>

      <div className="flex-1 min-w-0 bg-white/60 backdrop-blur-sm rounded-xl px-4 py-4 shadow-sm border border-white/80">
        {message.loading ? (
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#9D1B1E]/60 animate-bounce [animation-delay:0ms]" />
            <span className="w-2 h-2 rounded-full bg-[#9D1B1E]/60 animate-bounce [animation-delay:150ms]" />
            <span className="w-2 h-2 rounded-full bg-[#9D1B1E]/60 animate-bounce [animation-delay:300ms]" />
          </div>
        ) : (
          <>
            <p className="whitespace-pre-wrap leading-relaxed text-sm text-[#1A1A1A]">{message.content}</p>
            {message.sources && <SourceCard sources={message.sources} />}
            <div className="flex justify-end mt-2">
              <CopyButton text={message.content} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
