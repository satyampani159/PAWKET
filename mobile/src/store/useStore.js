// src/store/useStore.js
// Zustand global state — shared across all screens

import { create } from 'zustand';

const useStore = create((set, get) => ({
  // ── Selected month ──────────────────────────────────────────────────────────
  selectedMonth: new Date().toISOString().slice(0, 7), // "2024-05"
  setSelectedMonth: (month) => set({ selectedMonth: month }),

  // ── Analytics data ──────────────────────────────────────────────────────────
  analytics:     null,
  analyticsLoading: false,
  analyticsError:   null,
  setAnalytics:  (data) => set({ analytics: data, analyticsError: null }),
  setAnalyticsLoading: (v) => set({ analyticsLoading: v }),
  setAnalyticsError:   (e) => set({ analyticsError: e }),

  // ── Advice data ─────────────────────────────────────────────────────────────
  advice:        null,
  adviceLoading: false,
  setAdvice:     (data) => set({ advice: data }),
  setAdviceLoading: (v) => set({ adviceLoading: v }),

  // ── Transactions list ───────────────────────────────────────────────────────
  transactions:  [],
  txnTotal:      0,
  txnLoading:    false,
  setTransactions:  (list, total) => set({ transactions: list, txnTotal: total }),
  setTxnLoading:    (v) => set({ txnLoading: v }),

  // Update a single transaction's category (after correction)
  updateTransactionCategory: (txnId, newCategory) => set((state) => ({
    transactions: state.transactions.map((t) =>
      t.id === txnId
        ? { ...t, final_category: newCategory, is_corrected: true }
        : t
    ),
  })),

  // ── SMS import state ────────────────────────────────────────────────────────
  importProgress: null,   // { current, total, parsed, ignored, errors }
  importDone:     false,
  setImportProgress: (p) => set({ importProgress: p }),
  setImportDone:     (v) => set({ importDone: v }),

  // ── Available months ────────────────────────────────────────────────────────
  availableMonths: [],
  setAvailableMonths: (months) => set({ availableMonths: months }),

  // ── User income (for advice) ────────────────────────────────────────────────
  userIncome: null,
  setUserIncome: (income) => set({ userIncome: income }),

  // ── Chat messages ───────────────────────────────────────────────────────────
  chatMessages: [],
  addChatMessage: (msg) => set((state) => ({ chatMessages: [...state.chatMessages, msg] })),
  clearChatMessages: () => set({ chatMessages: [] }),
}));

export default useStore;
