import React, { useEffect, useRef, useState } from 'react';
import { 
  Terminal, 
  Copy, 
  Check, 
  ArrowDown, 
  Trash2,
  Cpu,
  CornerDownRight
} from 'lucide-react';
import { TerminalLog } from '../../types';

interface AgentTerminalProps {
  logs: TerminalLog[];
  onClearLogs: () => void;
}

export const AgentTerminal: React.FC<AgentTerminalProps> = ({
  logs,
  onClearLogs,
}) => {
  const [autoScroll, setAutoScroll] = useState(true);
  const [copied, setCopied] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const handleCopyLogs = () => {
    const text = logs.map((l) => `[${l.timestamp}] [${l.agentName}] ${l.message}`).join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getAgentBadge = (name: string) => {
    const upper = name.toUpperCase();
    if (upper.includes('COO') || upper.includes('ДИРЕКТОР')) {
      return 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30';
    }
    if (upper.includes('ЗАКУП') || upper.includes('PROCUREMENT') || upper.includes('GOSZAKUP')) {
      return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
    }
    if (upper.includes('ПТО') || upper.includes('PTO') || upper.includes('ИНЖЕНЕР')) {
      return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
    }
    if (upper.includes('СНАБЖ') || upper.includes('SUPPLY') || upper.includes('СКЛАД')) {
      return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
    }
    return 'bg-slate-700/40 text-slate-300 border-slate-600/30';
  };

  return (
    <div className="w-full rounded-2xl bg-slate-950/90 border border-slate-800 shadow-2xl overflow-hidden flex flex-col font-mono-code">
      {/* Terminal Window Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-900/90 border-b border-slate-800/80">
        <div className="flex items-center space-x-2">
          <div className="flex space-x-1.5">
            <div className="w-3 h-3 rounded-full bg-rose-500/80" />
            <div className="w-3 h-3 rounded-full bg-amber-500/80" />
            <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
          </div>
          <div className="flex items-center space-x-2 ml-2">
            <Terminal className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-semibold text-slate-300">
              Agent Thoughts & Realtime Execution Log
            </span>
          </div>
        </div>

        {/* Toolbar Controls */}
        <div className="flex items-center space-x-2 text-xs">
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`px-2.5 py-1 rounded-md text-[11px] border transition-colors flex items-center space-x-1 ${
              autoScroll
                ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
                : 'bg-slate-800 text-slate-400 border-slate-700'
            }`}
            title="Автоматическая прокрутка к последнему сообщению"
          >
            <ArrowDown className="w-3 h-3" />
            <span>Автопрокрутка</span>
          </button>

          <button
            onClick={handleCopyLogs}
            disabled={logs.length === 0}
            className="p-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors disabled:opacity-40"
            title="Копировать логи"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>

          <button
            onClick={onClearLogs}
            disabled={logs.length === 0}
            className="p-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-rose-400 border border-slate-700 transition-colors disabled:opacity-40"
            title="Очистить терминал"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Terminal Output Body */}
      <div
        ref={scrollRef}
        className="p-4 max-h-72 min-h-[140px] overflow-y-auto space-y-2 text-xs leading-relaxed"
      >
        {logs.length === 0 ? (
          <div className="h-28 flex flex-col items-center justify-center text-slate-500 space-y-2">
            <Cpu className="w-6 h-6 animate-pulse text-slate-600" />
            <p className="text-xs">Ожидание запуска задачи. Логи работы агентов появятся здесь в реальном времени...</p>
          </div>
        ) : (
          logs.map((log) => (
            <div
              key={log.id}
              className="flex items-start space-x-2.5 py-0.5 hover:bg-slate-900/50 rounded px-1.5 transition-colors group"
            >
              {/* Timestamp */}
              <span className="text-[11px] text-slate-500 select-none flex-shrink-0 pt-0.5">
                {log.timestamp}
              </span>

              {/* Agent Badge */}
              <span
                className={`text-[10px] uppercase font-bold px-1.5 py-0.2 rounded border flex-shrink-0 select-none ${getAgentBadge(
                  log.agentName
                )}`}
              >
                {log.agentName}
              </span>

              {/* Message body */}
              <div className="flex-1 text-slate-200 break-words flex items-start space-x-1.5">
                <CornerDownRight className="w-3 h-3 text-slate-600 mt-1 flex-shrink-0" />
                <span className="leading-5 whitespace-pre-wrap">{log.message}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
