// src/screens/ChartDetailScreen.js
import React, { useEffect, useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet,
  TouchableOpacity, Dimensions, ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { getCompare, sendChat } from '../services/api';
import useStore from '../store/useStore';
import { COLORS, FONTS, RADIUS, CATEGORY_META } from '../constants/theme';
import { EmptyState } from '../components';
import PieChart from '../components/PieChart';
import MultiLineChart from '../components/MultiLineChart';
import { buildChartDescription } from '../services/chartInsights';

const { width: SCREEN_W } = Dimensions.get('window');

const TITLES = {
  donut: 'Spending Breakdown',
  stacked: 'Category Split',
  trend3m: '3-Month Category Trend',
  daily: 'Daily Spend Trend',
};

function last3Months(month) {
  const [year, mon] = month.split('-').map(Number);
  const months = [];
  for (let i = 0; i < 3; i++) {
    const m = mon - i;
    const y = m <= 0 ? year - 1 : year;
    const mo = m <= 0 ? 12 + m : m;
    months.unshift(`${y}-${String(mo).padStart(2, '0')}`);
  }
  return months;
}

export default function ChartDetailScreen({ route, navigation }) {
  const chartType = route?.params?.chartType || 'donut';
  const { selectedMonth, analytics } = useStore();
  const insets = useSafeAreaInsets();

  const [compareData, setCompareData] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiReply, setAiReply] = useState('');

  useEffect(() => {
    if (chartType !== 'trend3m') return;
    let cancelled = false;
    (async () => {
      setCompareLoading(true);
      try {
        const data = await getCompare(last3Months(selectedMonth));
        if (!cancelled) setCompareData(data);
      } catch (e) {
        if (!cancelled) setCompareData(null);
      } finally {
        if (!cancelled) setCompareLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [chartType, selectedMonth]);

  const kpis = analytics?.kpis || {};
  const breakdown = analytics?.category_breakdown || [];
  const trend = analytics?.daily_trend || [];

  let description = [];
  let hasData = breakdown.length > 0;

  if (chartType === 'donut' || chartType === 'stacked') {
    description = buildChartDescription(chartType, { breakdown, kpis });
  } else if (chartType === 'daily') {
    hasData = trend.length > 0;
    description = buildChartDescription('daily', { trend });
  } else if (chartType === 'trend3m') {
    const monthsData = compareData?.months || {};
    hasData = Object.keys(monthsData).length >= 2;
    description = buildChartDescription('trend3m', { monthsData });
  }

  async function explainWithAI() {
    if (aiLoading) return;
    setAiLoading(true);
    setAiReply('');
    try {
      const prompt = `Explain my "${TITLES[chartType]}" for ${selectedMonth} in a few descriptive sentences. Point out what stands out, anything concerning, and one actionable takeaway.`;
      const reply = await sendChat(prompt, selectedMonth, []);
      setAiReply(typeof reply === 'string' && reply ? reply : 'No response received. Please try again.');
    } catch (e) {
      setAiReply('Could not reach Pawket AI right now. Please try again.');
    } finally {
      setAiLoading(false);
    }
  }

  function renderChart() {
    const chartW = SCREEN_W - 64;

    if (chartType === 'donut' || chartType === 'stacked') {
      if (!hasData) return null;
      return (
        <PieChart
          data={breakdown.map((item) => {
            const meta = CATEGORY_META[item.category] || CATEGORY_META.others;
            return { label: meta.label, value: item.total, color: meta.color };
          })}
          size={Math.min(chartW, 320)}
          centerValue={`₹${kpis.total_spend?.toLocaleString('en-IN')}`}
          centerLabel="Total Spent"
        />
      );
    }

    if (chartType === 'trend3m') {
      if (compareLoading) {
        return <ActivityIndicator size="small" color={COLORS.accent} style={{ marginVertical: 40 }} />;
      }
      if (!hasData) return null;

      const months = Object.keys(compareData.months).sort();
      const monthLabels = months.map((m) =>
        new Date(`${m}-01`).toLocaleString('en-IN', { month: 'short' })
      );
      const allCats = new Set();
      months.forEach((m) => {
        (compareData.months[m]?.category_breakdown || []).forEach((b) => allCats.add(b.category));
      });
      const datasets = [];
      Array.from(allCats).forEach((cat) => {
        const meta = CATEGORY_META[cat] || CATEGORY_META.others;
        const data = months.map((m) => {
          const item = (compareData.months[m]?.category_breakdown || []).find((b) => b.category === cat);
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

      return (
        <MultiLineChart
          datasets={datasets.slice(0, 6)}
          labels={monthLabels}
          width={SCREEN_W - 48}
          height={300}
        />
      );
    }

    // daily
    if (trend.length === 0) return null;
    const maxTrend = Math.max(...trend.map((t) => t.amount), 1);
    return (
      <View style={styles.dailyChart}>
        {trend.slice(-20).map((day) => {
          const h = Math.max((day.amount / maxTrend) * 100, 4);
          const meta = CATEGORY_META[day.category] || CATEGORY_META.others;
          return (
            <View key={day.date} style={styles.dailyBar}>
              <View style={[styles.dailyFill, { height: `${h}%`, backgroundColor: meta.color }]} />
              <Text style={styles.dailyDate}>{new Date(day.date).getDate()}</Text>
            </View>
          );
        })}
      </View>
    );
  }

  return (
    <View style={[styles.root, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backBtn}
          activeOpacity={0.7}
          onPress={() => navigation.goBack()}
        >
          <Ionicons name="chevron-back" size={24} color={COLORS.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle} numberOfLines={1}>{TITLES[chartType] || 'Chart'}</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scroll}>
        <Text style={styles.monthText}>
          {new Date(selectedMonth + '-01').toLocaleString('en-IN', { month: 'long', year: 'numeric' })}
        </Text>

        {!hasData && chartType !== 'trend3m' ? (
          <EmptyState iconName="bar-chart-outline" title="No data for this chart" sub="Add transactions to see analytics" />
        ) : (
          <>
            {/* Enlarged chart */}
            <View style={styles.chartCard}>{renderChart()}</View>

            {/* Rule-based description */}
            <View style={styles.descCard}>
              <View style={styles.descHeader}>
                <Ionicons name="sparkles-outline" size={16} color={COLORS.accent} />
                <Text style={styles.descTitle}>What this chart tells you</Text>
              </View>
              {description.map((b, i) => (
                <View key={i} style={styles.bulletRow}>
                  <View style={styles.bulletDot} />
                  <Text style={styles.bulletText}>{b}</Text>
                </View>
              ))}
            </View>

            {/* AI explanation */}
            <View style={styles.descCard}>
              <View style={styles.descHeader}>
                <Ionicons name="chatbubble-ellipses-outline" size={16} color={COLORS.accent} />
                <Text style={styles.descTitle}>Ask Pawket AI</Text>
              </View>
              <Text style={styles.aiSub}>
                Get a smarter, personalized explanation of this chart using your full financial context.
              </Text>

              <TouchableOpacity
                style={[styles.aiBtn, aiLoading && styles.aiBtnDisabled]}
                activeOpacity={0.7}
                onPress={explainWithAI}
                disabled={aiLoading}
              >
                {aiLoading ? (
                  <ActivityIndicator size="small" color="#fff" />
                ) : (
                  <>
                    <Ionicons name="sparkles" size={16} color="#fff" />
                    <Text style={styles.aiBtnText}>
                      {aiReply ? 'Refresh AI explanation' : 'Explain with AI'}
                    </Text>
                  </>
                )}
              </TouchableOpacity>

              {aiReply !== '' && (
                <View style={styles.aiBubble}>
                  <Text style={styles.aiBubbleText}>{aiReply}</Text>
                </View>
              )}
            </View>
          </>
        )}

        <View style={{ height: insets.bottom + 40 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: COLORS.bg },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  backBtn: {
    width: 40, height: 40, borderRadius: 20,
    alignItems: 'center', justifyContent: 'center',
    backgroundColor: COLORS.bgCard,
  },
  headerTitle: { color: COLORS.textPrimary, fontSize: 17, ...FONTS.bold, flex: 1, textAlign: 'center', marginHorizontal: 8 },

  scroll: { padding: 16 },
  monthText: { color: COLORS.textSecondary, fontSize: 14, ...FONTS.medium, marginBottom: 14 },

  chartCard: {
    backgroundColor: COLORS.bgCard,
    borderRadius: RADIUS.lg,
    padding: 16,
    marginBottom: 16,
    alignItems: 'center',
  },

  descCard: {
    backgroundColor: COLORS.bgCard,
    borderRadius: RADIUS.lg,
    padding: 16,
    marginBottom: 16,
  },
  descHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  descTitle: { color: COLORS.textPrimary, fontSize: 15, ...FONTS.bold },

  bulletRow: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 10, gap: 10 },
  bulletDot: {
    width: 6, height: 6, borderRadius: 3,
    backgroundColor: COLORS.accent,
    marginTop: 7,
  },
  bulletText: { flex: 1, color: COLORS.textSecondary, fontSize: 13.5, lineHeight: 20, ...FONTS.medium },

  aiSub: { color: COLORS.textMuted, fontSize: 12.5, lineHeight: 18, marginBottom: 12, ...FONTS.medium },
  aiBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: COLORS.accent,
    borderRadius: RADIUS.full,
    paddingVertical: 12,
  },
  aiBtnDisabled: { opacity: 0.6 },
  aiBtnText: { color: '#fff', fontSize: 14, ...FONTS.semi },

  aiBubble: {
    marginTop: 12,
    backgroundColor: COLORS.bgElevated,
    borderRadius: RADIUS.md,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.accent,
    padding: 12,
  },
  aiBubbleText: { color: COLORS.textPrimary, fontSize: 13.5, lineHeight: 20, ...FONTS.medium },

  dailyChart: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    height: 220,
    backgroundColor: COLORS.bgElevated,
    borderRadius: RADIUS.md,
    padding: 12,
    gap: 3,
    width: '100%',
  },
  dailyBar: { flex: 1, alignItems: 'center', justifyContent: 'flex-end', height: '100%' },
  dailyFill: { width: '80%', borderRadius: 3, minHeight: 4 },
  dailyDate: { color: COLORS.textMuted, fontSize: 9, marginTop: 4 },
});
