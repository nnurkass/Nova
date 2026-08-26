import React, { useState } from 'react';
import { 
  FileSpreadsheet, 
  Layers, 
  Boxes, 
  ShieldAlert, 
  Info, 
  Calculator,
  Search
} from 'lucide-react';
import { ABCMaterial, ABCWork } from '../../types';
import { formatCurrencyKZT, formatNumber } from '../../utils/formatters';

interface PtoTabProps {
  works: ABCWork[];
  materials: ABCMaterial[];
}

export const PtoTab: React.FC<PtoTabProps> = ({ works = [], materials = [] }) => {
  const [activeSubTab, setActiveSubTab] = useState<'works' | 'materials'>('works');
  const [searchQuery, setSearchQuery] = useState('');

  const totalWorksCost = works.reduce((acc, w) => acc + (w.quantity * (w.price || 0)), 0);
  const totalMaterialsCost = materials.reduce((acc, m) => acc + (m.quantity * (m.price || 0)), 0);

  const filteredWorks = works.filter((w) =>
    w.name.toLowerCase().includes(searchQuery.toLowerCase()) || w.code.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredMaterials = materials.filter((m) =>
    m.name.toLowerCase().includes(searchQuery.toLowerCase()) || m.code.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (works.length === 0 && materials.length === 0) {
    return (
      <div className="glass-card rounded-2xl p-10 text-center text-slate-400">
        <FileSpreadsheet className="w-8 h-8 text-amber-400 mx-auto mb-3 animate-pulse" />
        <h4 className="text-base font-semibold text-slate-200">Ведомость ПТО формируется</h4>
        <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
          Инженерный отдел ПТО проводит анализ технической спецификации конкурса и нормативов СН РК / АВС...
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="glass-card rounded-2xl p-4 border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[11px] uppercase font-semibold text-slate-400">
              Видов работ (ВОР)
            </div>
            <div className="text-2xl font-black text-slate-100 font-mono mt-0.5">
              {works.length} <span className="text-xs font-normal text-slate-400">позиций</span>
            </div>
          </div>
          <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Layers className="w-5 h-5" />
          </div>
        </div>

        <div className="glass-card rounded-2xl p-4 border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[11px] uppercase font-semibold text-slate-400">
              Номенклатура материалов
            </div>
            <div className="text-2xl font-black text-cyan-400 font-mono mt-0.5">
              {materials.length} <span className="text-xs font-normal text-slate-400">позиций</span>
            </div>
          </div>
          <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Boxes className="w-5 h-5" />
          </div>
        </div>

        <div className="glass-card rounded-2xl p-4 border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[11px] uppercase font-semibold text-slate-400">
              Оценка материалов (СН РК)
            </div>
            <div className="text-xl font-black text-emerald-400 font-mono mt-0.5 truncate">
              {formatCurrencyKZT(totalMaterialsCost)}
            </div>
          </div>
          <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Calculator className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Notice Banner: 5% Safety Reserve */}
      <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200/90 flex items-start space-x-2.5">
        <ShieldAlert className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-amber-300">Технологический запас +5% учтён:</span> Все объемы в ресурсной ведомости рассчитаны согласно строительным нормативам Республики Казахстан (СН РК) с запасом на технологические потери при СМР.
        </div>
      </div>

      {/* Main Table Container */}
      <div className="glass-card rounded-2xl p-5 border border-slate-800">
        
        {/* Navigation & Search toolbar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 mb-4">
          <div className="flex items-center space-x-2 p-1 rounded-xl bg-slate-900 border border-slate-800">
            <button
              onClick={() => setActiveSubTab('works')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                activeSubTab === 'works'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Ведомость работ (ВОР) ({works.length})
            </button>
            <button
              onClick={() => setActiveSubTab('materials')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                activeSubTab === 'materials'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Ресурсная ведомость материалов ({materials.length})
            </button>
          </div>

          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Поиск по шифру или наименованию..."
              className="pl-8 pr-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-700 text-slate-200 text-xs placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-full sm:w-64"
            />
          </div>
        </div>

        {/* Tables */}
        {activeSubTab === 'works' ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[11px] uppercase font-bold text-slate-400 bg-slate-900/80 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3 rounded-l-lg">№</th>
                  <th className="px-4 py-3">Шифр расценки</th>
                  <th className="px-4 py-3">Наименование работ (ВОР)</th>
                  <th className="px-4 py-3">Ед. изм.</th>
                  <th className="px-4 py-3 text-right">Объем</th>
                  <th className="px-4 py-3 text-right">Расценка (KZT)</th>
                  <th className="px-4 py-3 text-right rounded-r-lg">Сумма (KZT)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {filteredWorks.map((work, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                    <td className="px-4 py-3 text-slate-500 font-mono">{idx + 1}</td>
                    <td className="px-4 py-3 font-mono font-semibold text-amber-400">
                      {work.code}
                    </td>
                    <td className="px-4 py-3 text-slate-200 font-medium max-w-sm">
                      {work.name}
                    </td>
                    <td className="px-4 py-3 text-slate-300 font-mono">{work.unit}</td>
                    <td className="px-4 py-3 text-right font-mono font-bold text-slate-100">
                      {formatNumber(work.quantity)}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-slate-400">
                      {work.price ? formatCurrencyKZT(work.price) : '—'}
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-bold text-slate-200">
                      {work.price ? formatCurrencyKZT(work.quantity * work.price) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[11px] uppercase font-bold text-slate-400 bg-slate-900/80 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3 rounded-l-lg">№</th>
                  <th className="px-4 py-3">Код ресурса</th>
                  <th className="px-4 py-3">Наименование материала</th>
                  <th className="px-4 py-3">Ед. изм.</th>
                  <th className="px-4 py-3 text-right">Потребность (+5% запас)</th>
                  <th className="px-4 py-3 text-right">Цена за ед. (KZT)</th>
                  <th className="px-4 py-3 text-right rounded-r-lg">Расчетная стоимость</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {filteredMaterials.map((mat, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                    <td className="px-4 py-3 text-slate-500 font-mono">{idx + 1}</td>
                    <td className="px-4 py-3 font-mono font-semibold text-cyan-400">
                      {mat.code}
                    </td>
                    <td className="px-4 py-3 text-slate-200 font-medium max-w-sm">
                      {mat.name}
                    </td>
                    <td className="px-4 py-3 text-slate-300 font-mono">{mat.unit}</td>
                    <td className="px-4 py-3 text-right font-mono font-bold text-cyan-300">
                      {formatNumber(mat.quantity, 2)}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-slate-400">
                      {mat.price ? formatCurrencyKZT(mat.price) : '—'}
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-bold text-emerald-400">
                      {mat.price ? formatCurrencyKZT(mat.quantity * mat.price) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
