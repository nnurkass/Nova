import React from 'react';
import { 
  Building2, 
  Moon, 
  Sun, 
  History, 
  PlusCircle, 
  Activity, 
  ShieldCheck, 
  Database,
  Cpu
} from 'lucide-react';

interface HeaderProps {
  darkMode: boolean;
  setDarkMode: (val: boolean) => void;
  systemStatus: {
    status: string;
    components: Record<string, string>;
  };
  onOpenHistory: () => void;
  onNewTask: () => void;
  historyCount: number;
}

export const Header: React.FC<HeaderProps> = ({
  darkMode,
  setDarkMode,
  systemStatus,
  onOpenHistory,
  onNewTask,
  historyCount,
}) => {
  const isOnline = systemStatus.status === 'ok' || systemStatus.status === 'degraded';

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-[#0B0F19]/90 backdrop-blur-md transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={onNewTask}>
            <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 via-indigo-600 to-sky-500 shadow-lg shadow-cyan-500/20 text-white font-bold">
              <Building2 className="w-5 h-5" />
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </span>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-cyan-400">
                  NOVA
                </span>
                <span className="text-[10px] uppercase font-bold tracking-widest px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                  Multi-Agent AI
                </span>
              </div>
              <p className="text-xs text-slate-400 font-medium">
                Строительный AI-директор РК
              </p>
            </div>
          </div>

          {/* System Health Indicators (Desktop) */}
          <div className="hidden md:flex items-center space-x-4 text-xs">
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-800">
              <span className={`h-2 w-2 rounded-full ${isOnline ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
              <span className="text-slate-300 font-medium">API:</span>
              <span className={`font-mono font-semibold ${isOnline ? 'text-emerald-400' : 'text-rose-400'}`}>
                {isOnline ? 'Online (v0.1.0)' : 'Connecting...'}
              </span>
            </div>

            <div className="flex items-center space-x-3 px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 text-slate-400">
              <span className="flex items-center space-x-1" title="База данных">
                <Database className="w-3.5 h-3.5 text-indigo-400" />
                <span>DB: OK</span>
              </span>
              <span className="text-slate-600">|</span>
              <span className="flex items-center space-x-1" title="Госзакупки">
                <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
                <span>Goszakup: Live</span>
              </span>
              <span className="text-slate-600">|</span>
              <span className="flex items-center space-x-1" title="Claude LLM / Graph">
                <Cpu className="w-3.5 h-3.5 text-amber-400" />
                <span>Sonnet 4.6</span>
              </span>
            </div>
          </div>

          {/* Actions & Theme toggle */}
          <div className="flex items-center space-x-3">
            <button
              onClick={onNewTask}
              className="hidden sm:flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-600/20 transition-all active:scale-95"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Новый анализ</span>
            </button>

            <button
              onClick={onOpenHistory}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700 text-xs font-medium transition-colors relative active:scale-95"
            >
              <History className="w-4 h-4 text-cyan-400" />
              <span>История</span>
              {historyCount > 0 && (
                <span className="ml-1 px-1.5 py-0.2 bg-cyan-500/20 text-cyan-300 rounded text-[11px] font-mono">
                  {historyCount}
                </span>
              )}
            </button>

            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-white border border-slate-700 transition-colors active:scale-95"
              aria-label="Toggle theme"
            >
              {darkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-400" />}
            </button>
          </div>

        </div>
      </div>
    </header>
  );
};
