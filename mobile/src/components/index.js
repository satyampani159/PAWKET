// src/components/index.js
// All reusable UI components

import React from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  Modal, FlatList, Pressable, ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, CATEGORY_META, FONTS, RADIUS, SHADOW } from '../constants/theme';

// ── Category icon helper ──────────────────────────────────────────────────────
export function CategoryIcon({ category, size = 16, color }) {
  const iconName = CATEGORY_META[category]?.icon || 'ellipsis-horizontal';
  const iconColor = color || CATEGORY_META[category]?.color || COLORS.others;
  return <Ionicons name={iconName} size={size} color={iconColor} />;
}

// ── Confidence dot ────────────────────────────────────────────────────────────
export function ConfidenceDot({ tier }) {
  const color = {
    high:   COLORS.high,
    medium: COLORS.medium,
    low:    COLORS.low,
  }[tier] || COLORS.others;

  return <View style={[styles.dot, { backgroundColor: color }]} />;
}

// ── Category badge ────────────────────────────────────────────────────────────
export function CategoryBadge({ category, small = false }) {
  const meta  = CATEGORY_META[category] || CATEGORY_META.others;
  const size  = small ? styles.badgeSmall : styles.badge;
  const tsize = small ? styles.badgeTextSmall : styles.badgeText;
  const iconSize = small ? 12 : 14;

  return (
    <View style={[size, { backgroundColor: meta.color + '18', borderColor: meta.color + '40' }]}>
      <Ionicons name={meta.icon} size={iconSize} color={meta.color} style={{ marginRight: 4 }} />
      <Text style={tsize} numberOfLines={1} adjustsFontSizeToFit>{meta.label}</Text>
    </View>
  );
}

// ── Transaction card ──────────────────────────────────────────────────────────
export function TransactionCard({ txn, onCorrect }) {
  const meta   = CATEGORY_META[txn.final_category] || CATEGORY_META.others;
  const isDebit = txn.transaction_type === 'debit';
  const tier   = txn.confidence >= 0.85 ? 'high' : txn.confidence >= 0.60 ? 'medium' : 'low';

  const date = txn.received_at
    ? new Date(txn.received_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })
    : '—';

  return (
    <TouchableOpacity style={styles.txnCard} onPress={() => onCorrect && onCorrect(txn)} activeOpacity={0.75}>
      <View style={[styles.txnAccent, { backgroundColor: meta.color }]} />

      <View style={styles.txnLeft}>
        <View style={[styles.txnIcon, { backgroundColor: meta.color + '18' }]}>
          <Ionicons name={meta.icon} size={20} color={meta.color} />
        </View>
      </View>

      <View style={styles.txnMid}>
        <Text style={styles.txnMerchant} numberOfLines={1} ellipsizeMode="tail">
          {txn.merchant || 'Unknown'}
        </Text>
        <View style={styles.txnMeta}>
          <CategoryBadge category={txn.final_category} small />
          {txn.confidence != null && (
            <>
              <ConfidenceDot tier={tier} />
              <Text style={styles.txnConf} numberOfLines={1}>{Math.round(txn.confidence * 100)}%</Text>
            </>
          )}
          {txn.is_corrected && (
            <Text style={styles.correctedTag} numberOfLines={1}>edited</Text>
          )}
        </View>
        <Text style={styles.txnDate}>{date}</Text>
      </View>

      <View style={styles.txnRight}>
        <Text style={[styles.txnAmount, { color: isDebit ? COLORS.low : COLORS.high }]} numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.5}>
          {isDebit ? '-' : '+'}{'\u20B9'}{txn.amount?.toLocaleString('en-IN') || '—'}
        </Text>
        <Text style={styles.txnEdit}>tap to edit</Text>
      </View>
    </TouchableOpacity>
  );
}

