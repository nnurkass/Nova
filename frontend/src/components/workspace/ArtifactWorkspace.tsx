import React, { useState } from 'react';
import { 
  Building2, 
  FileSpreadsheet, 
  Package, 
  ShoppingCart, 
  Coins, 
  Download, 
  FileText, 
  Maximize2, 
  Minimize2,
  ExternalLink,
  Info
} from 'lucide-react';
import { TaskResult } from '../../types';
import { TenderTab } from '../tabs/TenderTab';
import { PtoTab } from '../tabs/PtoTab';
import { StockTab } from '../tabs/StockTab';
import { PurchaseOrdersTab } from '../tabs/PurchaseOrdersTab';
import { FinancialDashboardTab } from '../tabs/FinancialDashboardTab';
import { formatCurrencyKZT, formatPercent } from '../../utils/formatters';

interface ArtifactWorkspaceProps {
  result: TaskResult | null;
  activeTab: 'tender' | 'pto' | 'stock' | 'orders' | 'financial';
  setActiveTab: (tab: 'tender' | 'pto' | 'stock' | 'orders' | 'financial') => void;
  onExport: () => void;
}

export const ArtifactWorkspace: React.FC<ArtifactWorkspaceProps> = ({
  result,
  activeTab,
  setActiveTab,
  onExport,
}) => {
  const tender = result?.selected_tender;
  const works = result?.work_list || [];
  const materials = result?.materials_list || [];
  const stockSummary = result?.stock_check?.summary;
  const orders = result?.purchase_orders || [];

  const tenderBudget = tender ? Number(tender.total_sum || 0) : 0;
  const totalOrdersKzt = orders.reduce((sum, o) => sum + Number(o.total_amount_kzt || 0), 0);
  const inStockValue = Number(stockSummary?.in_stock_covered_value || 0);
  const estMargin = Math.max(0, tenderBudget - totalOrdersKzt - inStockValue);
  const marginPct = tenderBudget > 0 ? (estMargin / tenderBudget) * 100 : 0;

  return (
    <div className="flex flex-col h-full bg-slate-950/60 rounded-2xl border border-slate-800/80 shadow-2xl relative overflow-hidden backdrop-blur-xl">
      
      {/* Top Header & Tab Navigation */}
      <div className="border-b border-slate-800/80 bg-slate-900/60 px-4 py-3 flex-shrink-0 space-y-3">
        
        {/* Title bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                Документы и расчёты
                {tender && (
                  <span className="text-[11px] font-normal px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800/50 truncate max-w-[200px]">
                    {tender.name_ru}
                  </span>
                )}
              </h2>
            </div>
          </div>

          {/* Export Button */}
          {result && (
            <button
              onClick={onExport}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 hover:border-slate-600 transition-colors shadow-sm"
              title="Экспорт в Excel / Markdown"
            >
              <Download className="w-3.5 h-3.5 text-cyan-400" />
              <span>Экспорт</span>
            </button>
          )}
        </div>

        {/* Top KPI Ribbon (if result available) */}
        {result && tender && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
            <div className="p-2 rounded-xl bg-slate-900/90 border border-slate-800/80">
              <div className="text-[10px] text-slate-400">Бюджет конкурса</div>
              <div className="text-xs font-bold text-slate-100 font-mono">
                {formatCurrencyKZT(tenderBudget)}
              </div>
            </div>

            <div className="p-2 rounded-xl bg-slate-900/90 border border-slate-800/80">
              <div className="text-[10px] text-slate-400">Смета (Раб / Мат)</div>
              <div className="text-xs font-bold text-amber-300 font-mono">
                {works.length} раб. • {materials.length} мат.
              </div>
            </div>

            <div className="p-2 rounded-xl bg-slate-900/90 border border-slate-800/80">
              <div className="text-[10px] text-slate-400">Дефицит склада</div>
              <div className="text-xs font-bold text-rose-300 font-mono">
                {stockSummary?.full_deficit || 0} поз. ({orders.length} PO)
              </div>
            </div>

            <div className="p-2 rounded-xl bg-slate-900/90 border border-slate-800/80">
              <div className="text-[10px] text-slate-400">Прогноз маржи</div>
              <div className="text-xs font-bold text-emerald-400 font-mono">
                {formatPercent(marginPct, 1)} ({formatCurrencyKZT(estMargin)})
              </div>
            </div>
          </div>
        )}

        {/* Tab switcher */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar pt-1">
          <button
            onClick={() => setActiveTab('tender')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all ${
              activeTab === 'tender'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Building2 className="w-3.5 h-3.5 text-cyan-400" />
            <span>1. Госзакупки</span>
            {tender && <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />}
          </button>

          <button
            onClick={() => setActiveTab('pto')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all ${
              activeTab === 'pto'
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-amber-400" />
            <span>2. Смета ПТО</span>
            {(works.length > 0 || materials.length > 0) && (
              <span className="px-1.5 py-0.2 rounded-full bg-amber-500/30 text-amber-200 text-[10px] font-mono">
                {works.length + materials.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('stock')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all ${
              activeTab === 'stock'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Package className="w-3.5 h-3.5 text-emerald-400" />
            <span>3. Склад</span>
            {stockSummary && (
              <span className="px-1.5 py-0.2 rounded-full bg-emerald-500/30 text-emerald-200 text-[10px] font-mono">
                {stockSummary.total_items}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('orders')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all ${
              activeTab === 'orders'
                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <ShoppingCart className="w-3.5 h-3.5 text-rose-400" />
            <span>4. Заявки (PO)</span>
            {orders.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-rose-500/30 text-rose-200 text-[10px] font-mono">
                {orders.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('financial')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all ${
              activeTab === 'financial'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Coins className="w-3.5 h-3.5 text-emerald-400" />
            <span>5. Финансы & COO</span>
          </button>
        </div>

      </div>

      {/* Main Document Content Body */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6">
        {!result ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-4 text-slate-400">
            <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500">
              <Info className="w-6 h-6" />
            </div>
            <div className="space-y-1 max-w-sm">
              <h4 className="text-sm font-semibold text-slate-300">
                Документы пока не сформированы
              </h4>
              <p className="text-xs text-slate-500 leading-relaxed">
                Напишите задачу в чате слева (например: <i>«Найди тендер на капремонт школы в Алматы»</i>), 
                и мульти-агентная система наполнит ведомости и отчеты в реальном времени.
              </p>
            </div>
          </div>
        ) : (
          <div>
            {activeTab === 'tender' && (
              <TenderTab
                tender={tender}
                allTenders={result.tenders}
              />
            )}

            {activeTab === 'pto' && (
              <PtoTab
                works={works}
                materials={materials}
              />
            )}

            {activeTab === 'stock' && (
              <StockTab
                stockCheck={result.stock_check}
              />
            )}

            {activeTab === 'orders' && (
              <PurchaseOrdersTab
                orders={orders}
              />
            )}

            {activeTab === 'financial' && (
              <FinancialDashboardTab
                tender={tender}
                stockCheck={result.stock_check}
                purchaseOrders={orders}
                executiveSummary={result.executive_summary}
                onExport={onExport}
              />
            )}
          </div>
        )}
      </div>

    </div>
  );
};
