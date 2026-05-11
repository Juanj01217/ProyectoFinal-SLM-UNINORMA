import Image from "next/image";
import SourceCard from "./SourceCard";
import { Source } from "../lib/api";

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

export default function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-[#9D1B1E] flex items-center justify-center shrink-0 mr-3 mt-1 overflow-hidden">
          <Image src="/uninorte_tree.svg" alt="Uninorma" width={20} height={20} className="object-contain" />
        </div>
      )}

      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-[#9D1B1E] text-white rounded-tr-sm"
            : "bg-white border border-gray-200 text-gray-800 rounded-tl-sm shadow-sm"
        }`}
      >
        {message.loading ? (
          <div className="flex items-center gap-2 text-gray-400">
            <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:0ms]" />
            <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:150ms]" />
            <span className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:300ms]" />
          </div>
        ) : (
          <>
            <p className="whitespace-pre-wrap leading-relaxed text-sm">{message.content}</p>
            {!isUser && message.sources && <SourceCard sources={message.sources} />}
          </>
        )}
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-gray-600 text-sm font-bold shrink-0 ml-3 mt-1">
          Tú
        </div>
      )}
    </div>
  );
}