// ── KPI card ──────────────────────────────────────────────────────────────────
export function KPICard({ label, value, sub, accent }) {
  return (
    <View style={[styles.kpiCard, { borderLeftWidth: 3, borderLeftColor: accent || COLORS.accent }]}>
      <Text style={styles.kpiValue} numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.4}>{value}</Text>
      <Text style={styles.kpiLabel} numberOfLines={1} adjustsFontSizeToFit>{label}</Text>
      {sub && <Text style={styles.kpiSub} numberOfLines={1}>{sub}</Text>}
    </View>
  );
}

// ── Category correction bottom sheet ─────────────────────────────────────────
export function CategoryPicker({ visible, transaction, onSelect, onClose }) {
  const categories = Object.entries(CATEGORY_META);

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <Pressable style={styles.overlay} onPress={onClose} />
      <View style={styles.sheet}>
        <View style={styles.sheetHandle} />
        <Text style={styles.sheetTitle}>Change Category</Text>
        {transaction && (
          <Text style={styles.sheetSub} numberOfLines={1} adjustsFontSizeToFit>
            {transaction.merchant || 'Unknown'} · {'\u20B9'}{transaction.amount}
          </Text>
        )}
        <FlatList
          data={categories}
          keyExtractor={([key]) => key}
          numColumns={2}
          contentContainerStyle={styles.catGrid}
          renderItem={({ item: [key, meta] }) => {
            const isActive = transaction?.final_category === key;
            return (
              <TouchableOpacity
                style={[styles.catItem, isActive && { borderColor: meta.color, backgroundColor: meta.color + '18' }]}
                onPress={() => onSelect(key)}
                activeOpacity={0.7}
              >
                <Ionicons name={meta.icon} size={24} color={isActive ? meta.color : COLORS.textSecondary} />
                <Text style={[styles.catLabel, isActive && { color: meta.color }]} numberOfLines={1} adjustsFontSizeToFit>{meta.label}</Text>
              </TouchableOpacity>
            );
          }}
        />
      </View>
    </Modal>
  );
}

// ── Section header ────────────────────────────────────────────────────────────
export function SectionHeader({ title, right }) {
  return (
    <View style={styles.sectionHeader}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {right}
    </View>
  );
}

