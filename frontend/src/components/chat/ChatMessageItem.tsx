import React, { useState } from 'react';
import { 
  Bot, 
  User, 
  ChevronDown, 
  ChevronUp, 
  Brain, 
  Sparkles, 
  Building2, 
  FileSpreadsheet, 
  Package, 
  Coins, 
  ExternalLink,
  Copy,
  Check
} from 'lucide-react';
import { ChatMessage } from '../../types';

interface ChatMessageItemProps {
  message: ChatMessage;
  onSelectSuggestion?: (suggestion: string) => void;
  onOpenTab?: (tab: 'tender' | 'pto' | 'stock' | 'orders' | 'financial') => void;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({
  message,
  onSelectSuggestion,
  onOpenTab,
}) => {
  const [showThought, setShowThought] = useState(false);
  const [copied, setCopied] = useState(false);

  const isUser = message.role === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Render markdown-like simple formatting
  const formatMarkdown = (text: string) => {
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      // Headings
      if (line.startsWith('### ')) {
        return (
          <h3 key={idx} className="text-base font-bold text-cyan-300 mt-3 mb-1.5 flex items-center gap-1.5">
            {line.replace('### ', '')}
          </h3>
        );
      }
      if (line.startsWith('## ')) {
        return (
          <h2 key={idx} className="text-lg font-extrabold text-slate-100 mt-4 mb-2">
            {line.replace('## ', '')}
          </h2>
        );
      }
      // Lists
      if (line.startsWith('* ') || line.startsWith('- ')) {
        return (
          <li key={idx} className="ml-4 list-disc text-slate-300 my-0.5 text-sm">
            {renderInlineFormat(line.substring(2))}
          </li>
        );
      }
      // Numbered lists
      const numMatch = line.match(/^(\d+)\.\s+(.*)/);
      if (numMatch) {
        return (
          <div key={idx} className="flex items-start gap-2 my-1 text-sm text-slate-300">
            <span className="font-bold text-cyan-400 min-w-[1.2rem]">{numMatch[1]}.</span>
            <div>{renderInlineFormat(numMatch[2])}</div>
          </div>
        );
      }
      // Empty line
      if (!line.trim()) {
        return <div key={idx} className="h-2" />;
      }
      // Paragraph
      return (
        <p key={idx} className="my-1 text-sm text-slate-200 leading-relaxed">
          {renderInlineFormat(line)}
        </p>
      );
    });
  };

  const renderInlineFormat = (text: string) => {
    // Bold **text**
    const parts = text.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="font-semibold text-cyan-200">{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('*') && part.endsWith('*')) {
        return <em key={i} className="italic text-slate-400">{part.slice(1, -1)}</em>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code key={i} className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-cyan-300 text-xs font-mono">
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  return (
    <div className={`flex gap-3.5 my-4 group ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div
        className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 shadow-md ${
          isUser
            ? 'bg-gradient-to-br from-indigo-500 to-cyan-500 text-white'
            : 'bg-gradient-to-br from-cyan-900/80 to-slate-900 border border-cyan-500/30 text-cyan-400'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Message Bubble */}
      <div className={`max-w-[85%] sm:max-w-[78%] flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        
        {/* Header (Sender title + time) */}
        <div className="flex items-center gap-2 mb-1 px-1 text-xs text-slate-400">
          <span className="font-medium text-slate-300">
            {isUser ? 'Вы' : (message.senderTitle || 'Операционный директор (COO)')}
          </span>
          <span className="text-[10px] text-slate-500">{message.timestamp}</span>
        </div>

        {/* Thought accordion for AI messages */}
        {!isUser && message.thought && (
          <div className="mb-2 w-full">
            <button
              onClick={() => setShowThought(!showThought)}
              className="flex items-center gap-1.5 text-xs text-cyan-400/90 hover:text-cyan-300 bg-cyan-950/40 hover:bg-cyan-900/40 px-2.5 py-1 rounded-lg border border-cyan-800/40 transition-colors"
            >
              <Brain className="w-3.5 h-3.5" />
              <span>Ход рассуждений агента</span>
              {showThought ? <ChevronUp className="w-3 h-3 ml-1" /> : <ChevronDown className="w-3 h-3 ml-1" />}
            </button>
            {showThought && (
              <div className="mt-1.5 p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs text-slate-300 space-y-1 font-mono leading-relaxed animate-fadeIn">
                <div className="flex items-center gap-1 text-[11px] text-cyan-400 font-semibold mb-1">
                  <Sparkles className="w-3 h-3" />
                  <span>ReAct Loop & Анализ контекста:</span>
                </div>
                {message.thought}
              </div>
            )}
          </div>
        )}

        {/* Main Content Box */}
        <div
          className={`p-4 rounded-2xl relative text-sm shadow-lg ${
            isUser
              ? 'bg-gradient-to-r from-cyan-600 to-indigo-600 text-white rounded-tr-none'
              : 'bg-slate-900/90 border border-slate-800 text-slate-200 rounded-tl-none'
          }`}
        >
          {formatMarkdown(message.content)}

          {/* If state was attached (pipeline finished), show quick artifact jump chips */}
          {!isUser && message.state?.selected_tender && onOpenTab && (
            <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap gap-2">
              <span className="text-xs text-slate-400 w-full mb-0.5">📂 Сформированные документы:</span>
              <button
                onClick={() => onOpenTab('tender')}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-cyan-950/80 border border-slate-700 hover:border-cyan-500/50 text-xs text-cyan-300 transition-colors"
              >
                <Building2 className="w-3 h-3 text-cyan-400" />
                <span>Тендер</span>
              </button>
              <button
                onClick={() => onOpenTab('pto')}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-amber-950/80 border border-slate-700 hover:border-amber-500/50 text-xs text-amber-300 transition-colors"
              >
                <FileSpreadsheet className="w-3 h-3 text-amber-400" />
                <span>Смета ПТО ({message.state.work_list?.length || 0})</span>
              </button>
              <button
                onClick={() => onOpenTab('stock')}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-emerald-950/80 border border-slate-700 hover:border-emerald-500/50 text-xs text-emerald-300 transition-colors"
              >
                <Package className="w-3 h-3 text-emerald-400" />
                <span>Склад</span>
              </button>
              <button
                onClick={() => onOpenTab('financial')}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-emerald-950/80 border border-slate-700 hover:border-emerald-500/50 text-xs text-emerald-300 transition-colors"
              >
                <Coins className="w-3 h-3 text-emerald-400" />
                <span>Финансы & Отчет</span>
              </button>
            </div>
          )}

          {/* Copy button */}
          <button
            onClick={handleCopy}
            className="absolute top-2.5 right-2.5 opacity-0 group-hover:opacity-100 p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-all text-xs"
            title="Скопировать"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>

        {/* Suggestion action pills below AI message */}
        {!isUser && message.suggestions && message.suggestions.length > 0 && onSelectSuggestion && (
          <div className="mt-2 flex flex-wrap gap-1.5 w-full">
            {message.suggestions.map((sug, sIdx) => (
              <button
                key={sIdx}
                onClick={() => onSelectSuggestion(sug)}
                className="text-xs text-slate-300 hover:text-cyan-300 bg-slate-900/60 hover:bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-800 hover:border-cyan-500/40 transition-all text-left flex items-center gap-1"
              >
                <span>{sug}</span>
              </button>
            ))}
          </div>
        )}

      </div>
    </div>
  );
};
