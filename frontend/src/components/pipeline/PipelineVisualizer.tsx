import React from 'react';
import { 
  Briefcase, 
  Search, 
  FileSpreadsheet, 
  Package, 
  FileText, 
  CheckCircle2, 
  Loader2, 
  AlertCircle, 
  Clock,
  ArrowRight
} from 'lucide-react';

export interface AgentNodeState {
  id: string;
  name: string;
  role: string;
  icon: React.ElementType;
  status: 'pending' | 'running' | 'success' | 'error';
  badge: string;
  description: string;
}

interface PipelineVisualizerProps {
  currentNode: string;
  activeStep: number;
  totalSteps: number;
  isComplete: boolean;
  hasError: boolean;
}

export const PipelineVisualizer: React.FC<PipelineVisualizerProps> = ({
  currentNode,
  activeStep,
  totalSteps,
  isComplete,
  hasError,
}) => {
  const getStepStatus = (nodeIndex: number, nodeId: string): 'pending' | 'running' | 'success' | 'error' => {
    if (hasError && (currentNode === nodeId || activeStep === nodeIndex)) return 'error';
    if (isComplete) return 'success';
    if (activeStep > nodeIndex) return 'success';
    if (activeStep === nodeIndex) return 'running';
    return 'pending';
  };

  const steps: AgentNodeState[] = [
    {
      id: 'coo',
      name: 'COO Supervisor',
      role: 'Операционный директор',
      icon: Briefcase,
      status: getStepStatus(1, 'coo'),
      badge: 'Level 1',
      description: 'Декомпозиция и контроль контекста',
    },
    {
      id: 'procurement',
      name: 'Гос. Закупщик',
      role: 'Procurement Agent',
      icon: Search,
      status: getStepStatus(2, 'procurement'),
      badge: 'Level 2',
      description: 'Поиск goszakup.gov.kz & Скоринг',
    },
    {
      id: 'pto',
      name: 'Инженер ПТО',
      role: 'Technical Dept',
      icon: FileSpreadsheet,
      status: getStepStatus(3, 'pto'),
      badge: 'Level 2',
      description: 'ВОР, АВС и СН РК (+5% запас)',
    },
    {
      id: 'supply',
      name: 'ОМТС / Снабжение',
      role: 'Supply Agent',
      icon: Package,
      status: getStepStatus(4, 'supply'),
      badge: 'Level 2',
      description: 'Склад, Дефицит & Заказы PO (+10%)',
    },
    {
      id: 'coo_summary',
      name: 'Executive Summary',
      role: 'Финансовый баланс',
      icon: FileText,
      status: getStepStatus(5, 'coo_summary'),
      badge: 'Итог',
      description: 'Расчет маржи % & Рекомендация',
    },
  ];

  return (
    <div className="w-full glass-panel rounded-2xl p-5 sm:p-6 border border-slate-800 shadow-xl">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <h3 className="text-sm font-bold tracking-wide uppercase text-slate-300">
            Realtime Pipeline Visualizer
          </h3>
        </div>
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
          <span>Прогресс пайплайна:</span>
          <span className="px-2 py-0.5 rounded-full bg-slate-800 text-cyan-400 font-bold border border-slate-700">
            {isComplete ? '100%' : `${Math.min(100, Math.round((activeStep / totalSteps) * 100))}%`}
          </span>
        </div>
      </div>

      {/* Nodes Row */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          const isCurrent = step.status === 'running';
          const isDone = step.status === 'success';
          const isErr = step.status === 'error';

          return (
            <div
              key={step.id}
              className={`relative flex flex-col p-4 rounded-xl border transition-all duration-200 ${
                isCurrent
                  ? 'bg-slate-900/90 border-cyan-500 shadow-lg shadow-cyan-500/10 ring-1 ring-cyan-500/50 scale-[1.02]'
                  : isDone
                  ? 'bg-slate-900/60 border-emerald-500/40 text-slate-300'
                  : isErr
                  ? 'bg-slate-900/60 border-rose-500/40 text-rose-300'
                  : 'bg-slate-900/30 border-slate-800 text-slate-500 opacity-60'
              }`}
            >
              {/* Header inside card */}
              <div className="flex items-center justify-between mb-3">
                <div
                  className={`p-2 rounded-lg ${
                    isCurrent
                      ? 'bg-cyan-500/20 text-cyan-400'
                      : isDone
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : isErr
                      ? 'bg-rose-500/20 text-rose-400'
                      : 'bg-slate-800 text-slate-500'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                </div>

                {/* Status indicator */}
                <div>
                  {isCurrent && (
                    <div className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 text-[10px] font-bold animate-pulse">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      <span>RUNNING</span>
                    </div>
                  )}
                  {isDone && (
                    <div className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-bold">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>DONE</span>
                    </div>
                  )}
                  {isErr && (
                    <div className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[10px] font-bold">
                      <AlertCircle className="w-3 h-3" />
                      <span>ERROR</span>
                    </div>
                  )}
                  {step.status === 'pending' && (
                    <div className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-slate-800 text-slate-500 text-[10px] font-medium">
                      <Clock className="w-3 h-3" />
                      <span>PENDING</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Title and Role */}
              <div className="mt-1">
                <div className="flex items-center space-x-1">
                  <span className="text-[10px] font-mono uppercase text-slate-400">
                    Шаг {idx + 1}
                  </span>
                  <span className="text-[10px] text-slate-600">•</span>
                  <span className="text-[10px] font-semibold text-slate-400">
                    {step.badge}
                  </span>
                </div>
                <h4 className="text-xs font-bold text-slate-100 mt-0.5 truncate">
                  {step.name}
                </h4>
                <p className="text-[11px] text-slate-400 line-clamp-2 mt-1">
                  {step.description}
                </p>
              </div>

              {/* Connecting arrow for desktop */}
              {idx < steps.length - 1 && (
                <div className="hidden md:block absolute -right-2 top-1/2 -translate-y-1/2 z-10">
                  <div className="w-4 h-4 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-400">
                    <ArrowRight className="w-2.5 h-2.5" />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
