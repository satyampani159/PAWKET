// src/screens/AdviceScreen.js
import React, { useEffect, useState, useRef } from 'react';
import {
  View, Text, ScrollView, StyleSheet,
  TouchableOpacity, TextInput, KeyboardAvoidingView,
  Platform, ActivityIndicator, Keyboard, Modal, Pressable,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { getAdvice, sendChat } from '../services/api';
import useStore from '../store/useStore';
import { COLORS, FONTS, RADIUS } from '../constants/theme';
import { Loader, EmptyState } from '../components';

const INSIGHT_COLORS = {
  warning:     { bg: '#C46B6B18', border: '#C46B6B', iconName: 'warning' },
  tip:         { bg: '#C4A05C18', border: '#C4A05C', iconName: 'bulb' },
  achievement: { bg: '#5BAF8E18', border: '#5BAF8E', iconName: 'trophy' },
};

const QUICK_ACTIONS = [
  'How much did I spend this month?',
  'Where am I overspending?',
  'Am I saving enough?',
  'Show my top expenses',
  'How can I cut costs?',
  'Talk to human',
];

// Displayed above the chat so users always know they are talking to an AI,
// with a one-tap path to human support (Q4: disclosure + handoff).
const AI_DISCLOSURE = 'You are chatting with Pawket AI (not a human). Say "Talk to human" anytime for human support.';

export default function AdviceScreen() {
  const { selectedMonth, advice, setAdvice, chatMessages, addChatMessage } = useStore();
  const [loading, setLoading] = useState(false);
  const [input, setInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [insightsVisible, setInsightsVisible] = useState(false);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);
  const insets = useSafeAreaInsets();
  const [kbHeight, setKbHeight] = useState(0);

  useEffect(() => { loadAdvice(); }, [selectedMonth]);

  useEffect(() => {
    const showEvt = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvt = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';
    const showSub = Keyboard.addListener(showEvt, (e) => {
      const h = e?.endCoordinates?.height ?? 0;
      setKbHeight(h);
      setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);
    });
    const hideSub = Keyboard.addListener(hideEvt, () => setKbHeight(0));
    return () => { showSub.remove(); hideSub.remove(); };
  }, []);

  async function loadAdvice() {
    setLoading(true);
    try {
      const data = await getAdvice(selectedMonth);
      setAdvice(data);
    } catch (e) {
      console.warn(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function sendMessage(text) {
    const msg = text || input.trim();
    if (!msg || chatLoading) return;

    const userMsg = { role: 'user', text: msg };
    const history = [...chatMessages, userMsg].slice(-10);
    addChatMessage(userMsg);
    setInput('');
    setChatLoading(true);

    try {
      const reply = await sendChat(msg, selectedMonth, history);
      const replyText = typeof reply === 'string' ? reply : String(reply?.reply ?? '');
      addChatMessage({
        role: 'bot',
        text: replyText || 'Sorry, I couldn\'t process that. Please try again.',
      });
    } catch (e) {
      addChatMessage({ role: 'bot', text: 'Sorry, I couldn\'t process that. Please try again.' });
    } finally {
      setChatLoading(false);
      setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);
    }
  }

  const insights = advice?.insights || [];
  const keyboardOpen = kbHeight > 0;

  // Input bar sticks just above the keyboard on both platforms:
  // - iOS: KeyboardAvoidingView (padding) already lifts the bar, so only add a small gutter.
  // - Android: KeyboardAvoidingView does nothing, so pad manually by the keyboard height.
  const baseBottom = Math.max(insets.bottom, 10);
  const inputBarPaddingBottom =
    Platform.OS === 'ios'
      ? (keyboardOpen ? 8 : baseBottom)
      : (keyboardOpen ? kbHeight + 8 : baseBottom);

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      {/* Top bar: month + insights button */}
      <View style={styles.topBar}>
        <View style={styles.monthBadge}>
          <Ionicons name="calendar-outline" size={14} color={COLORS.accent} />
          <Text style={styles.monthBadgeText}>
            {new Date(selectedMonth + '-01').toLocaleString('en-IN', { month: 'long', year: 'numeric' })}
          </Text>
        </View>

        <TouchableOpacity
          style={styles.insightsBtn}
          onPress={() => setInsightsVisible(true)}
          activeOpacity={0.7}
        >
          <Ionicons name="bulb" size={15} color={COLORS.accent} />
          <Text style={styles.insightsBtnText}>Insights</Text>
          {loading ? (
            <ActivityIndicator size="small" color={COLORS.accent} />
          ) : (
            <View style={styles.countBadge}>
              <Text style={styles.countBadgeText}>{insights.length}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      {/* Chat takes the full remaining space */}
      <ScrollView
        ref={scrollRef}
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        onContentSizeChange={() => scrollRef.current?.scrollToEnd({ animated: false })}
      >
        {/* Chat header */}
        <View style={styles.aiBadgeRow}>
          <View style={styles.aiBadge}>
            <Text style={styles.aiBadgeText}>AI</Text>
          </View>
          <Text style={styles.chatSubtitle}>{AI_DISCLOSURE}</Text>
        </View>

        {/* Messages */}
        {chatMessages.length === 0 && !chatLoading ? (
          <View style={styles.welcomeWrap}>
            <View style={styles.welcomeIcon}>
              <Ionicons name="paw" size={28} color={COLORS.accent} />
            </View>
            <Text style={styles.welcomeTitle}>Ask Pawket anything</Text>
            <Text style={styles.welcomeSub}>
              Spending, saving, budgets — I answer from your transactions.
            </Text>
          </View>
        ) : null}

        {chatMessages.map((msg, i) => (
          <View key={i} style={[styles.msgBubble, msg.role === 'user' ? styles.msgUser : styles.msgBot]}>
            {msg.role === 'bot' && (
              <View style={styles.botAvatar}>
                <Ionicons name="paw" size={14} color={COLORS.accent} />
              </View>
            )}
            <View style={[styles.msgContent, msg.role === 'user' ? styles.msgContentUser : styles.msgContentBot]}>
              <Text style={[styles.msgText, msg.role === 'user' ? styles.msgTextUser : styles.msgTextBot]}>
                {msg.text}
              </Text>
            </View>
          </View>
        ))}

        {chatLoading && (
          <View style={[styles.msgBubble, styles.msgBot]}>
            <View style={styles.botAvatar}>
              <Ionicons name="paw" size={14} color={COLORS.accent} />
            </View>
            <View style={[styles.msgContent, styles.msgContentBot]}>
              <ActivityIndicator size="small" color={COLORS.accent} />
            </View>
          </View>
        )}

        {/* Quick actions */}
        {chatMessages.length === 0 && (
          <View style={styles.quickActions}>
            {QUICK_ACTIONS.map((q, i) => (
              <TouchableOpacity key={i} style={styles.quickChip} onPress={() => sendMessage(q)} activeOpacity={0.7}>
                <Text style={styles.quickChipText}>{q}</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        <View style={{ height: 20 }} />
      </ScrollView>

      {/* Input bar — pinned just above the keyboard */}
      <View style={[styles.inputBar, { paddingBottom: inputBarPaddingBottom }]}>
        <View style={styles.inputWrap}>
          <TextInput
            ref={inputRef}
            style={styles.textInput}
            value={input}
            onChangeText={setInput}
            placeholder="Ask about your spending..."
            placeholderTextColor={COLORS.textMuted}
            returnKeyType="send"
            multiline
            maxLength={500}
            onSubmitEditing={() => sendMessage()}
            blurOnSubmit={false}
          />
          <TouchableOpacity
            style={[styles.sendBtn, (!input.trim() || chatLoading) && styles.sendBtnDisabled]}
            onPress={() => sendMessage()}
            disabled={!input.trim() || chatLoading}
            activeOpacity={0.7}
          >
            <View style={styles.sendBtnSolid}>
              <Ionicons name="arrow-up" size={20} color="#fff" />
            </View>
          </TouchableOpacity>
        </View>
      </View>

      {/* Insights bottom sheet */}
      <Modal
        visible={insightsVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setInsightsVisible(false)}
      >
        <Pressable style={styles.overlay} onPress={() => setInsightsVisible(false)} />
        <View style={[styles.sheet, { paddingBottom: Math.max(insets.bottom, 16) }]}>
          <View style={styles.sheetHandle} />
          <View style={styles.sheetHeader}>
            <Text style={styles.sheetTitle}>
              Insights{insights.length > 0 ? ` (${insights.length})` : ''}
            </Text>
            <TouchableOpacity
              style={styles.sheetClose}
              onPress={() => setInsightsVisible(false)}
              activeOpacity={0.7}
            >
              <Ionicons name="close" size={20} color={COLORS.textSecondary} />
            </TouchableOpacity>
          </View>
          <ScrollView
            style={styles.sheetScroll}
            contentContainerStyle={styles.sheetScrollContent}
            showsVerticalScrollIndicator={false}
          >
            {loading ? (
              <Loader text="Analysing your finances..." />
            ) : insights.length > 0 ? (
              insights.map((ins, i) => {
                const st = INSIGHT_COLORS[ins.type] || INSIGHT_COLORS.tip;
                return (
                  <View key={i} style={[styles.insightCard, { backgroundColor: st.bg, borderLeftColor: st.border }]}>
                    <Ionicons name={st.iconName} size={20} color={st.border} style={{ marginTop: 2 }} />
                    <View style={styles.insightContent}>
                      <Text style={styles.insightTitle} numberOfLines={2} adjustsFontSizeToFit>{ins.title}</Text>
                      <Text style={styles.insightMsg} numberOfLines={4} adjustsFontSizeToFit>{ins.message}</Text>
                    </View>
                  </View>
                );
              })
            ) : (
              <EmptyState iconName="bulb-outline" title="No insights yet" sub="Add transactions to see financial insights." />
            )}
          </ScrollView>
        </View>
      </Modal>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root:   { flex: 1, backgroundColor: COLORS.bg },

  topBar: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingTop: 12, paddingBottom: 8,
  },
  monthBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: COLORS.bgCard, borderRadius: RADIUS.full,
    paddingHorizontal: 14, paddingVertical: 8, alignSelf: 'flex-start',
  },
  monthBadgeText: { color: COLORS.textSecondary, fontSize: 13, ...FONTS.medium },

  insightsBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: COLORS.accentSoft, borderRadius: RADIUS.full,
    borderWidth: 1, borderColor: COLORS.accent + '40',
    paddingHorizontal: 14, paddingVertical: 8,
  },
  insightsBtnText: { color: COLORS.textPrimary, fontSize: 13, ...FONTS.bold },
  countBadge: {
    backgroundColor: COLORS.accent, borderRadius: RADIUS.full,
    minWidth: 20, height: 20, alignItems: 'center', justifyContent: 'center',
    paddingHorizontal: 5,
  },
  countBadgeText: { color: '#fff', fontSize: 11, ...FONTS.bold },

  scroll: { flex: 1 },
  scrollContent: { padding: 16, paddingTop: 4, paddingBottom: 0, flexGrow: 1 },

  chatSubtitle: { color: COLORS.textMuted, fontSize: 12, flex: 1 },

  aiBadgeRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  aiBadge: {
    backgroundColor: COLORS.accent, borderRadius: RADIUS.full,
    paddingHorizontal: 8, paddingVertical: 2,
  },
  aiBadgeText: { color: '#fff', fontSize: 10, ...FONTS.bold },

  welcomeWrap: { alignItems: 'center', paddingVertical: 32, paddingHorizontal: 24 },
  welcomeIcon: {
    width: 56, height: 56, borderRadius: 28,
    backgroundColor: COLORS.bgElevated, alignItems: 'center', justifyContent: 'center',
    borderWidth: 1, borderColor: COLORS.border, marginBottom: 12,
  },
  welcomeTitle: { color: COLORS.textPrimary, fontSize: 17, ...FONTS.bold, marginBottom: 6, textAlign: 'center' },
  welcomeSub:   { color: COLORS.textSecondary, fontSize: 13, textAlign: 'center', lineHeight: 18 },

  msgBubble: { flexDirection: 'row', marginBottom: 10, alignItems: 'flex-end' },
  msgUser:   { justifyContent: 'flex-end' },
  msgBot:    { justifyContent: 'flex-start' },

  botAvatar: {
    width: 28, height: 28, borderRadius: 14,
    backgroundColor: COLORS.bgElevated, alignItems: 'center', justifyContent: 'center',
    marginRight: 8, borderWidth: 1, borderColor: COLORS.border,
  },

  msgContent: { maxWidth: '80%', borderRadius: RADIUS.lg, padding: 12 },
  msgContentUser: { backgroundColor: COLORS.accent, borderBottomRightRadius: 4 },
  msgContentBot:  { backgroundColor: COLORS.bgCard, borderBottomLeftRadius: 4, borderWidth: 1, borderColor: COLORS.border },

  msgText: { fontSize: 14, lineHeight: 20 },
  msgTextUser: { color: '#fff', ...FONTS.medium },
  msgTextBot:  { color: COLORS.textPrimary, ...FONTS.medium },

  quickActions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 4 },
  quickChip: {
    backgroundColor: COLORS.bgCard, borderRadius: RADIUS.full,
    borderWidth: 1, borderColor: COLORS.border,
    paddingHorizontal: 14, paddingVertical: 8,
  },
  quickChipText: { color: COLORS.textSecondary, fontSize: 12, ...FONTS.medium },

  inputBar: {
    backgroundColor: COLORS.bgCard, borderTopWidth: 1, borderTopColor: COLORS.border,
    paddingHorizontal: 16, paddingTop: 10,
  },
  inputWrap: {
    flexDirection: 'row', alignItems: 'flex-end', gap: 10,
    backgroundColor: COLORS.bgElevated, borderRadius: RADIUS.lg,
    paddingHorizontal: 12, paddingVertical: 6,
    borderWidth: 1, borderColor: COLORS.border,
  },
  textInput: {
    flex: 1, color: COLORS.textPrimary, fontSize: 15, ...FONTS.medium,
    maxHeight: 100, minHeight: 36, paddingVertical: 6,
    textAlignVertical: 'center',
  },
  sendBtn: { width: 36, height: 36, borderRadius: 18, overflow: 'hidden' },
  sendBtnDisabled: { opacity: 0.4 },
  sendBtnSolid: { flex: 1, backgroundColor: COLORS.accent, borderRadius: 18, alignItems: 'center', justifyContent: 'center' },

  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)' },
  sheet: {
    backgroundColor: COLORS.bgSheet,
    borderTopLeftRadius: 24, borderTopRightRadius: 24,
    paddingTop: 0, maxHeight: '80%',
  },
  sheetHandle: {
    width: 40, height: 4, borderRadius: 2,
    backgroundColor: COLORS.borderBright,
    alignSelf: 'center', marginTop: 12, marginBottom: 8,
  },
  sheetHeader: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 20, paddingVertical: 12,
  },
  sheetTitle: { color: COLORS.textPrimary, fontSize: 18, ...FONTS.bold },
  sheetClose: {
    width: 32, height: 32, borderRadius: 16,
    backgroundColor: COLORS.bgElevated, alignItems: 'center', justifyContent: 'center',
    borderWidth: 1, borderColor: COLORS.border,
  },
  sheetScroll: { maxHeight: 480 },
  sheetScrollContent: { paddingHorizontal: 16, paddingBottom: 24 },

  insightCard: { flexDirection: 'row', borderRadius: RADIUS.md, borderLeftWidth: 4, padding: 14, marginBottom: 10, gap: 12 },
  insightContent: { flex: 1 },
  insightTitle: { color: COLORS.textPrimary, fontSize: 14, ...FONTS.bold, marginBottom: 4 },
  insightMsg:   { color: COLORS.textSecondary, fontSize: 13, lineHeight: 18 },
});
