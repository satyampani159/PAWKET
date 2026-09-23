// src/screens/DashboardScreen.js
import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, ScrollView, StyleSheet,
  RefreshControl, TouchableOpacity, StatusBar,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from '@react-navigation/native';

import { getAnalytics, getTransactions, correctCategory } from '../services/api';
import useStore from '../store/useStore';
import { COLORS, FONTS, RADIUS, SHADOW, CATEGORY_META } from '../constants/theme';
import {
  KPICard, TransactionCard, CategoryIcon,
  CategoryPicker, SectionHeader, Loader, EmptyState,
} from '../components';

export default function DashboardScreen({ navigation }) {
  const {
    selectedMonth, analytics, setAnalytics,
    transactions, setTransactions,
    analyticsLoading, setAnalyticsLoading,
  } = useStore();

  const [refreshing, setRefreshing]     = useState(false);
  const [pickerVisible, setPickerVisible] = useState(false);
  const [selectedTxn, setSelectedTxn]   = useState(null);

  const load = useCallback(async () => {
    setAnalyticsLoading(true);
    try {
      const [analyticsData, txnData] = await Promise.all([
        getAnalytics(selectedMonth),
        getTransactions({ month: selectedMonth, limit: 8 }),
      ]);
      setAnalytics(analyticsData);
      setTransactions(txnData.transactions || [], txnData.total || 0);
    } catch (e) {
      console.warn('Dashboard load error:', e.message);
    } finally {
      setAnalyticsLoading(false);
    }
  }, [selectedMonth]);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  const handleCorrect = (txn) => { setSelectedTxn(txn); setPickerVisible(true); };

  const handleCategorySelect = async (category) => {
    setPickerVisible(false);
    if (!selectedTxn) return;
    try {
      await correctCategory(selectedTxn.id, category);
      useStore.getState().updateTransactionCategory(selectedTxn.id, category);
    } catch (e) {
      console.warn('Correction error:', e.message);
    }
  };

  const kpis = analytics?.kpis || {};
  const breakdown = analytics?.category_breakdown || [];
  const topCategory = breakdown[0];

  if (analyticsLoading && !analytics) return <Loader text="Loading your finances..." />;

  return (
    <View style={styles.root}>
      <StatusBar barStyle="light-content" backgroundColor={COLORS.bg} />

      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={COLORS.accent} />}
        contentContainerStyle={styles.scroll}
      >
        {/* Hero card */}
        <LinearGradient
          colors={[COLORS.gradientA, COLORS.gradientB]}
          start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
          style={styles.hero}
        >
          <Text style={styles.heroLabel}>Total Spent</Text>
          <Text style={styles.heroAmount} numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.5}>
            {'\u20B9'}{kpis.total_spend?.toLocaleString('en-IN') || '0'}
          </Text>
          <View style={styles.heroRow}>
            <View style={styles.heroStat}>
              <Text style={styles.heroStatLabel}>Income</Text>
              <Text style={styles.heroStatValue} numberOfLines={1} adjustsFontSizeToFit>+{'\u20B9'}{kpis.total_credit?.toLocaleString('en-IN') || '0'}</Text>
            </View>
            <View style={styles.heroStatDivider} />
            <View style={styles.heroStat}>
              <Text style={styles.heroStatLabel}>Net</Text>
              <Text style={[styles.heroStatValue, { color: kpis.net >= 0 ? '#D4F5D4' : '#F5D4D4' }]} numberOfLines={1} adjustsFontSizeToFit>
                {kpis.net >= 0 ? '+' : ''}{'\u20B9'}{kpis.net?.toLocaleString('en-IN') || '0'}
              </Text>
            </View>
            <View style={styles.heroStatDivider} />
            <View style={styles.heroStat}>
              <Text style={styles.heroStatLabel}>Transactions</Text>
              <Text style={styles.heroStatValue} numberOfLines={1}>{kpis.transaction_count || 0}</Text>
            </View>
          </View>

          {/* Month selector */}
          <TouchableOpacity
            style={styles.monthBadge}
            onPress={() => navigation.navigate('Analytics')}
          >
            <Text style={styles.monthBadgeText}>
              {new Date(selectedMonth + '-01').toLocaleString('en-IN', { month: 'long', year: 'numeric' })}  {'\u25BC'}
            </Text>
          </TouchableOpacity>
        </LinearGradient>

        {/* KPI row */}
        <View style={styles.kpiRow}>
          <KPICard label="Avg/txn"   value={`\u20B9${kpis.avg_transaction?.toFixed(0) || 0}`} accent={COLORS.accent} />
          <KPICard label="Largest"   value={`\u20B9${kpis.largest_transaction?.toLocaleString('en-IN') || 0}`} accent={COLORS.transfer} />
          <KPICard label="Uncategorised" value={kpis.uncategorized_count || 0} accent={COLORS.medium} />
        </View>

        {/* Top category */}
        {topCategory && (
          <TouchableOpacity
            style={styles.topCatCard}
            onPress={() => navigation.navigate('Analytics')}
            activeOpacity={0.8}
          >
            <View style={styles.topCatLeft}>
              <CategoryIcon category={topCategory.category} size={28} />
              <View>
                <Text style={styles.topCatLabel}>Top Category</Text>
                <Text style={styles.topCatName} numberOfLines={1} adjustsFontSizeToFit>{CATEGORY_META[topCategory.category]?.label || topCategory.category}</Text>
              </View>
            </View>
            <View style={styles.topCatRight}>
              <Text style={styles.topCatAmount} numberOfLines={1} adjustsFontSizeToFit>{'\u20B9'}{topCategory.total?.toLocaleString('en-IN')}</Text>
              <Text style={styles.topCatPct}>{topCategory.percentage}% of spend</Text>
            </View>
          </TouchableOpacity>
        )}

        {/* Category ring chart (simplified bar) */}
        {breakdown.length > 0 && (
          <>
            <SectionHeader
              title="Spending Breakdown"
              right={
                <TouchableOpacity onPress={() => navigation.navigate('Analytics')}>
                  <Text style={styles.seeAll}>See all {'\u2192'}</Text>
                </TouchableOpacity>
              }
            />
            <TouchableOpacity
              activeOpacity={0.85}
              onPress={() => navigation.navigate('ChartDetail', { chartType: 'stacked' })}
            >
              <View style={styles.breakdownBar}>
                {breakdown.slice(0, 6).map((item) => {
                  const meta = CATEGORY_META[item.category] || CATEGORY_META.others;
                  return (
                    <View
                      key={item.category}
                      style={[styles.breakdownSegment, { flex: item.percentage, backgroundColor: meta.color }]}
                    />
                  );
                })}
              </View>
              <View style={styles.breakdownLegend}>
                {breakdown.slice(0, 6).map((item) => {
                  const meta = CATEGORY_META[item.category] || CATEGORY_META.others;
                  return (
                    <View key={item.category} style={styles.legendItem}>
                      <View style={[styles.legendDot, { backgroundColor: meta.color }]} />
                      <Text style={styles.legendLabel} numberOfLines={1}>{meta.label}</Text>
                      <Text style={styles.legendPct}>{item.percentage}%</Text>
                    </View>
                  );
                })}
              </View>
            </TouchableOpacity>
          </>
        )}

        {/* Recent transactions */}
        <SectionHeader
          title="Recent Transactions"
          right={
            <TouchableOpacity onPress={() => navigation.navigate('Transactions')}>
              <Text style={styles.seeAll}>See all {'\u2192'}</Text>
            </TouchableOpacity>
          }
        />

        {transactions.length === 0 ? (
          <EmptyState
            iconName="wallet-outline"
            title="No transactions yet"
            sub="Tap the + button to add your first SMS"
          />
        ) : (
          transactions.map((txn) => (
            <TransactionCard key={txn.id} txn={txn} onCorrect={handleCorrect} />
          ))
        )}

        <View style={{ height: 100 }} />
      </ScrollView>

      {/* Category correction picker */}
      <CategoryPicker
        visible={pickerVisible}
        transaction={selectedTxn}
        onSelect={handleCategorySelect}
        onClose={() => setPickerVisible(false)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root:   { flex: 1, backgroundColor: COLORS.bg },
  scroll: { padding: 16 },

  hero: {
    borderRadius: RADIUS.xl, padding: 24, marginBottom: 16,
    ...SHADOW.card,
  },
  heroLabel:  { color: 'rgba(255,255,255,0.7)', fontSize: 14, ...FONTS.medium, marginBottom: 4 },
  heroAmount: { color: '#fff', fontSize: 40, ...FONTS.black, marginBottom: 16 },
  heroRow:    { flexDirection: 'row', alignItems: 'center', marginBottom: 16 },
  heroStat:   { flex: 1, alignItems: 'center' },
  heroStatLabel: { color: 'rgba(255,255,255,0.6)', fontSize: 11, ...FONTS.medium },
  heroStatValue: { color: '#fff', fontSize: 15, ...FONTS.bold, marginTop: 2 },
  heroStatDivider: { width: 1, height: 30, backgroundColor: 'rgba(255,255,255,0.2)' },
  monthBadge: {
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(255,255,255,0.15)',
    borderRadius: RADIUS.full, paddingHorizontal: 14, paddingVertical: 6,
  },
  monthBadgeText: { color: '#fff', fontSize: 13, ...FONTS.semi },

  kpiRow: { flexDirection: 'row', marginBottom: 16 },

  topCatCard: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    backgroundColor: COLORS.bgCard, borderRadius: RADIUS.lg,
    padding: 16, marginBottom: 20, ...SHADOW.card,
  },
  topCatLeft:   { flexDirection: 'row', alignItems: 'center', gap: 12 },
  topCatLabel:  { color: COLORS.textMuted, fontSize: 11, ...FONTS.medium },
  topCatName:   { color: COLORS.textPrimary, fontSize: 16, ...FONTS.bold },
  topCatRight:  { alignItems: 'flex-end' },
  topCatAmount: { color: COLORS.textPrimary, fontSize: 18, ...FONTS.bold },
  topCatPct:    { color: COLORS.textMuted, fontSize: 11, marginTop: 2 },

  breakdownBar: {
    flexDirection: 'row', height: 10, borderRadius: RADIUS.full,
    overflow: 'hidden', marginBottom: 12,
  },
  breakdownSegment: { height: '100%' },
  breakdownLegend:  { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 20 },
  legendItem:  { flexDirection: 'row', alignItems: 'center', gap: 4 },
  legendDot:   { width: 8, height: 8, borderRadius: 4 },
  legendLabel: { color: COLORS.textSecondary, fontSize: 11 },
  legendPct:   { color: COLORS.textMuted, fontSize: 11, marginLeft: 2 },

  seeAll: { color: COLORS.accent, fontSize: 13, ...FONTS.semi },
});
