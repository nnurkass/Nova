import React, { useState } from 'react';
import { 
  TrendingUp, 
  Coins, 
  PieChart, 
  CheckCircle2, 
  FileText, 
  Copy, 
  Check, 
  Download, 
  ArrowUpRight,
  ShieldCheck,
  AlertCircle
} from 'lucide-react';
import { PurchaseOrder, StockCheck, Tender } from '../../types';
import { formatCurrencyKZT, formatPercent } from '../../utils/formatters';

interface FinancialDashboardTabProps {
  tender?: Tender | null;
  stockCheck?: StockCheck | null;
  purchaseOrders: PurchaseOrder[];
  executiveSummary?: string;
  onExport: () => void;
}

export const FinancialDashboardTab: React.FC<FinancialDashboardTabProps> = ({
  tender,
  stockCheck,
  purchaseOrders = [],
  executiveSummary = '',
  onExport,
}) => {
  const [copied, setCopied] = useState(false);

  const tenderBudget = tender ? (tender.total_sum || 0) : 0;
  const totalPurchaseCost = purchaseOrders.reduce((sum, po) => sum + (po.total_amount_kzt || 0), 0);
  const inStockValue = stockCheck?.summary?.in_stock_covered_value || 0;

  const estimatedGrossMargin = Math.max(0, tenderBudget - totalPurchaseCost - inStockValue);
  const marginPct = tenderBudget > 0 ? (estimatedGrossMargin / tenderBudget) * 100 : 0;
  const purchasePct = tenderBudget > 0 ? (totalPurchaseCost / tenderBudget) * 100 : 0;
  const stockPct = tenderBudget > 0 ? (inStockValue / tenderBudget) * 100 : 0;

  const isHighPriority = marginPct >= 25;

  const handleCopySummary = () => {
    navigator.clipboard.writeText(executiveSummary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* 4 Financial KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Tender Revenue */}
        <div className="glass-card rounded-2xl p-5 border border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase font-bold text-slate-400">Выручка (Бюджет тендера)</span>
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400">
              <Coins className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl sm:text-2xl font-black text-slate-100 font-mono mt-2">
            {formatCurrencyKZT(tenderBudget)}
          </div>
          <p className="text-[11px] text-cyan-400 mt-1 font-semibold">100% от контракта</p>
        </div>

        {/* Purchase Orders Costs */}
        <div className="glass-card rounded-2xl p-5 border border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase font-bold text-slate-400">Затраты на закупку (PO)</span>
            <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400">
              <TrendingUp className="w-4 h-4 rotate-180" />
            </div>
          </div>
          <div className="text-xl sm:text-2xl font-black text-rose-400 font-mono mt-2">
            {formatCurrencyKZT(totalPurchaseCost)}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 font-mono">
            {formatPercent(purchasePct)} от выручки
          </p>
        </div>

        {/* Stock Value */}
        <div className="glass-card rounded-2xl p-5 border border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase font-bold text-slate-400">Остатки на складе</span>
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
              <PieChart className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl sm:text-2xl font-black text-indigo-300 font-mono mt-2">
            {formatCurrencyKZT(inStockValue)}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 font-mono">
            {formatPercent(stockPct)} от выручки
          </p>
        </div>

        {/* Estimated Gross Margin */}
        <div className={`glass-card rounded-2xl p-5 border relative overflow-hidden ${
          isHighPriority
            ? 'bg-gradient-to-br from-slate-900 to-emerald-950/40 border-emerald-500/40'
            : 'bg-gradient-to-br from-slate-900 to-amber-950/40 border-amber-500/40'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase font-bold text-slate-300">Расчетная валовая маржа</span>
            <div className={`p-2 rounded-xl ${isHighPriority ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'}`}>
              <ArrowUpRight className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl sm:text-2xl font-black text-emerald-400 font-mono mt-2">
            {formatCurrencyKZT(estimatedGrossMargin)}
          </div>
          <div className="flex items-center space-x-2 mt-1">
            <span className="text-xs font-bold font-mono text-emerald-300 px-2 py-0.5 rounded-full bg-emerald-500/20">
              {formatPercent(marginPct)}
            </span>
            <span className="text-[11px] text-slate-400 font-medium">Маржинальность</span>
          </div>
        </div>

      </div>

      {/* Visual Budget Breakdown Bar */}
      <div className="glass-card rounded-2xl p-5 border border-slate-800">
        <div className="flex items-center justify-between mb-3 text-xs">
          <span className="font-bold text-slate-300 uppercase tracking-wide">
            Структура распределения бюджета проекта
          </span>
          <span className="font-mono text-slate-400">
            Итого: {formatCurrencyKZT(tenderBudget)}
          </span>
        </div>

        <div className="w-full bg-slate-950 h-5 rounded-xl overflow-hidden flex p-0.5 border border-slate-800">
          <div
            style={{ width: `${Math.max(2, purchasePct)}%` }}
            className="bg-gradient-to-r from-rose-500 to-rose-600 h-full rounded-l-lg transition-all relative group"
            title={`Внешняя закупка: ${formatCurrencyKZT(totalPurchaseCost)} (${purchasePct.toFixed(1)}%)`}
          />
          <div
            style={{ width: `${Math.max(2, stockPct)}%` }}
            className="bg-gradient-to-r from-indigo-500 to-indigo-600 h-full transition-all relative group"
            title={`Складские остатки: ${formatCurrencyKZT(inStockValue)} (${stockPct.toFixed(1)}%)`}
          />
          <div
            style={{ width: `${Math.max(2, marginPct)}%` }}
            className="bg-gradient-to-r from-emerald-500 to-teal-400 h-full rounded-r-lg transition-all relative group"
            title={`Валовая прибыль (на СМР, налоги): ${formatCurrencyKZT(estimatedGrossMargin)} (${marginPct.toFixed(1)}%)`}
          />
        </div>

        <div className="flex flex-wrap items-center justify-between gap-4 mt-3 text-xs">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-rose-500" />
            <span className="text-slate-400">Внешняя закупка:</span>
            <strong className="text-slate-200 font-mono">{formatCurrencyKZT(totalPurchaseCost)} ({purchasePct.toFixed(1)}%)</strong>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-indigo-500" />
            <span className="text-slate-400">Собственный склад:</span>
            <strong className="text-slate-200 font-mono">{formatCurrencyKZT(inStockValue)} ({stockPct.toFixed(1)}%)</strong>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-emerald-500" />
            <span className="text-slate-400">Валовая прибыль (на СМР, маржу):</span>
            <strong className="text-emerald-400 font-mono">{formatCurrencyKZT(estimatedGrossMargin)} ({marginPct.toFixed(1)}%)</strong>
          </div>
        </div>
      </div>

      {/* Decision Card */}
      <div className={`p-5 rounded-2xl border flex items-start space-x-4 ${
        isHighPriority
          ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-200'
          : 'bg-amber-950/30 border-amber-500/40 text-amber-200'
      }`}>
        <div className={`p-3 rounded-xl flex-shrink-0 ${
          isHighPriority ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
        }`}>
          {isHighPriority ? <ShieldCheck className="w-6 h-6" /> : <AlertCircle className="w-6 h-6" />}
        </div>
        <div className="flex-1 space-y-1">
          <h4 className="font-extrabold text-sm text-slate-100">
            {isHighPriority
              ? '🎯 РЕШЕНИЕ: РЕКОМЕНДОВАНО К УЧАСТИЮ В ТЕНДЕРЕ (HIGH PRIORITY)'
              : '⚠️ РЕШЕНИЕ: ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНОЕ СОГЛАСОВАНИЕ (MEDIUM PRIORITY)'}
          </h4>
          <p className="text-xs text-slate-300 leading-relaxed">
            {isHighPriority
              ? `Проект обладает высокой расчетной рентабельностью (${marginPct.toFixed(1)}%) и низкой зависимостью от дефицитных импортных материалов. Поставки обеспечены локальными дистрибьюторами РК.`
              : `Маржинальность проекта составляет ${marginPct.toFixed(1)}%. Рекомендуется оптимизировать график закупок и проверить коммерческие предложения поставщиков.`}
          </p>
        </div>
      </div>

      {/* Full Executive Summary Markdown Report */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <FileText className="w-5 h-5 text-cyan-400" />
            <h4 className="text-sm font-bold uppercase tracking-wider text-slate-200">
              Исполнительный отчет Операционного Директора (COO Report)
            </h4>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopySummary}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Скопировано' : 'Копировать'}</span>
            </button>
            <button
              onClick={onExport}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-600/20 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Экспорт отчета</span>
            </button>
          </div>
        </div>

        {/* Markdown Text Area / Render */}
        <div className="p-5 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-300 text-xs leading-relaxed font-sans whitespace-pre-wrap max-h-[500px] overflow-y-auto">
          {executiveSummary || 'Отчет еще не сформирован. Запустите мульти-агентный пайплайн...'}
        </div>
      </div>
    </div>
  );
};