// ── Loading spinner ───────────────────────────────────────────────────────────
export function Loader({ text }) {
  return (
    <View style={styles.loader}>
      <ActivityIndicator size="large" color={COLORS.accent} />
      {text && <Text style={styles.loaderText}>{text}</Text>}
    </View>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────
export function EmptyState({ iconName, title, sub }) {
  return (
    <View style={styles.empty}>
      <Ionicons name={iconName || 'file-tray-outline'} size={48} color={COLORS.textMuted} style={{ marginBottom: 12 }} />
      <Text style={styles.emptyTitle} numberOfLines={2} adjustsFontSizeToFit>{title}</Text>
      {sub && <Text style={styles.emptySub} numberOfLines={2} adjustsFontSizeToFit>{sub}</Text>}
    </View>
  );
}

// ── Solid button (replaces gradient) ──────────────────────────────────────────
export function GradientButton({ label, onPress, loading, small }) {
  return (
    <TouchableOpacity onPress={onPress} disabled={loading} activeOpacity={0.8}>
      <View style={[styles.solidBtn, small && styles.solidBtnSmall]}>
        {loading
          ? <ActivityIndicator color="#fff" size="small" />
          : <Text style={[styles.solidBtnText, small && styles.solidBtnTextSmall]}>{label}</Text>
        }
      </View>
    </TouchableOpacity>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  dot: { width: 7, height: 7, borderRadius: 4, marginHorizontal: 4 },

  badge: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 10, paddingVertical: 4,
    borderRadius: RADIUS.full, borderWidth: 1,
  },
  badgeSmall: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 7, paddingVertical: 2,
    borderRadius: RADIUS.full, borderWidth: 1,
  },
  badgeText: { color: COLORS.textPrimary, fontSize: 13, ...FONTS.semi },
  badgeTextSmall: { color: COLORS.textSecondary, fontSize: 11, ...FONTS.medium },

  txnCard: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: COLORS.bgCard,
    borderRadius: RADIUS.lg, marginBottom: 10,
    overflow: 'hidden', ...SHADOW.card,
  },
  txnAccent: { width: 2, alignSelf: 'stretch' },
  txnLeft:   { padding: 14 },
  txnIcon:   { width: 44, height: 44, borderRadius: RADIUS.md, alignItems: 'center', justifyContent: 'center' },
  txnMid:    { flex: 1, paddingVertical: 14 },
  txnMerchant:{ color: COLORS.textPrimary, fontSize: 15, ...FONTS.semi, marginBottom: 4 },
  txnMeta:   { flexDirection: 'row', alignItems: 'center', marginBottom: 3 },
  txnConf:   { color: COLORS.textMuted, fontSize: 10, ...FONTS.medium },
  txnDate:   { color: COLORS.textMuted, fontSize: 11 },
  correctedTag: { color: COLORS.medium, fontSize: 10, marginLeft: 6 },
  txnRight:  { padding: 14, alignItems: 'flex-end' },
  txnAmount: { fontSize: 16, ...FONTS.bold },
  txnEdit:   { color: COLORS.textMuted, fontSize: 10, marginTop: 4 },

  kpiCard: {
    flex: 1, backgroundColor: COLORS.bgCard,
    borderRadius: RADIUS.lg, padding: 16,
    margin: 5, ...SHADOW.card,
  },
  kpiValue: { color: COLORS.textPrimary, fontSize: 22, ...FONTS.black, marginBottom: 4 },
  kpiLabel: { color: COLORS.textSecondary, fontSize: 12, ...FONTS.medium },
  kpiSub:   { color: COLORS.textMuted, fontSize: 11, marginTop: 2 },

  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)' },
  sheet: {
    backgroundColor: COLORS.bgSheet,
    borderTopLeftRadius: 24, borderTopRightRadius: 24,
    paddingBottom: 40, maxHeight: '80%',
  },
  sheetHandle: {
    width: 40, height: 4, borderRadius: 2,
    backgroundColor: COLORS.borderBright,
    alignSelf: 'center', marginTop: 12, marginBottom: 16,
  },
  sheetTitle: { color: COLORS.textPrimary, fontSize: 18, ...FONTS.bold, paddingHorizontal: 20 },
  sheetSub:   { color: COLORS.textSecondary, fontSize: 13, paddingHorizontal: 20, marginTop: 4, marginBottom: 12 },

  catGrid: { paddingHorizontal: 12, paddingTop: 8 },
  catItem: {
    flex: 1, alignItems: 'center', margin: 6,
    backgroundColor: COLORS.bgElevated,
    borderRadius: RADIUS.md, padding: 14,
    borderWidth: 1, borderColor: COLORS.border,
  },
  catLabel: { color: COLORS.textSecondary, fontSize: 12, ...FONTS.medium, textAlign: 'center', marginTop: 6 },

  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, marginTop: 8 },
  sectionTitle:  { color: COLORS.textPrimary, fontSize: 17, ...FONTS.bold },

  loader:     { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 40 },
  loaderText: { color: COLORS.textSecondary, marginTop: 12, fontSize: 14 },

  empty:      { alignItems: 'center', padding: 40 },
  emptyTitle: { color: COLORS.textPrimary, fontSize: 18, ...FONTS.bold, textAlign: 'center' },
  emptySub:   { color: COLORS.textSecondary, fontSize: 14, marginTop: 8, textAlign: 'center' },

  solidBtn: { backgroundColor: COLORS.accent, borderRadius: RADIUS.full, paddingVertical: 16, paddingHorizontal: 32, alignItems: 'center' },
  solidBtnSmall: { paddingVertical: 10, paddingHorizontal: 20 },
  solidBtnText: { color: '#fff', fontSize: 16, ...FONTS.bold },
  solidBtnTextSmall: { fontSize: 13 },
});
