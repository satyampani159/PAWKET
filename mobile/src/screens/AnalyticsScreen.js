// src/screens/AnalyticsScreen.js
import React, { useEffect, useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet,
  TouchableOpacity, Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { getAnalytics, getMonths, getCompare } from '../services/api';
import useStore from '../store/useStore';
import { COLORS, FONTS, RADIUS, SHADOW, CATEGORY_META } from '../constants/theme';
import { SectionHeader, Loader, EmptyState, KPICard } from '../components';
import PieChart from '../components/PieChart';
import MultiLineChart from '../components/MultiLineChart';

const { width } = Dimensions.get('window');
const CHART_W = width - 32;

export default function AnalyticsScreen({ navigation }) {
  const { selectedMonth, setSelectedMonth, analytics, setAnalytics,
          availableMonths, setAvailableMonths } = useStore();

  const [loading, setLoading] = useState(false);
  const [showMonthPicker, setShowMonthPicker] = useState(false);
  const [compareData, setCompareData] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);

  useEffect(() => {
    loadMonths();
  }, []);

  useEffect(() => {
    loadAnalytics();
    loadCompare();
  }, [selectedMonth]);

  async function loadMonths() {
    try {
      const data = await getMonths();
      setAvailableMonths(data.months || []);
    } catch (e) {}
  }

  async function loadAnalytics() {
    setLoading(true);
    try {
      const data = await getAnalytics(selectedMonth);
      setAnalytics(data);
    } catch (e) {
      console.warn(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadCompare() {
    const [year, mon] = selectedMonth.split('-').map(Number);
    const months = [];
    for (let i = 0; i < 3; i++) {
      const m = mon - i;
      const y = m <= 0 ? year - 1 : year;
      const month = m <= 0 ? 12 + m : m;
      months.unshift(`${y}-${String(month).padStart(2, '0')}`);
    }
    setCompareLoading(true);
    try {
      const data = await getCompare(months);
      setCompareData(data);
    } catch (e) {
      console.warn(e.message);
    } finally {
      setCompareLoading(false);
    }
  }

  if (loading) return <Loader text="Crunching numbers..." />;

  const kpis      = analytics?.kpis || {};
  const breakdown = analytics?.category_breakdown || [];
  const trend     = analytics?.daily_trend || [];
  const merchants = analytics?.top_merchants || [];

  const maxTrend = Math.max(...trend.map((t) => t.amount), 1);

  return (
    <View style={styles.root}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scroll}>

        {/* Month selector */}
        <TouchableOpacity style={styles.monthSelector} onPress={() => setShowMonthPicker(!showMonthPicker)}>
          <View style={styles.monthPill}>
            <Ionicons name="calendar-outline" size={14} color={COLORS.accent} style={{ marginRight: 6 }} />
            <Text style={styles.monthText}>
              {new Date(selectedMonth + '-01').toLocaleString('en-IN', { month: 'long', year: 'numeric' })}
            </Text>
            <Ionicons name="chevron-down" size={14} color={COLORS.accent} style={{ marginLeft: 4 }} />
          </View>
        </TouchableOpacity>

        {showMonthPicker && (
          <View style={styles.monthList}>
            {availableMonths.map((m) => (
              <TouchableOpacity
                key={m.month}
                style={[styles.monthItem, m.month === selectedMonth && styles.monthItemActive]}
                onPress={() => { setSelectedMonth(m.month); setShowMonthPicker(false); }}
              >
                <Text style={[styles.monthItemText, m.month === selectedMonth && { color: COLORS.accent }]} numberOfLines={1} adjustsFontSizeToFit>
                  {new Date(m.month + '-01').toLocaleString('en-IN', { month: 'long', year: 'numeric' })}
                </Text>
                <Text style={styles.monthItemCount} numberOfLines={1}>{m.count} txns</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {!analytics || breakdown.length === 0 ? (
          <EmptyState iconName="bar-chart-outline" title="No data for this month" sub="Add transactions to see analytics" />
        ) : (
          <>
            {/* KPI grid */}
            <SectionHeader title="Key Numbers" />
            <View style={styles.kpiGrid}>
              <KPICard label="Total Spent"   value={`\u20B9${kpis.total_spend?.toLocaleString('en-IN')}`} accent={COLORS.accent} />
              <KPICard label="Total Received" value={`\u20B9${kpis.total_credit?.toLocaleString('en-IN')}`} accent={COLORS.high} />
            </View>
            <View style={styles.kpiGrid2}>
              <KPICard label="Avg Transaction" value={`\u20B9${kpis.avg_transaction?.toFixed(0)}`}       accent={COLORS.transfer} />
              <KPICard label="Median"           value={`\u20B9${kpis.median_transaction?.toFixed(0)}`}   accent={COLORS.shopping} />
            </View>
            <View style={styles.kpiGridSingle}>
              <KPICard label="Largest" value={`\u20B9${kpis.largest_transaction?.toLocaleString('en-IN')}`} accent={COLORS.low} />
            </View>

            {/* Spending by category - Donut Chart */}
            <SectionHeader title="Spending Breakdown" />
            <TouchableOpacity
              style={styles.chartCard}
              activeOpacity={0.85}
              onPress={() => navigation.navigate('ChartDetail', { chartType: 'donut' })}
            >
              <PieChart
                data={breakdown.map((item) => {
                  const meta = CATEGORY_META[item.category] || CATEGORY_META.others;
                  return { label: meta.label, value: item.total, color: meta.color };
                })}
                size={CHART_W > 300 ? 260 : CHART_W - 40}
                centerValue={`₹${kpis.total_spend?.toLocaleString('en-IN')}`}
                centerLabel="Total Spent"
              />
              <View style={styles.expandHint}>
                <Ionicons name="expand-outline" size={13} color={COLORS.textMuted} />
                <Text style={styles.expandText}>Tap to explore</Text>
              </View>
            </TouchableOpacity>
            <View style={{ height: 4 }} />

            {/* Category details with bars */}
            {breakdown.map((item) => {
              const meta = CATEGORY_META[item.category] || CATEGORY_META.others;
              return (
                <View key={item.category} style={styles.catCard}>
                  <View style={styles.catRow}>
                    <View style={[styles.catIconWrap, { backgroundColor: meta.color + '18' }]}>
                      <Ionicons name={meta.icon} size={20} color={meta.color} />
                    </View>
                    <View style={styles.catInfo}>
                      <View style={styles.catInfoTop}>
                        <Text style={styles.catName} numberOfLines={1} adjustsFontSizeToFit>{meta.label}</Text>
                        <Text style={styles.catAmt} numberOfLines={1} adjustsFontSizeToFit>{'\u20B9'}{item.total?.toLocaleString('en-IN')} ({item.percentage}%)</Text>
                      </View>
                      <View style={styles.catBarBg}>
                        <View style={[styles.catBarFill, { width: `${item.percentage}%`, backgroundColor: meta.color }]} />
                      </View>
                      <Text style={styles.catMeta} numberOfLines={1} adjustsFontSizeToFit>{item.count} transactions · avg {'\u20B9'}{item.avg_transaction?.toFixed(0)}</Text>
                    </View>
                  </View>
                </View>
              );
            })}

            {/* 3-Month Category Trend */}
            {compareData && compareData.months && Object.keys(compareData.months).length >= 2 && (
              <>
                <SectionHeader title="3-Month Category Trend" />
                <TouchableOpacity
                  style={styles.chartCard}
                  activeOpacity={0.85}
                  onPress={() => navigation.navigate('ChartDetail', { chartType: 'trend3m' })}
                >
                  {(() => {
                    const months = Object.keys(compareData.months).sort();
                    const monthLabels = months.map((m) => {
                      const [y, mo] = m.split('-');
                      return new Date(`${m}-01`).toLocaleString('en-IN', { month: 'short' });
                    });
                    const allCats = new Set();
                    months.forEach((m) => {
                      const breakdown = compareData.months[m]?.category_breakdown || [];
                      breakdown.forEach((b) => allCats.add(b.category));
                    });
                    const datasets = [];
                    Array.from(allCats).forEach((cat) => {
                      const meta = CATEGORY_META[cat] || CATEGORY_META.others;
                      const data = months.map((m) => {
                        const breakdown = compareData.months[m]?.category_breakdown || [];
                        const item = breakdown.find((b) => b.category === cat);
                        return { x: m, y: item?.total || 0 };
                      });
                      if (data.some((d) => d.y > 0)) {
                        datasets.push({ label: meta.label, color: meta.color, data });
                      }
                    });
                    datasets.sort((a, b) => {
                      const totalA = a.data.reduce((s, d) => s + d.y, 0);
                      const totalB = b.data.reduce((s, d) => s + d.y, 0);
                      return totalB - totalA;
                    });
                    const topDatasets = datasets.slice(0, 6);
                    return (
                      <MultiLineChart
                        datasets={topDatasets}
                        labels={monthLabels}
                        width={CHART_W}
                        height={240}
                      />
                    );
                  })()}
                  <View style={styles.expandHint}>
                    <Ionicons name="expand-outline" size={13} color={COLORS.textMuted} />
                    <Text style={styles.expandText}>Tap to explore</Text>
                  </View>
                </TouchableOpacity>
              </>
            )}

            {/* Daily spend trend */}
            {trend.length > 0 && (
              <>
                <SectionHeader title="Daily Spend Trend" />
                <TouchableOpacity
                  style={styles.trendChart}
                  activeOpacity={0.85}
                  onPress={() => navigation.navigate('ChartDetail', { chartType: 'daily' })}
                >
                  {trend.slice(-20).map((day, i) => {
                    const h = Math.max((day.amount / maxTrend) * 100, 4);
                    const meta = CATEGORY_META[day.category] || CATEGORY_META.others;
                    return (
                      <View key={day.date} style={styles.trendBar}>
                        <View style={[styles.trendFill, { height: h, backgroundColor: meta.color }]} />
                        <Text style={styles.trendDate}>
                          {new Date(day.date).getDate()}
                        </Text>
                      </View>
                    );
                  })}
                </TouchableOpacity>
                <View style={[styles.expandHint, { marginTop: -12, marginBottom: 16 }]}>
                  <Ionicons name="expand-outline" size={13} color={COLORS.textMuted} />
                  <Text style={styles.expandText}>Tap to explore</Text>
                </View>
              </>
            )}

            {/* Top merchants */}
            {merchants.length > 0 && (
              <>
                <SectionHeader title="Top Merchants" />
                {merchants.slice(0, 6).map((m, i) => (
                  <View key={m.merchant} style={styles.merchantRow}>
                    <View style={styles.merchantRank}>
                      <Text style={styles.merchantRankText}>#{i + 1}</Text>
                    </View>
                    <Text style={styles.merchantName} numberOfLines={1}>{m.merchant}</Text>
                    <View style={styles.merchantRight}>
                      <Text style={styles.merchantAmt} numberOfLines={1} adjustsFontSizeToFit>{'\u20B9'}{m.total?.toLocaleString('en-IN')}</Text>
                      <Text style={styles.merchantCount} numberOfLines={1}>{m.count}x</Text>
                    </View>
                  </View>
                ))}
              </>
            )}
          </>
        )}

        <View style={{ height: 100 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root:   { flex: 1, backgroundColor: COLORS.bg },
  scroll: { padding: 16 },

  monthSelector: { marginBottom: 16 },
  monthPill: {
    flexDirection: 'row', alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: COLORS.bgCard,
    borderRadius: RADIUS.full,
    paddingVertical: 10, paddingHorizontal: 16,
    borderWidth: 1, borderColor: COLORS.accent + '40',
  },
  monthText: { color: COLORS.textPrimary, fontSize: 15, ...FONTS.semi },

  monthList: { backgroundColor: COLORS.bgCard, borderRadius: RADIUS.lg, marginBottom: 16, overflow: 'hidden' },
  monthItem: { flexDirection: 'row', justifyContent: 'space-between', padding: 16, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  monthItemActive: { backgroundColor: COLORS.accentSoft },
  monthItemText:  { color: COLORS.textPrimary, fontSize: 14, ...FONTS.medium },
  monthItemCount: { color: COLORS.textMuted, fontSize: 12 },

  kpiGrid: { flexDirection: 'row', marginBottom: 8 },
  kpiGrid2: { flexDirection: 'row', marginBottom: 8 },
  kpiGridSingle: { marginBottom: 8 },

  chartCard: {
    backgroundColor: COLORS.bgCard,
    borderRadius: RADIUS.lg,
    padding: 16,
    marginBottom: 20,
    alignItems: 'center',
  },

  expandHint: {
    flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 8,
  },
  expandText: { color: COLORS.textMuted, fontSize: 11, ...FONTS.medium },

  catCard: {
    backgroundColor: COLORS.bgCard,
    borderRadius: RADIUS.md,
    padding: 14,
    marginBottom: 8,
  },
  catRow: { flexDirection: 'row', alignItems: 'center' },
  catIconWrap: { width: 38, height: 38, borderRadius: RADIUS.md, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  catInfo: { flex: 1 },
  catInfoTop: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 },
  catName: { color: COLORS.textPrimary, fontSize: 14, ...FONTS.semi, flex: 1, marginRight: 8 },
  catAmt:  { color: COLORS.textPrimary, fontSize: 13, ...FONTS.bold },
  catBarBg:   { height: 6, backgroundColor: COLORS.bgElevated, borderRadius: RADIUS.full, marginBottom: 4 },
  catBarFill: { height: 6, borderRadius: RADIUS.full },
  catMeta: { color: COLORS.textMuted, fontSize: 11 },

  trendChart: { flexDirection: 'row', alignItems: 'flex-end', height: 120, backgroundColor: COLORS.bgCard, borderRadius: RADIUS.lg, padding: 12, marginBottom: 20, gap: 3 },
  trendBar:   { flex: 1, alignItems: 'center', justifyContent: 'flex-end' },
  trendFill:  { width: '80%', borderRadius: 3, minHeight: 4 },
  trendDate:  { color: COLORS.textMuted, fontSize: 9, marginTop: 4 },

  merchantRow:   { flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.bgCard, borderRadius: RADIUS.md, padding: 14, marginBottom: 8 },
  merchantRank:  { width: 28, height: 28, borderRadius: 14, backgroundColor: COLORS.bgElevated, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  merchantRankText: { color: COLORS.accent, fontSize: 12, ...FONTS.bold },
  merchantName:  { flex: 1, color: COLORS.textPrimary, fontSize: 14, ...FONTS.medium },
  merchantRight: { alignItems: 'flex-end' },
  merchantAmt:   { color: COLORS.textPrimary, fontSize: 14, ...FONTS.bold },
  merchantCount: { color: COLORS.textMuted, fontSize: 11 },
});
