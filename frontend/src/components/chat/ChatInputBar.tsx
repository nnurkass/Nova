import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Paperclip, StopCircle, ArrowUp } from 'lucide-react';

interface ChatInputBarProps {
  onSendMessage: (text: string) => void;
  isLoading: boolean;
  onStop?: () => void;
  suggestions?: string[];
  onSelectSuggestion?: (sug: string) => void;
}

export const ChatInputBar: React.FC<ChatInputBarProps> = ({
  onSendMessage,
  isLoading,
  onStop,
  suggestions = [],
  onSelectSuggestion,
}) => {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-grow textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [text]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!text.trim() || isLoading) return;

    onSendMessage(text.trim());
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full relative space-y-2">
      {/* Dynamic Starter suggestions */}
      {suggestions.length > 0 && onSelectSuggestion && (
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar text-xs">
          <div className="flex items-center gap-1 text-cyan-400 font-medium px-1 flex-shrink-0">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Подсказки:</span>
          </div>
          {suggestions.map((sug, i) => (
            <button
              key={i}
              type="button"
              onClick={() => onSelectSuggestion(sug)}
              disabled={isLoading}
              className="flex-shrink-0 px-3 py-1 rounded-full bg-slate-900/80 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/40 text-slate-300 hover:text-white transition-all text-xs disabled:opacity-50"
            >
              {sug}
            </button>
          ))}
        </div>
      )}

      {/* Input container */}
      <form
        onSubmit={handleSubmit}
        className="glass-panel rounded-2xl p-2 sm:p-2.5 border border-slate-800/90 shadow-2xl focus-within:border-cyan-500/50 focus-within:ring-2 focus-within:ring-cyan-500/20 transition-all bg-slate-950/90"
      >
        <div className="flex items-end gap-2">
          {/* File attach button */}
          <button
            type="button"
            className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-xl transition-colors mb-0.5 flex-shrink-0"
            title="Загрузить смету или ТЗ (PDF, Excel, АВС)"
            onClick={() => alert('Функция прямой загрузки сметных файлов PDF/Excel будет доступна в следующем обновлении.')}
          >
            <Paperclip className="w-4 h-4" />
          </button>

          {/* Multiline textarea */}
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            rows={1}
            placeholder="Спросите о тендере, смете или напишите: «Найди капремонт школы в Алматы»..."
            className="w-full max-h-40 min-h-[40px] py-2 px-1 bg-transparent text-slate-100 placeholder-slate-500 text-sm focus:outline-none resize-none leading-relaxed"
          />

          {/* Send / Stop button */}
          <div className="flex-shrink-0 mb-0.5">
            {isLoading ? (
              <button
                type="button"
                onClick={onStop}
                className="p-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/30 transition-all active:scale-95"
                title="Остановить"
              >
                <StopCircle className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!text.trim()}
                className="p-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-40 disabled:cursor-not-allowed active:scale-95 group"
                title="Отправить (Enter)"
              >
                <ArrowUp className="w-4 h-4 group-hover:-translate-y-0.5 transition-transform" />
              </button>
            )}
          </div>
        </div>
      </form>
      <div className="flex items-center justify-between px-2 text-[11px] text-slate-500">
        <span>Enter — отправить, Shift+Enter — новая строка</span>
        <span className="font-mono">Nova Multi-Agent v0.1</span>
      </div>
    </div>
  );
};
