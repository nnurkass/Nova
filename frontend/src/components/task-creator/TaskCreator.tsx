import React, { useState } from 'react';
import { 
  Sparkles, 
  MapPin, 
  Coins, 
  Play, 
  Square, 
  ArrowRight,
  Layers,
  Wand2
} from 'lucide-react';
import { TaskRequest } from '../../types';

interface TaskCreatorProps {
  onStartTask: (payload: TaskRequest) => void;
  isRunning: boolean;
  onStopTask: () => void;
}

const REGIONS = [
  'Все регионы',
  'г. Алматы',
  'г. Астана',
  'г. Шымкент',
  'г. Караганда',
  'г. Актобе',
  'г. Атырау',
  'г. Актау',
];

const PRESETS = [
  {
    title: '🏫 Капремонт школы в Алматы',
    prompt: 'Капитальный ремонт средней школы в г. Алматы с заменой кровли, инженерных сетей и отделочными работами',
    region: 'г. Алматы',
    budget: 50000000,
  },
  {
    title: '🚰 Сети водоснабжения в Астане',
    prompt: 'Строительство и монтаж магистральных сетей водоснабжения и напорной канализации в г. Астана',
    region: 'г. Астана',
    budget: 85000000,
  },
  {
    title: '🏥 Ремонт больницы в Шымкенте',
    prompt: 'Текущий ремонт и модернизация помещений городской больницы в г. Шымкент',
    region: 'г. Шымкент',
    budget: 35000000,
  },
  {
    title: '👶 Реконструкция детсада в Караганде',
    prompt: 'Реконструкция и благоустройство территории детского сада в г. Караганда с установкой МАФ',
    region: 'г. Караганда',
    budget: 30000000,
  },
];

export const TaskCreator: React.FC<TaskCreatorProps> = ({
  onStartTask,
  isRunning,
  onStopTask,
}) => {
  const [taskText, setTaskText] = useState('Капитальный ремонт средней школы в г. Алматы с заменой кровли и инженерных сетей');
  const [selectedRegion, setSelectedRegion] = useState('г. Алматы');
  const [budgetMax, setBudgetMax] = useState<number>(50000000);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskText.trim() || isRunning) return;

    onStartTask({
      task: taskText.trim(),
      region: selectedRegion === 'Все регионы' ? undefined : selectedRegion,
      budget_max: budgetMax > 0 ? budgetMax : undefined,
    });
  };

  const handleApplyPreset = (preset: typeof PRESETS[0]) => {
    setTaskText(preset.prompt);
    setSelectedRegion(preset.region);
    setBudgetMax(preset.budget);
  };

  return (
    <div className="w-full glass-panel rounded-2xl p-5 sm:p-7 border border-slate-800 shadow-2xl relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute top-0 right-1/4 w-96 h-32 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-1/3 w-80 h-32 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              Постановка строительной задачи
              <span className="text-xs font-normal px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                Этап 1-4 LangGraph
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Введите описание объекта или выберите готовый сценарий для запуска цепочки агентов
            </p>
          </div>
        </div>
      </div>

      {/* Preset pills */}
      <div className="mb-4">
        <div className="flex items-center space-x-1.5 mb-2 text-xs font-medium text-slate-400">
          <Wand2 className="w-3.5 h-3.5 text-cyan-400" />
          <span>Быстрые шаблоны тендеров РК:</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
          {PRESETS.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleApplyPreset(preset)}
              disabled={isRunning}
              className="text-left px-3 py-2 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 hover:border-cyan-500/40 text-xs text-slate-300 hover:text-white transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              <div className="font-semibold text-slate-200 group-hover:text-cyan-400 truncate">
                {preset.title}
              </div>
              <div className="text-[11px] text-slate-400 truncate mt-0.5">
                {preset.region} • {(preset.budget / 1000000).toFixed(0)} млн ₸
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main input form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <textarea
            value={taskText}
            onChange={(e) => setTaskText(e.target.value)}
            disabled={isRunning}
            rows={2}
            placeholder="Опишите задачу, например: «Поиск тендеров и расчет сметы на строительство водопровода в г. Астана»"
            className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 text-sm resize-none transition-all disabled:opacity-60"
          />
        </div>

        {/* Filters and Controls Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
          
          {/* Region selector */}
          <div className="flex items-center space-x-2 bg-slate-900/80 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
            <MapPin className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
            <span className="text-slate-400 font-medium">Регион:</span>
            <select
              value={selectedRegion}
              onChange={(e) => setSelectedRegion(e.target.value)}
              disabled={isRunning}
              className="bg-transparent text-slate-200 font-medium focus:outline-none cursor-pointer text-xs"
            >
              {REGIONS.map((reg) => (
                <option key={reg} value={reg} className="bg-slate-900 text-slate-200">
                  {reg}
                </option>
              ))}
            </select>
          </div>

          {/* Budget Filter */}
          <div className="flex items-center space-x-2 bg-slate-900/80 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
            <Coins className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
            <span className="text-slate-400 font-medium">Лимит бюджета:</span>
            <input
              type="number"
              value={budgetMax || ''}
              onChange={(e) => setBudgetMax(Number(e.target.value))}
              disabled={isRunning}
              step={1000000}
              min={1000000}
              placeholder="Без ограничений"
              className="w-28 bg-transparent text-slate-200 font-mono font-medium focus:outline-none text-xs"
            />
            <span className="text-slate-400">₸</span>
          </div>

          {/* Submit / Stop Buttons */}
          <div className="flex items-center space-x-2 ml-auto">
            {isRunning ? (
              <button
                type="button"
                onClick={onStopTask}
                className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold shadow-lg shadow-rose-600/30 transition-all active:scale-95 animate-pulse"
              >
                <Square className="w-4 h-4 fill-current" />
                <span>Остановить стрим</span>
              </button>
            ) : (
              <button
                type="submit"
                disabled={!taskText.trim()}
                className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 via-sky-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white text-xs font-bold shadow-lg shadow-cyan-500/25 transition-all duration-200 hover:shadow-cyan-500/40 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed group"
              >
                <Play className="w-4 h-4 fill-current" />
                <span>Запустить агентов Nova</span>
                <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" />
              </button>
            )}
          </div>

        </div>
      </form>
    </div>
  );
};
