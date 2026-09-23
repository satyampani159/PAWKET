// src/screens/TransactionsScreen.js
import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { getTransactions, correctCategory } from '../services/api';
import useStore from '../store/useStore';
import { COLORS, FONTS, RADIUS, CATEGORY_META } from '../constants/theme';
import { TransactionCard, CategoryPicker, Loader, EmptyState } from '../components';

const ALL_CATS = ['all', ...Object.keys(CATEGORY_META)];

export default function TransactionsScreen() {
  const { selectedMonth, transactions, txnTotal, txnLoading,
          setTransactions, setTxnLoading, updateTransactionCategory } = useStore();

  const [filterCat, setFilterCat] = useState('all');
  const [page, setPage]           = useState(0);
  const [pickerVisible, setPickerVisible] = useState(false);
  const [selectedTxn, setSelectedTxn]     = useState(null);

  const LIMIT = 30;

  const load = useCallback(async (cat = filterCat, pg = 0) => {
    setTxnLoading(true);
    try {
      const data = await getTransactions({
        month:    selectedMonth,
        category: cat === 'all' ? undefined : cat,
        limit:    LIMIT,
        offset:   pg * LIMIT,
      });
      if (pg === 0) setTransactions(data.transactions || [], data.total || 0);
      else setTransactions([...transactions, ...(data.transactions || [])], data.total || 0);
    } catch (e) {
      console.warn(e.message);
    } finally {
      setTxnLoading(false);
    }
  }, [selectedMonth, filterCat]);

  useEffect(() => { setPage(0); load(filterCat, 0); }, [selectedMonth, filterCat]);

  const handleCorrect = (txn) => { setSelectedTxn(txn); setPickerVisible(true); };

  const handleCategorySelect = async (category) => {
    setPickerVisible(false);
    if (!selectedTxn) return;
    try {
      await correctCategory(selectedTxn.id, category);
      updateTransactionCategory(selectedTxn.id, category);
    } catch (e) { console.warn(e.message); }
  };

  const loadMore = () => {
    if (transactions.length < txnTotal && !txnLoading) {
      const next = page + 1;
      setPage(next);
      load(filterCat, next);
    }
  };

  return (
    <View style={styles.root}>
      {/* Category filter chips */}
      <FlatList
        data={ALL_CATS}
        horizontal
        showsHorizontalScrollIndicator={false}
        keyExtractor={(k) => k}
        contentContainerStyle={styles.chips}
        renderItem={({ item }) => {
          const active = filterCat === item;
          const meta   = CATEGORY_META[item];
          return (
            <TouchableOpacity
              style={[styles.chip, active && { backgroundColor: meta?.color || COLORS.accent, borderColor: 'transparent' }]}
              onPress={() => setFilterCat(item)}
            >
              {meta ? (
                <Ionicons
                  name={meta.icon}
                  size={14}
                  color={active ? '#fff' : meta.color}
                  style={{ marginRight: 4 }}
                />
              ) : null}
              <Text style={[styles.chipText, active && { color: '#fff' }]} numberOfLines={1} adjustsFontSizeToFit>
                {meta ? meta.label : 'All'}
              </Text>
            </TouchableOpacity>
          );
        }}
        style={styles.filterRow}
      />

      {/* Summary bar */}
      <View style={styles.summaryBar}>
        <Text style={[styles.summaryText, { flex: 1 }]} numberOfLines={1} adjustsFontSizeToFit>{txnTotal} transactions</Text>
        <Text style={[styles.summaryText, { flex: 1, textAlign: 'right' }]} numberOfLines={1} adjustsFontSizeToFit>{filterCat !== 'all' ? CATEGORY_META[filterCat]?.label : 'All categories'}</Text>
      </View>

      {/* List */}
      {txnLoading && transactions.length === 0 ? (
        <Loader text="Loading transactions..." />
      ) : transactions.length === 0 ? (
        <EmptyState iconName="search-outline" title="No transactions found" sub="Try a different filter or month" />
      ) : (
        <FlatList
          data={transactions}
          keyExtractor={(t) => String(t.id)}
          contentContainerStyle={styles.list}
          renderItem={({ item }) => (
            <TransactionCard txn={item} onCorrect={handleCorrect} />
          )}
          onEndReached={loadMore}
          onEndReachedThreshold={0.3}
          ListFooterComponent={
            txnLoading ? <Loader /> : transactions.length < txnTotal
              ? <Text style={styles.loadMore}>Loading more...</Text>
              : <Text style={styles.endText}>All caught up</Text>
          }
        />
      )}

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
  root:       { flex: 1, backgroundColor: COLORS.bg },
  filterRow:  { maxHeight: 60, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  chips:      { paddingHorizontal: 16, paddingVertical: 10, gap: 8 },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16, paddingVertical: 10,
    borderRadius: RADIUS.full, borderWidth: 1,
    borderColor: COLORS.border, backgroundColor: COLORS.bgCard,
    minHeight: 44,
  },
  chipText:   { color: COLORS.textSecondary, fontSize: 13, ...FONTS.medium },

  summaryBar: {
    flexDirection: 'row', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 8,
    borderBottomWidth: 1, borderBottomColor: COLORS.border,
  },
  summaryText: { color: COLORS.textMuted, fontSize: 12 },

  list:     { padding: 16 },
  loadMore: { textAlign: 'center', color: COLORS.textMuted, padding: 16 },
  endText:  { textAlign: 'center', color: COLORS.accent, padding: 16, fontSize: 13 },
});
