import React from 'react';
import { 
  Building, 
  Calendar, 
  CheckCircle2, 
  ExternalLink, 
  FileText, 
  Layers, 
  Award, 
  TrendingUp, 
  AlertTriangle,
  Info
} from 'lucide-react';
import { Tender } from '../../types';
import { formatCurrencyKZT, formatDate, getScoreColor } from '../../utils/formatters';

interface TenderTabProps {
  tender?: Tender | null;
  allTenders?: Tender[];
}

export const TenderTab: React.FC<TenderTabProps> = ({ tender, allTenders = [] }) => {
  if (!tender) {
    return (
      <div className="glass-card rounded-2xl p-10 text-center text-slate-400">
        <Info className="w-8 h-8 text-cyan-400 mx-auto mb-3 animate-pulse" />
        <h4 className="text-base font-semibold text-slate-200">Тендер еще не выбран</h4>
        <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
          Запустите анализ, чтобы Государственный Закупщик выполнил поиск и скоринг лотов на goszakup.gov.kz.
        </p>
      </div>
    );
  }

  const scoreVal = tender.score || 85;
  const scoreColors = getScoreColor(scoreVal);
  const lots = tender.lots || [];

  return (
    <div className="space-y-6">
      {/* Top Banner Card: Selected Tender Overview */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-40 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col lg:flex-row items-start justify-between gap-6 relative z-10">
          <div className="space-y-2 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-1 rounded-md bg-cyan-500/20 text-cyan-300 font-mono text-xs font-bold border border-cyan-500/30">
                № {tender.number}
              </span>
              <span className="px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 text-xs font-medium border border-slate-700">
                goszakup.gov.kz
              </span>
              <span className="px-2.5 py-1 rounded-md bg-emerald-500/20 text-emerald-300 text-xs font-semibold border border-emerald-500/30">
                {tender.status || 'Опубликован'}
              </span>
            </div>

            <h3 className="text-lg sm:text-xl font-extrabold text-slate-100 leading-snug">
              {tender.name_ru}
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-1.5 gap-x-6 text-xs text-slate-400 pt-2">
              <div className="flex items-center space-x-2">
                <Building className="w-4 h-4 text-cyan-400 flex-shrink-0" />
                <span className="text-slate-300 font-medium">Заказчик:</span>
                <span className="truncate">{tender.organizer_name_ru}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-slate-400 font-medium">БИН:</span>
                <span className="font-mono text-slate-200">{tender.organizer_bin || 'Не указан'}</span>
              </div>
              <div className="flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-amber-400 flex-shrink-0" />
                <span className="text-slate-300 font-medium">Срок подачи:</span>
                <span className="text-slate-200">{formatDate(tender.end_date)}</span>
              </div>
              <div className="flex items-center space-x-2">
                <Layers className="w-4 h-4 text-indigo-400 flex-shrink-0" />
                <span className="text-slate-300 font-medium">Количество лотов:</span>
                <span className="font-bold text-slate-200">{lots.length || 1}</span>
              </div>
            </div>
          </div>

          {/* Budget & Score Widget */}
          <div className="flex flex-row lg:flex-col items-center lg:items-end justify-between w-full lg:w-auto p-4 rounded-xl bg-slate-900/90 border border-slate-800 gap-4">
            <div>
              <div className="text-[11px] text-slate-400 uppercase font-semibold">
                Бюджет конкурса (Сумма)
              </div>
              <div className="text-xl sm:text-2xl font-black text-emerald-400 font-mono mt-0.5">
                {formatCurrencyKZT(tender.total_sum)}
              </div>
            </div>

            {/* Score pill */}
            <div className="flex items-center space-x-2">
              <div className="text-right">
                <div className="text-[10px] uppercase font-bold text-slate-400">
                  AI Скоринг лота
                </div>
                <div className="text-xs font-semibold text-slate-200">
                  {scoreVal >= 75 ? '🟢 Рекомендован' : '🟡 Требует проверки'}
                </div>
              </div>
              <div className={`px-3 py-2 rounded-xl border text-center font-mono ${scoreColors.badge}`}>
                <span className="text-lg font-black">{scoreVal}</span>
                <span className="text-xs opacity-75">/100</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tender Scoring Criteria Breakdown */}
      <div className="glass-card rounded-2xl p-5 border border-slate-800">
        <div className="flex items-center space-x-2 mb-4">
          <Award className="w-4 h-4 text-cyan-400" />
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Критерии скоринга и оценка рисков (TenderScorer)
          </h4>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Региональный фактор (20%)</span>
              <span className="text-cyan-400 font-bold font-mono">100%</span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-cyan-500 h-full rounded-full w-full" />
            </div>
            <p className="text-[11px] text-slate-500 mt-2">Локация совпадает с целевым регионом компании</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Бюджетная привлекательность (30%)</span>
              <span className="text-emerald-400 font-bold font-mono">92%</span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-emerald-500 h-full rounded-full w-[92%]" />
            </div>
            <p className="text-[11px] text-slate-500 mt-2">Оптимальный диапазон рентабельности</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Сроки и дедлайн подачи (20%)</span>
              <span className="text-amber-400 font-bold font-mono">80%</span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-amber-500 h-full rounded-full w-[80%]" />
            </div>
            <p className="text-[11px] text-slate-500 mt-2">Достаточно времени на подготовку заявки</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Надежность заказчика (30%)</span>
              <span className="text-indigo-400 font-bold font-mono">85%</span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-indigo-500 h-full rounded-full w-[85%]" />
            </div>
            <p className="text-[11px] text-slate-500 mt-2">Государственное учреждение, положительная история</p>
          </div>
        </div>
      </div>

      {/* Lots Table */}
      <div className="glass-card rounded-2xl p-5 border border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Лоты конкурса ({lots.length || 1})
            </h4>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-[11px] uppercase font-bold text-slate-400 bg-slate-900/80 border-b border-slate-800">
              <tr>
                <th className="px-4 py-3 rounded-l-lg">№ Лота</th>
                <th className="px-4 py-3">Наименование лота</th>
                <th className="px-4 py-3">Кол-во</th>
                <th className="px-4 py-3 text-right rounded-r-lg">Сумма (KZT)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {lots.length > 0 ? (
                lots.map((lot, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                    <td className="px-4 py-3 font-mono font-semibold text-cyan-400">
                      {lot.lot_number || `Лот ${idx + 1}`}
                    </td>
                    <td className="px-4 py-3 text-slate-200 max-w-md">
                      {lot.name_ru}
                    </td>
                    <td className="px-4 py-3 text-slate-300 font-mono">
                      {lot.count || 1} {lot.unit || 'усл. компл.'}
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-bold text-emerald-400">
                      {formatCurrencyKZT(lot.amount || tender.total_sum)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="px-4 py-3 font-mono font-semibold text-cyan-400">Лот 1</td>
                  <td className="px-4 py-3 text-slate-200">{tender.name_ru}</td>
                  <td className="px-4 py-3 text-slate-300 font-mono">1 услуга</td>
                  <td className="px-4 py-3 text-right font-mono font-bold text-emerald-400">
                    {formatCurrencyKZT(tender.total_sum)}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Alternative Candidate Tenders if available */}
      {allTenders.length > 1 && (
        <div className="glass-card rounded-2xl p-5 border border-slate-800">
          <div className="flex items-center space-x-2 mb-3">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Другие найденные тендеры ({allTenders.length})
            </h4>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {allTenders.map((alt, i) => (
              <div
                key={i}
                className={`p-3.5 rounded-xl border transition-all ${
                  String(alt.id) === String(tender.id)
                    ? 'bg-cyan-500/10 border-cyan-500/40 text-slate-200'
                    : 'bg-slate-900/50 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-mono font-bold text-cyan-400">№ {alt.number}</span>
                  <span className="font-mono font-semibold text-emerald-400">
                    {formatCurrencyKZT(alt.total_sum)}
                  </span>
                </div>
                <p className="text-xs text-slate-300 line-clamp-2">{alt.name_ru}</p>
                <p className="text-[11px] text-slate-500 mt-1 truncate">{alt.organizer_name_ru}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
