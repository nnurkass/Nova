import React from 'react';
import { 
  ShoppingCart, 
  Truck, 
  AlertOctagon, 
  CheckCircle2, 
  Building2, 
  Clock, 
  Calendar,
  FileCheck,
  ShieldCheck
} from 'lucide-react';
import { PurchaseOrder } from '../../types';
import { formatCurrencyKZT, formatNumber } from '../../utils/formatters';

interface PurchaseOrdersTabProps {
  orders: PurchaseOrder[];
}

export const PurchaseOrdersTab: React.FC<PurchaseOrdersTabProps> = ({ orders = [] }) => {
  if (orders.length === 0) {
    return (
      <div className="glass-card rounded-2xl p-10 text-center text-slate-400">
        <ShoppingCart className="w-8 h-8 text-cyan-400 mx-auto mb-3 animate-pulse" />
        <h4 className="text-base font-semibold text-slate-200">Заявки на закупку формируются</h4>
        <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
          Отдел материально-технического снабжения формирует пакет заказов поставщикам РК со страховым запасом +10%...
        </p>
      </div>
    );
  }

  const totalAmountKZT = orders.reduce((acc, po) => acc + (po.total_amount_kzt || 0), 0);
  const urgentOrders = orders.filter((po) => po.priority === 'URGENT');

  return (
    <div className="space-y-6">
      {/* Top Banner & KPI */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="glass-card rounded-2xl p-4 border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[11px] uppercase font-bold text-slate-400">
              Сформировано заявок (PO)
            </div>
            <div className="text-2xl font-black text-slate-100 font-mono mt-0.5">
              {orders.length} <span className="text-xs font-normal text-slate-400">заказов</span>
            </div>
          </div>
          <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <ShoppingCart className="w-5 h-5" />
          </div>
        </div>

        <div className="glass-card rounded-2xl p-4 border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[11px] uppercase font-bold text-rose-400">
              Срочные позиции (URGENT)
            </div>
            <div className="text-2xl font-black text-rose-400 font-mono mt-0.5">
              {urgentOrders.length} <span className="text-xs font-normal text-slate-400">критичных</span>
            </div>
          </div>
          <div className="p-2.5 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertOctagon className="w-5 h-5" />
          </div>
        </div>

        <div className="glass-card rounded-2xl p-4 border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[11px] uppercase font-bold text-emerald-400">
              Общая сумма к закупке
            </div>
            <div className="text-xl font-black text-emerald-400 font-mono mt-0.5 truncate">
              {formatCurrencyKZT(totalAmountKZT)}
            </div>
          </div>
          <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <FileCheck className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Notice: +10% Safety Buffer */}
      <div className="p-3.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-xs text-cyan-200/90 flex items-start space-x-2.5">
        <ShieldCheck className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-cyan-300">Страховой буфер +10% применен:</span> В соответствии с регламентом ОМТС, объемы заказов увеличены на 10% для компенсации возможных срывов сроков и брака при доставке на стройплощадку.
        </div>
      </div>

      {/* Purchase Orders List */}
      <div className="space-y-4">
        {orders.map((po, idx) => {
          const isUrgent = po.priority === 'URGENT';
          const items = po.items && po.items.length > 0 ? po.items : (po.name ? [po] : []);

          return (
            <div
              key={idx}
              className={`glass-card rounded-2xl p-5 border transition-all ${
                isUrgent
                  ? 'border-rose-500/40 bg-gradient-to-r from-slate-900 via-slate-900 to-rose-950/20'
                  : 'border-slate-800 hover:border-slate-700'
              }`}
            >
              {/* Card Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
                <div className="flex items-center space-x-3">
                  <div
                    className={`p-2 rounded-xl border ${
                      isUrgent
                        ? 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                        : 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30'
                    }`}
                  >
                    <Building2 className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-bold text-slate-100 text-sm">
                        {po.order_id || `PO-${idx + 1}`}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                          isUrgent
                            ? 'bg-rose-500/20 text-rose-300 border-rose-500/40 animate-pulse'
                            : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        }`}
                      >
                        {isUrgent ? '🔴 URGENT' : '🟢 NORMAL'}
                      </span>
                    </div>
                    <div className="text-xs font-semibold text-cyan-300 mt-0.5">
                      {po.supplier_name || 'Определяется'} {po.supplier_city ? `(${po.supplier_city})` : ''}
                    </div>
                  </div>
                </div>

                {/* Amount and delivery badge */}
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-1.5 text-xs text-slate-400">
                    <Clock className="w-3.5 h-3.5 text-amber-400" />
                    <span>Срок: <strong className="text-slate-200 font-mono">{po.lead_time_days || 3} дн.</strong></span>
                  </div>
                  <div className="text-right">
                    <div className="text-[10px] text-slate-400 uppercase font-semibold">Сумма заявки</div>
                    <div className="text-base font-black font-mono text-emerald-400">
                      {formatCurrencyKZT(po.total_amount_kzt)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Items Table inside PO */}
              <div className="mt-3 overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="text-[10px] uppercase font-bold text-slate-400 bg-slate-900/60">
                    <tr>
                      <th className="px-3 py-2 rounded-l">Код</th>
                      <th className="px-3 py-2">Материал</th>
                      <th className="px-3 py-2 text-right">Потребность</th>
                      <th className="px-3 py-2 text-right">К заказу (+10%)</th>
                      <th className="px-3 py-2 text-right">Цена (KZT)</th>
                      <th className="px-3 py-2 text-right rounded-r">Сумма (KZT)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/40 font-sans">
                    {items.map((it: any, i: number) => {
                      const reqQ = it.required_quantity || it.quantity || 0;
                      const ordQ = it.order_quantity || it.quantity || 0;
                      const unitP = it.unit_price_kzt || it.price || 0;
                      const totA = it.total_amount_kzt || (ordQ * unitP);

                      return (
                        <tr key={i} className="hover:bg-slate-900/30">
                          <td className="px-3 py-2 font-mono text-cyan-400 font-semibold">{it.code || 'M-01'}</td>
                          <td className="px-3 py-2 text-slate-200 font-medium">{it.name || po.name}</td>
                          <td className="px-3 py-2 text-right font-mono text-slate-400">
                            {formatNumber(reqQ, 1)} {it.unit}
                          </td>
                          <td className="px-3 py-2 text-right font-mono font-bold text-cyan-300">
                            {formatNumber(ordQ, 1)} {it.unit}
                          </td>
                          <td className="px-3 py-2 text-right font-mono text-slate-400">
                            {formatCurrencyKZT(unitP)}
                          </td>
                          <td className="px-3 py-2 text-right font-mono font-bold text-emerald-400">
                            {formatCurrencyKZT(totA)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
