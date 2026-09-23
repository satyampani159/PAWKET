// src/services/chartInsights.js
// Rule-based descriptive explanations for chart detail screens.

function fmt(n) {
  return `₹${Math.round(n || 0).toLocaleString('en-IN')}`;
}

function pct(n) {
  return `${Math.round(n || 0)}%`;
}

function monthLabel(m) {
  return new Date(`${m}-01`).toLocaleString('en-IN', { month: 'short', year: 'numeric' });
}

export function buildDonutDescription(breakdown = [], kpis = {}) {
  const bullets = [];
  const items = breakdown.filter((b) => (b.total || 0) > 0);
  if (items.length === 0) return ['No spending recorded for this month yet.'];

  const top = items[0];
  const label = (b) => b.category.charAt(0).toUpperCase() + b.category.slice(1);

  bullets.push(
    `${label(top)} is your biggest category — ${fmt(top.total)}, which is ${pct(top.percentage)} of everything you spent.`
  );

  if (items.length >= 3) {
    const top3 = items.slice(0, 3);
    const share = top3.reduce((s, b) => s + (b.percentage || 0), 0);
    bullets.push(
      `Your top 3 categories (${top3.map((b) => label(b)).join(', ')}) together make up ${pct(share)} of total spending.`
    );
  }

  if (kpis.total_spend) {
    bullets.push(
      `You made ${kpis.transaction_count || 0} transactions totalling ${fmt(kpis.total_spend)}, averaging ${fmt(kpis.avg_transaction)} per transaction.`
    );
  }

  if (items.length > 1) {
    const bottom = items[items.length - 1];
    bullets.push(
      `Smallest category: ${label(bottom)} at ${fmt(bottom.total)} (${pct(bottom.percentage)}).`
    );
  }

  if ((top.percentage || 0) >= 50) {
    bullets.push(
      `Heads up — over half your spending is concentrated in ${label(top)}. Cutting back here will have the biggest impact.`
    );
  } else if (items.length >= 2 && items[0].percentage < 30) {
    bullets.push('Your spending is well spread across categories — no single area dominates.');
  }

  return bullets;
}

export function buildTrend3mDescription(monthsData = {}) {
  const bullets = [];
  const monthKeys = Object.keys(monthsData).sort();
  if (monthKeys.length < 2) return ['Not enough months of data to show a trend yet.'];

  const totalsByMonth = {};
  const byCat = {};

  monthKeys.forEach((m) => {
    const bd = monthsData[m]?.category_breakdown || [];
    totalsByMonth[m] = bd.reduce((s, b) => s + (b.total || 0), 0);
    bd.forEach((b) => {
      if (!byCat[b.category]) byCat[b.category] = {};
      byCat[b.category][m] = b.total || 0;
    });
  });

  const first = monthKeys[0];
  const last = monthKeys[monthKeys.length - 1];

  const changes = Object.entries(byCat).map(([cat, vals]) => {
    const a = vals[first] || 0;
    const b = vals[last] || 0;
    const change = a > 0 ? ((b - a) / a) * 100 : b > 0 ? 100 : 0;
    return { cat, from: a, to: b, change };
  });

  const totalFirst = totalsByMonth[first] || 0;
  const totalLast = totalsByMonth[last] || 0;
  const totalChange = totalFirst > 0 ? ((totalLast - totalFirst) / totalFirst) * 100 : 0;

  bullets.push(
    `Overall spending ${totalChange >= 0 ? 'rose' : 'fell'} ${pct(Math.abs(totalChange))} from ${monthLabel(first)} (${fmt(totalFirst)}) to ${monthLabel(last)} (${fmt(totalLast)}).`
  );

  const rising = changes.filter((c) => c.change >= 15 && c.to > 0).sort((a, b) => b.change - a.change);
  const falling = changes.filter((c) => c.change <= -15).sort((a, b) => a.change - b.change);

  if (rising.length > 0) {
    const r = rising[0];
    const name = r.cat.charAt(0).toUpperCase() + r.cat.slice(1);
    bullets.push(`${name} spending is climbing fastest — up ${pct(r.change)} (${fmt(r.from)} → ${fmt(r.to)}).`);
  }
  if (falling.length > 0) {
    const f = falling[0];
    const name = f.cat.charAt(0).toUpperCase() + f.cat.slice(1);
    bullets.push(`${name} is down ${pct(Math.abs(f.change))} (${fmt(f.from)} → ${fmt(f.to)}) — nice improvement.`);
  }
  if (rising.length === 0 && falling.length === 0) {
    bullets.push('Category spending has stayed fairly stable across these months.');
  }

  const peakMonth = monthKeys.reduce((best, m) => ((totalsByMonth[m] || 0) > (totalsByMonth[best] || 0) ? m : best), monthKeys[0]);
  bullets.push(`${monthLabel(peakMonth)} was your highest-spending month in this period at ${fmt(totalsByMonth[peakMonth])}.`);

  return bullets;
}

export function buildDailyDescription(trend = []) {
  const bullets = [];
  const days = trend.slice(-20);
  if (days.length === 0) return ['No daily spend data available yet.'];

  const total = days.reduce((s, d) => s + (d.amount || 0), 0);
  const avg = total / days.length;
  const peak = days.reduce((max, d) => ((d.amount || 0) > (max.amount || 0) ? d : max), days[0]);

  bullets.push(
    `Across the last ${days.length} days you spent ${fmt(total)}, averaging ${fmt(avg)} per day.`
  );
  bullets.push(
    `Your biggest day was ${new Date(peak.date).toLocaleString('en-IN', { day: 'numeric', month: 'short' })} at ${fmt(peak.amount)}${
      peak.category ? ` (mostly ${peak.category})` : ''
    }.`
  );

  const heavy = days.filter((d) => (d.amount || 0) > avg * 1.5);
  if (heavy.length > 0) {
    bullets.push(`${heavy.length} day${heavy.length > 1 ? 's' : ''} stood out at more than 1.5× your average daily spend.`);
  }

  const catTotals = {};
  days.forEach((d) => {
    const c = d.category || 'others';
    catTotals[c] = (catTotals[c] || 0) + (d.amount || 0);
  });
  const topCat = Object.entries(catTotals).sort((a, b) => b[1] - a[1])[0];
  if (topCat) {
    const name = topCat[0].charAt(0).toUpperCase() + topCat[0].slice(1);
    bullets.push(`${name} drove most of your daily spending in this window (${fmt(topCat[1])}).`);
  }

  if (avg > 0 && days.every((d) => (d.amount || 0) <= avg * 1.5)) {
    bullets.push('Your daily spending has been consistent — no unusually large spikes.');
  }

  return bullets;
}

export function buildChartDescription(chartType, payload = {}) {
  switch (chartType) {
    case 'donut':
    case 'stacked':
      return buildDonutDescription(payload.breakdown, payload.kpis);
    case 'trend3m':
      return buildTrend3mDescription(payload.monthsData);
    case 'daily':
      return buildDailyDescription(payload.trend);
    default:
      return ['No description available for this chart.'];
  }
}
