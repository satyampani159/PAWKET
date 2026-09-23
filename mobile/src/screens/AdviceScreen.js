// src/screens/AdviceScreen.js
import React, { useEffect, useState, useRef } from 'react';
import {
  View, Text, ScrollView, StyleSheet,
  TouchableOpacity, TextInput, KeyboardAvoidingView,
  Platform, ActivityIndicator, Keyboard,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { getAdvice, sendChat } from '../services/api';
import useStore from '../store/useStore';
import { COLORS, FONTS, RADIUS, SHADOW, CATEGORY_META } from '../constants/theme';
import { SectionHeader, Loader, EmptyState } from '../components';

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
];

export default function AdviceScreen() {
  const { selectedMonth, advice, setAdvice, chatMessages, addChatMessage } = useStore();
  const [loading, setLoading] = useState(false);
  const [input, setInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);
  const insets = useSafeAreaInsets();
  const [keyboardOpen, setKeyboardOpen] = useState(false);

  useEffect(() => { loadAdvice(); }, [selectedMonth]);

  useEffect(() => {
    const showEvt = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvt = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';
    const showSub = Keyboard.addListener(showEvt, () => {
      setKeyboardOpen(true);
      setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);
    });
    const hideSub = Keyboard.addListener(hideEvt, () => setKeyboardOpen(false));
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

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        ref={scrollRef}
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* Month badge */}
        <TouchableOpacity style={styles.monthBadge}>
          <Ionicons name="calendar-outline" size={14} color={COLORS.accent} />
          <Text style={styles.monthBadgeText}>
            {new Date(selectedMonth + '-01').toLocaleString('en-IN', { month: 'long', year: 'numeric' })}
          </Text>
        </TouchableOpacity>

        {/* Insights */}
        {loading ? (
          <Loader text="Analysing your finances..." />
        ) : insights.length > 0 ? (
          <>
            <SectionHeader title="Insights" />
            {insights.map((ins, i) => {
              const style = INSIGHT_COLORS[ins.type] || INSIGHT_COLORS.tip;
              return (
                <View key={i} style={[styles.insightCard, { backgroundColor: style.bg, borderLeftColor: style.border }]}>
                  <Ionicons name={style.iconName} size={20} color={style.border} style={{ marginTop: 2 }} />
                  <View style={styles.insightContent}>
                    <Text style={styles.insightTitle} numberOfLines={2} adjustsFontSizeToFit>{ins.title}</Text>
                    <Text style={styles.insightMsg} numberOfLines={3} adjustsFontSizeToFit>{ins.message}</Text>
                  </View>
                </View>
              );
            })}
          </>
        ) : !advice || advice.message ? (
          <EmptyState iconName="bulb-outline" title="No insights yet" sub="Add transactions to see financial insights." />
        ) : null}

        {/* Chat section */}
        <SectionHeader title="Ask Pawket" />
        <Text style={styles.chatSubtitle}>Get personalized answers about your finances</Text>

        {/* Messages */}
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

      {/* Input bar */}
      <View style={[styles.inputBar, { paddingBottom: keyboardOpen ? 8 : Math.max(insets.bottom, 10) }]}>
        <View style={styles.inputWrap}>
          <TextInput
            ref={inputRef}
            style={styles.textInput}
            value={input}
            onChangeText={setInput}
            placeholder="Ask about your spending..."
            placeholderTextColor={COLORS.textMuted}
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
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root:   { flex: 1, backgroundColor: COLORS.bg },
  scroll: { flex: 1 },
  scrollContent: { padding: 16, paddingBottom: 0 },

  monthBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: COLORS.bgCard, borderRadius: RADIUS.full,
    paddingHorizontal: 14, paddingVertical: 8, alignSelf: 'flex-start', marginBottom: 16,
  },
  monthBadgeText: { color: COLORS.textSecondary, fontSize: 13, ...FONTS.medium },

  insightCard: { flexDirection: 'row', borderRadius: RADIUS.md, borderLeftWidth: 4, padding: 14, marginBottom: 10, gap: 12 },
  insightContent: { flex: 1 },
  insightTitle: { color: COLORS.textPrimary, fontSize: 14, ...FONTS.bold, marginBottom: 4 },
  insightMsg:   { color: COLORS.textSecondary, fontSize: 13, lineHeight: 18 },

  chatSubtitle: { color: COLORS.textMuted, fontSize: 12, marginBottom: 12, marginTop: -4 },

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
    paddingHorizontal: 16, paddingVertical: 10,
  },
  inputWrap: {
    flexDirection: 'row', alignItems: 'flex-end', gap: 10,
    backgroundColor: COLORS.bgElevated, borderRadius: RADIUS.lg,
    paddingHorizontal: 12, paddingVertical: 6,
    borderWidth: 1, borderColor: COLORS.border,
  },
  textInput: {
    flex: 1, color: COLORS.textPrimary, fontSize: 15, ...FONTS.medium,
    maxHeight: 100, paddingVertical: 4,
  },
  sendBtn: { width: 36, height: 36, borderRadius: 18, overflow: 'hidden' },
  sendBtnDisabled: { opacity: 0.4 },
  sendBtnSolid: { flex: 1, backgroundColor: COLORS.accent, borderRadius: 18, alignItems: 'center', justifyContent: 'center' },
});
