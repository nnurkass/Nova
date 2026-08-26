import React, { useState } from 'react';
import { 
  Package, 
  CheckCircle2, 
  AlertCircle, 
  XCircle, 
  Warehouse, 
  Search, 
  Coins,
  ShieldCheck
} from 'lucide-react';
import { StockCheck } from '../../types';
import { formatCurrencyKZT, formatNumber, formatPercent } from '../../utils/formatters';

interface StockTabProps {
  stockCheck?: StockCheck | null;
}

export const StockTab: React.FC<StockTabProps> = ({ stockCheck }) => {
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [search, setSearch] = useState('');

  if (!stockCheck || !stockCheck.summary) {
    return (
      <div className="glass-card rounded-2xl p-10 text-center text-slate-400">
        <Warehouse className="w-8 h-8 text-emerald-400 mx-auto mb-3 animate-pulse" />
        <h4 className="text-base font-semibold text-slate-200">Сверка остатков на складах...</h4>
        <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
          Отдел снабжения выполняет проверку складских баз РК (Склад №1, Склад №2) для расчета чистого дефицита.
        </p>
      </div>
    );
  }

  const { summary, items = {} } = stockCheck;
  const itemsList = Object.values(items);

  const filteredItems = itemsList.filter((item) => {
    const matchesSearch =
      item.name.toLowerCase().includes(search.toLowerCase()) ||
      item.code.toLowerCase().includes(search.toLowerCase());
    if (!matchesSearch) return false;
    if (filterStatus === 'IN_STOCK') return item.status === 'IN_STOCK';
    if (filterStatus === 'PARTIAL') return item.status === 'PARTIAL';
    if (filterStatus === 'DEFICIT') return item.status === 'DEFICIT';
    return true;
  });

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        
        {/* Total Checked */}
        <div className="glass-card rounded-2xl p-4 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase font-bold text-slate-400">Проверено позиций</span>
            <Package className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black text-slate-100 font-mono mt-1">
            {summary.total_items}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Номенклатура из ведомости ПТО</p>
        </div>

        {/* Fully In Stock */}
        <div className="glass-card rounded-2xl p-4 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase font-bold text-emerald-400">В наличии (100%)</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-emerald-400 font-mono mt-1">
            {summary.fully_in_stock}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Закупка не требуется</p>
        </div>

        {/* Partial */}
        <div className="glass-card rounded-2xl p-4 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase font-bold text-amber-400">Частичный остаток</span>
            <AlertCircle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black text-amber-400 font-mono mt-1">
            {summary.partial_stock}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Требуется дозаказ разницы</p>
        </div>

        {/* Deficit */}
        <div className="glass-card rounded-2xl p-4 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-[11px] uppercase font-bold text-rose-400">Полный дефицит (0%)</span>
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-black text-rose-400 font-mono mt-1">
            {summary.full_deficit}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Формируется 100% заказ в PO</p>
        </div>
      </div>

      {/* Warehouse Value Summary Card */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-950/40 via-slate-900 to-slate-900 border border-emerald-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Coins className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-400 font-medium">Оценка материалов из собственных складских запасов:</div>
            <div className="text-xl font-extrabold text-emerald-400 font-mono">
              {formatCurrencyKZT(summary.in_stock_covered_value)}
            </div>
          </div>
        </div>

        <div className="text-xs text-slate-400 sm:text-right">
          <div>Общая стоимость дефицита (к закупке):</div>
          <div className="text-sm font-bold text-rose-400 font-mono">
            {formatCurrencyKZT(summary.total_deficit_cost)}
          </div>
        </div>
      </div>

      {/* Table Container */}
      <div className="glass-card rounded-2xl p-5 border border-slate-800">
        
        {/* Controls */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 mb-4">
          <div className="flex items-center space-x-1.5 p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <button
              onClick={() => setFilterStatus('ALL')}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all ${
                filterStatus === 'ALL' ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Все ({itemsList.length})
            </button>
            <button
              onClick={() => setFilterStatus('IN_STOCK')}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all ${
                filterStatus === 'IN_STOCK' ? 'bg-emerald-500/20 text-emerald-300' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              В наличии ({summary.fully_in_stock})
            </button>
            <button
              onClick={() => setFilterStatus('PARTIAL')}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all ${
                filterStatus === 'PARTIAL' ? 'bg-amber-500/20 text-amber-300' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Частично ({summary.partial_stock})
            </button>
            <button
              onClick={() => setFilterStatus('DEFICIT')}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all ${
                filterStatus === 'DEFICIT' ? 'bg-rose-500/20 text-rose-300' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Дефицит ({summary.full_deficit})
            </button>
          </div>

          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск по материалам..."
              className="pl-8 pr-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-700 text-slate-200 text-xs placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-full sm:w-64"
            />
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-[11px] uppercase font-bold text-slate-400 bg-slate-900/80 border-b border-slate-800">
              <tr>
                <th className="px-4 py-3 rounded-l-lg">Код</th>
                <th className="px-4 py-3">Наименование материала</th>
                <th className="px-4 py-3 text-right">Потребность</th>
                <th className="px-4 py-3 text-right">На складе</th>
                <th className="px-4 py-3 text-right">Дефицит</th>
                <th className="px-4 py-3 text-center">Обеспеченность</th>
                <th className="px-4 py-3 text-center rounded-r-lg">Статус</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {filteredItems.map((item, idx) => {
                const percent = Math.min(100, Math.round(item.coverage_percent || 0));
                let statusBadge = {
                  label: 'В НАЛИЧИИ',
                  classes: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
                  bar: 'bg-emerald-500',
                };
                if (item.status === 'PARTIAL') {
                  statusBadge = {
                    label: 'ЧАСТИЧНО',
                    classes: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
                    bar: 'bg-amber-500',
                  };
                } else if (item.status === 'DEFICIT') {
                  statusBadge = {
                    label: 'ДЕФИЦИТ',
                    classes: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
                    bar: 'bg-rose-500',
                  };
                }

                return (
                  <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                    <td className="px-4 py-3 font-mono font-semibold text-cyan-400">
                      {item.code}
                    </td>
                    <td className="px-4 py-3 text-slate-200 font-medium max-w-sm">
                      {item.name}
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-bold text-slate-100">
                      {formatNumber(item.required_quantity, 1)} {item.unit}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-emerald-400 font-semibold">
                      {formatNumber(item.in_stock_quantity, 1)} {item.unit}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-rose-400 font-bold">
                      {formatNumber(item.deficit_quantity, 1)} {item.unit}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="w-24 mx-auto">
                        <div className="flex justify-between text-[10px] font-mono text-slate-400 mb-0.5">
                          <span>{percent}%</span>
                        </div>
                        <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${statusBadge.bar}`}
                            style={{ width: `${percent}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${statusBadge.classes}`}>
                        {statusBadge.label}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
