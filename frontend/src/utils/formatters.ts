/**
 * Utility functions for formatting numbers, currencies in KZT (₸), and dates.
 */

export function formatCurrencyKZT(amount?: number | null): string {
  if (amount === undefined || amount === null || isNaN(amount)) {
    return '0.00 ₸';
  }
  return new Intl.NumberFormat('ru-KZ', {
    style: 'decimal',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount) + ' ₸';
}

export function formatNumber(value?: number | null, decimals = 1): string {
  if (value === undefined || value === null || isNaN(value)) {
    return '0';
  }
  return new Intl.NumberFormat('ru-RU', {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  }).format(value);
}

export function formatPercent(value?: number | null, decimals = 1): string {
  if (value === undefined || value === null || isNaN(value)) {
    return '0.0%';
  }
  return `${value.toFixed(decimals)}%`;
}

export function formatDate(dateStr?: string | null): string {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

export function getScoreColor(score: number): {
  badge: string;
  text: string;
  bg: string;
  border: string;
} {
  if (score >= 75) {
    return {
      badge: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      text: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/30',
    };
  }
  if (score >= 50) {
    return {
      badge: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      text: 'text-amber-400',
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/30',
    };
  }
  return {
    badge: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
    text: 'text-rose-400',
    bg: 'bg-rose-500/10',
    border: 'border-rose-500/30',
  };
}
