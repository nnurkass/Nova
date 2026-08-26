import React, { useState } from 'react';
import { 
  X, 
  History, 
  Search, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  ArrowRight,
  RefreshCw,
  Coins
} from 'lucide-react';
import { TaskItem } from '../../types';
import { formatCurrencyKZT, formatDate } from '../../utils/formatters';

interface TaskHistorySidebarProps {
  isOpen: boolean;
  onClose: () => void;
  tasks: TaskItem[];
  currentTaskId?: string;
  onSelectTask: (task: TaskItem) => void;
  onRefresh: () => void;
  isLoading: boolean;
}

export const TaskHistorySidebar: React.FC<TaskHistorySidebarProps> = ({
  isOpen,
  onClose,
  tasks = [],
  currentTaskId,
  onSelectTask,
  onRefresh,
  isLoading,
}) => {
  const [search, setSearch] = useState('');

  if (!isOpen) return null;

  const filteredTasks = tasks.filter((t) => {
    const prompt = t.result?.task || t.task_id;
    return prompt.toLowerCase().includes(search.toLowerCase());
  });

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Drawer Panel */}
      <div className="relative w-full max-w-md bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col h-full z-10">
        
        {/* Drawer Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/90">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100">История запусков Nova</h3>
              <p className="text-[11px] text-slate-400">Всего сохранено в БД: {tasks.length}</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
              title="Обновить список"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-cyan-400' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Search input */}
        <div className="p-4 border-b border-slate-800/80">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск по названию задачи..."
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-slate-200 text-xs placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>

        {/* Tasks List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {filteredTasks.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              История пуста или совпадений не найдено.
            </div>
          ) : (
            filteredTasks.map((t) => {
              const isSelected = t.task_id === currentTaskId;
              const isDone = t.status === 'completed';
              const isErr = t.status === 'failed';
              const budget = t.result?.selected_tender?.total_sum;
              const title = t.result?.task || (t.result?.selected_tender?.name_ru) || 'Анализ тендера';

              return (
                <div
                  key={t.task_id}
                  onClick={() => {
                    onSelectTask(t);
                    onClose();
                  }}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-cyan-500/10 border-cyan-500/50 shadow-md shadow-cyan-500/10'
                      : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <div className="flex items-center space-x-1.5">
                      {isDone && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                      {isErr && <AlertCircle className="w-3.5 h-3.5 text-rose-400" />}
                      {!isDone && !isErr && <Clock className="w-3.5 h-3.5 text-cyan-400 animate-spin" />}
                      <span className={`text-[10px] uppercase font-bold ${
                        isDone ? 'text-emerald-400' : isErr ? 'text-rose-400' : 'text-cyan-400'
                      }`}>
                        {t.status}
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-500 font-mono">
                      {formatDate(t.created_at)}
                    </span>
                  </div>

                  <h4 className="text-xs font-semibold text-slate-200 line-clamp-2 leading-relaxed">
                    {title}
                  </h4>

                  {budget && (
                    <div className="mt-2 flex items-center justify-between text-[11px] pt-2 border-t border-slate-800/60">
                      <span className="text-slate-400">Бюджет:</span>
                      <span className="font-mono font-bold text-emerald-400">
                        {formatCurrencyKZT(budget)}
                      </span>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
