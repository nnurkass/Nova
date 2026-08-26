import React, { useRef, useEffect } from 'react';
import { 
  Sparkles, 
  Trash2, 
  Bot, 
  Building2, 
  FileSpreadsheet, 
  Package, 
  Coins, 
  ArrowRight,
  ShieldCheck
} from 'lucide-react';
import { ChatMessage } from '../../types';
import { ChatMessageItem } from './ChatMessageItem';
import { ChatInputBar } from './ChatInputBar';

interface ChatContainerProps {
  messages: ChatMessage[];
  isLoading: boolean;
  onSendMessage: (text: string) => void;
  onClearChat: () => void;
  onOpenTab?: (tab: 'tender' | 'pto' | 'stock' | 'orders' | 'financial') => void;
  activeAgent?: string;
}

const STARTER_PROMPTS = [
  {
    title: '🏭 Склад из сэндвич-панелей 800 м²',
    desc: 'Караганда: фундамент, металлокаркас, PIR-панели',
    prompt: 'Найди тендер на строительство быстровозводимого склада 800 м2 в г. Караганда и рассчитай смету',
    icon: Building2,
    color: 'text-cyan-400',
  },
  {
    title: '🌾 Зернохранилище 1500 м² в Кокшетау',
    desc: 'Земляные работы, стальной каркас, ворота',
    prompt: 'Рассчитай проект: строительство зернохранилища 1500 кв.м в г. Кокшетау с расчетом потребности материалов',
    icon: Package,
    color: 'text-amber-400',
  },
  {
    title: '🏫 Капремонт школы в Алматы',
    desc: 'Кровля, фасад, инженерные сети и отделка',
    prompt: 'Найди тендер на капитальный ремонт здания школы в Алматы и рассчитай ведомость материалов',
    icon: FileSpreadsheet,
    color: 'text-emerald-400',
  },
  {
    title: '🚰 Магистральный водопровод в Астане',
    desc: 'Трубы ПЭ100 d160, ж/б колодцы, земляные работы',
    prompt: 'Рассчитай смету на строительство наружных сетей водопровода 2.5 км в г. Астана',
    icon: Coins,
    color: 'text-indigo-400',
  },
];

export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  isLoading,
  onSendMessage,
  onClearChat,
  onOpenTab,
  activeAgent = 'coo',
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  // Current suggestions from latest AI message
  const lastAiMsg = [...messages].reverse().find((m) => m.role === 'assistant');
  const suggestions = lastAiMsg?.suggestions || [];

  return (
    <div className="flex flex-col h-full bg-slate-950/60 rounded-2xl border border-slate-800/80 shadow-2xl relative overflow-hidden backdrop-blur-xl">
      
      {/* Chat Top Header */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-800/80 bg-slate-900/60 flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-slate-100">AI-Консультант Nova</h2>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-medium text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Live Agents
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Координатор COO • Госзакупки РК • ПТО • Снабжение
            </p>
          </div>
        </div>

        {messages.length > 0 && (
          <button
            onClick={onClearChat}
            disabled={isLoading}
            className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800/60 rounded-lg transition-colors text-xs flex items-center gap-1"
            title="Очистить диалог"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Очистить</span>
          </button>
        )}
      </div>

      {/* Messages Scroll Area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 sm:px-6 py-4 space-y-2">
        {messages.length === 0 ? (
          /* Empty state */
          <div className="h-full flex flex-col justify-center max-w-xl mx-auto py-8 text-center space-y-6">
            <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-xl shadow-cyan-500/10">
              <Bot className="w-7 h-7" />
            </div>

            <div className="space-y-2">
              <h3 className="text-lg font-bold text-slate-100">
                Чем могу помочь вашей строительной компании?
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed max-w-md mx-auto">
                Я координирую команду AI-агентов. Мы найдем подходящий тендер на <b>goszakup.gov.kz</b>, 
                распарсим ТЗ, сформируем ведомость объемов работ (ВОР), сверим склад и посчитаем маржу.
              </p>
            </div>

            {/* Quick Starters Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-left pt-2">
              {STARTER_PROMPTS.map((item, idx) => {
                const Icon = item.icon;
                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => onSendMessage(item.prompt)}
                    disabled={isLoading}
                    className="p-3 rounded-xl bg-slate-900/70 hover:bg-slate-800/90 border border-slate-800 hover:border-cyan-500/40 text-left transition-all duration-200 group flex flex-col justify-between"
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <Icon className={`w-4 h-4 ${item.color}`} />
                        <span className="text-xs font-semibold text-slate-200 group-hover:text-cyan-400">
                          {item.title}
                        </span>
                      </div>
                      <ArrowRight className="w-3 h-3 text-slate-600 group-hover:text-cyan-400 group-hover:translate-x-0.5 transition-transform" />
                    </div>
                    <p className="text-[11px] text-slate-400 line-clamp-2">
                      {item.desc}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>
        ) : (
          /* Render message history */
          <>
            {messages.map((msg) => (
              <ChatMessageItem
                key={msg.id}
                message={msg}
                onSelectSuggestion={onSendMessage}
                onOpenTab={onOpenTab}
              />
            ))}

            {/* Typing / Agent Processing Indicator */}
            {isLoading && (
              <div className="flex gap-3 my-4 animate-fadeIn">
                <div className="w-8 h-8 rounded-xl bg-cyan-950 border border-cyan-500/30 text-cyan-400 flex items-center justify-center flex-shrink-0 animate-pulse">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="p-3.5 rounded-2xl bg-slate-900 border border-slate-800 text-xs text-slate-300 flex items-center gap-2.5 shadow-lg">
                  <span className="flex gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                  </span>
                  <span className="text-slate-400">Агенты Nova выполняют расчет и формируют ответ...</span>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Input Bottom Bar */}
      <div className="p-3 sm:p-4 border-t border-slate-800/80 bg-slate-900/40 flex-shrink-0">
        <ChatInputBar
          onSendMessage={onSendMessage}
          isLoading={isLoading}
          suggestions={messages.length > 0 ? suggestions : []}
          onSelectSuggestion={onSendMessage}
        />
      </div>

    </div>
  );
};
