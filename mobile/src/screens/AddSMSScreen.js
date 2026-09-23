// src/screens/AddSMSScreen.js
import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TextInput,
  ScrollView, Platform, Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { parseSMS } from '../services/api';
import { readSMSAndroid, processSMSBatch } from '../services/smsReader';
import { COLORS, FONTS, RADIUS, SHADOW, CATEGORY_META } from '../constants/theme';
import { GradientButton, CategoryBadge, ConfidenceDot } from '../components';

export default function AddSMSScreen() {
  const [smsText, setSmsText]     = useState('');
  const [loading, setLoading]     = useState(false);
  const [result, setResult]       = useState(null);
  const [importLoading, setImportLoading] = useState(false);
  const [importProgress, setImportProgress] = useState(null);

  async function handleParse() {
    if (!smsText.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const data = await parseSMS({ text: smsText.trim() });
      setResult(data);
    } catch (e) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleBulkImport() {
    if (Platform.OS !== 'android') {
      Alert.alert('Android Only', 'Automatic SMS reading is only available on Android. On iOS, paste your SMS manually above.');
      return;
    }

    Alert.alert(
      'Import SMS',
      'This will read your last 90 days of SMS messages and process all financial ones. Continue?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Import',
          onPress: async () => {
            setImportLoading(true);
            setImportProgress({ current: 0, total: 0, parsed: 0, ignored: 0, errors: 0 });
            try {
              const smsList = await readSMSAndroid(90);
              if (smsList.length === 0) {
                Alert.alert('No SMS Found', 'No financial SMS found in your inbox.');
                return;
              }
              const results = await processSMSBatch(smsList, parseSMS, setImportProgress);
              Alert.alert(
                'Import Complete',
                'Processed ' + smsList.length + ' messages\n' + results.parsed + ' transactions added\n' + results.ignored + ' ignored\n' + results.errors + ' errors'
              );
            } catch (e) {
              Alert.alert('Import Error', e.message);
            } finally {
              setImportLoading(false);
              setImportProgress(null);
            }
          },
        },
      ]
    );
  }

  const tier = result?.confidence >= 0.85 ? 'high' : result?.confidence >= 0.60 ? 'medium' : 'low';

  return (
    <ScrollView style={styles.root} contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">

      <Text style={styles.heading}>Add Transaction</Text>
      <Text style={styles.sub}>Paste an SMS from your bank or payment app</Text>

      <TextInput
        style={styles.input}
        value={smsText}
        onChangeText={setSmsText}
        placeholder="e.g. INR 250 debited via UPI at Swiggy..."
        placeholderTextColor={COLORS.textMuted}
        multiline
        numberOfLines={4}
        textAlignVertical="top"
      />

      <GradientButton label="Parse SMS" onPress={handleParse} loading={loading} />

      {result && (
        <View style={styles.resultCard}>
          {result.status === 'ignored' ? (
            <>
              <Ionicons name="close-circle" size={48} color={COLORS.textMuted} style={{ textAlign: 'center', marginBottom: 12 }} />
              <Text style={styles.ignoredTitle}>Not a financial SMS</Text>
              <Text style={styles.ignoredSub}>This message does not look like a bank transaction.</Text>
            </>
          ) : (
            <>
              <View style={styles.resultHeader}>
                <Text style={styles.resultStatus}>Parsed Successfully</Text>
                <View style={styles.tierRow}>
                  <ConfidenceDot tier={tier} />
                  <Text style={styles.tierText}>{Math.round((result.confidence || 0) * 100)}% confident</Text>
                </View>
              </View>

              <View style={styles.resultRow}>
                <Text style={styles.resultLabel}>Amount</Text>
                <Text style={[styles.resultValue, { color: result.transaction_type === 'debit' ? COLORS.low : COLORS.high }]}>
                  {result.transaction_type === 'debit' ? '-' : '+'}{'\u20B9'}{result.amount?.toLocaleString('en-IN') || '-'}
                </Text>
              </View>

              <View style={styles.resultRow}>
                <Text style={styles.resultLabel}>Merchant</Text>
                <Text style={styles.resultValue}>{result.merchant || '-'}</Text>
              </View>

              <View style={styles.resultRow}>
                <Text style={styles.resultLabel}>Bank</Text>
                <Text style={styles.resultValue}>{result.bank || '-'}</Text>
              </View>

              <View style={styles.resultRow}>
                <Text style={styles.resultLabel}>Category</Text>
                <CategoryBadge category={result.final_category} />
              </View>

              {result.pattern_category && (
                <View style={styles.resultRow}>
                  <Text style={styles.resultLabel}>Pattern hint</Text>
                  <Text style={[styles.resultValue, { color: COLORS.medium }]}>
                    {result.pattern_category} (amount/time)
                  </Text>
                </View>
              )}

              {result.all_scores && (
                <View style={styles.scoresSection}>
                  <Text style={styles.scoresTitle}>All Category Scores</Text>
                  {Object.entries(result.all_scores)
                    .sort((a, b) => b[1] - a[1])
                    .map(([cat, score]) => {
                      const meta = CATEGORY_META[cat] || CATEGORY_META.others;
                      return (
                        <View key={cat} style={styles.scoreRow}>
                          <View style={styles.scoreLabelRow}>
                            <Ionicons name={meta.icon} size={12} color={meta.color} style={{ marginRight: 4 }} />
                            <Text style={styles.scoreLabel}>{meta.label}</Text>
                          </View>
                          <View style={styles.scoreBarBg}>
                            <View style={[styles.scoreBarFill, { width: (score * 100) + '%', backgroundColor: meta.color }]} />
                          </View>
                          <Text style={styles.scorePct}>{(score * 100).toFixed(1)}%</Text>
                        </View>
                      );
                    })}
                </View>
              )}
            </>
          )}
        </View>
      )}

      <View style={styles.divider}>
        <View style={styles.dividerLine} />
        <Text style={styles.dividerText}>or</Text>
        <View style={styles.dividerLine} />
      </View>

      <View style={styles.importCard}>
        <View style={styles.importTitleRow}>
          <Ionicons name="phone-portrait" size={18} color={COLORS.accent} />
          <Text style={styles.importTitle}> Auto-Import from Phone</Text>
        </View>
        <Text style={styles.importSub}>
          {Platform.OS === 'android'
            ? 'Automatically read and process all financial SMS from the last 90 days.'
            : 'Auto-import is Android only. On iPhone, paste SMS messages manually above.'}
        </Text>

        {importProgress && (
          <View style={styles.progressCard}>
            <Text style={styles.progressText}>
              Processing {importProgress.current} / {importProgress.total}
            </Text>
            <Text style={styles.progressStats}>
              {importProgress.parsed} saved - {importProgress.ignored} ignored
            </Text>
          </View>
        )}

        {Platform.OS === 'android' && (
          <GradientButton
            label={importLoading ? 'Importing...' : 'Import SMS History'}
            onPress={handleBulkImport}
            loading={importLoading}
          />
        )}
      </View>

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root:    { flex: 1, backgroundColor: COLORS.bg },
  scroll:  { padding: 16 },
  heading: { color: COLORS.textPrimary, fontSize: 26, ...FONTS.black, marginBottom: 6 },
  sub:     { color: COLORS.textSecondary, fontSize: 14, marginBottom: 20 },

  input: {
    backgroundColor: COLORS.bgCard, borderRadius: RADIUS.lg,
    padding: 16, color: COLORS.textPrimary, fontSize: 14,
    borderWidth: 1, borderColor: COLORS.border,
    minHeight: 100, marginBottom: 16,
  },

  resultCard: { backgroundColor: COLORS.bgCard, borderRadius: RADIUS.lg, padding: 20, marginTop: 20, ...SHADOW.card },
  resultHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  resultStatus: { color: COLORS.high, fontSize: 14, ...FONTS.bold },
  tierRow: { flexDirection: 'row', alignItems: 'center' },
  tierText: { color: COLORS.textMuted, fontSize: 12, marginLeft: 4 },
  resultRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  resultLabel: { color: COLORS.textSecondary, fontSize: 13 },
  resultValue: { color: COLORS.textPrimary, fontSize: 14, ...FONTS.semi },

  ignoredTitle: { color: COLORS.textPrimary, fontSize: 18, ...FONTS.bold, textAlign: 'center' },
  ignoredSub:   { color: COLORS.textMuted, fontSize: 13, textAlign: 'center', marginTop: 6 },

  scoresSection: { marginTop: 16 },
  scoresTitle:   { color: COLORS.textSecondary, fontSize: 12, ...FONTS.semi, marginBottom: 10 },
  scoreRow:      { flexDirection: 'row', alignItems: 'center', marginBottom: 6 },
  scoreLabelRow: { flexDirection: 'row', alignItems: 'center', width: 120 },
  scoreLabel:    { color: COLORS.textSecondary, fontSize: 11 },
  scoreBarBg:    { flex: 1, height: 5, backgroundColor: COLORS.bgElevated, borderRadius: 3, marginHorizontal: 8 },
  scoreBarFill:  { height: 5, borderRadius: 3 },
  scorePct:      { width: 38, color: COLORS.textMuted, fontSize: 10, textAlign: 'right' },

  divider:     { flexDirection: 'row', alignItems: 'center', marginVertical: 24 },
  dividerLine: { flex: 1, height: 1, backgroundColor: COLORS.border },
  dividerText: { color: COLORS.textMuted, marginHorizontal: 12, fontSize: 13 },

  importCard: { backgroundColor: COLORS.bgCard, borderRadius: RADIUS.lg, padding: 20, borderWidth: 1, borderColor: COLORS.border },
  importTitleRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  importTitle: { color: COLORS.textPrimary, fontSize: 16, ...FONTS.bold },
  importSub:   { color: COLORS.textSecondary, fontSize: 13, lineHeight: 20, marginBottom: 16 },

  progressCard: { backgroundColor: COLORS.bgElevated, borderRadius: RADIUS.md, padding: 12, marginBottom: 16 },
  progressText: { color: COLORS.textPrimary, fontSize: 14, ...FONTS.semi },
  progressStats:{ color: COLORS.textMuted, fontSize: 12, marginTop: 4 },
});
