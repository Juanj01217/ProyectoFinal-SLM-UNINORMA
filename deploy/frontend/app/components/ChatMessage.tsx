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
          </>
        )}
      </div>
    </div>
  );
}
