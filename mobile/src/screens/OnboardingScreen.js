// src/screens/OnboardingScreen.js
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Platform,
  PermissionsAndroid,
} from 'react-native';

import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

import { readSMSAndroid } from '../services/smsReader';
import { parseSMSBatch } from '../services/api';
import { updateSyncStatus } from '../services/auth';
import { GradientButton } from '../components';
import { COLORS } from '../constants/theme';

const BATCH_SIZE = 100;

export default function OnboardingScreen({ onDone }) {
  const [step, setStep] = useState('permission');

  const [progress, setProgress] = useState({
    current: 0,
    total: 0,
    parsed: 0,
  });

  async function requestAndImport() {
    if (Platform.OS === 'android') {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.READ_SMS,
        {
          title: 'Read SMS Permission',

          message:
            'PAWKET needs to read your SMS to automatically detect and categorise your transactions. Your messages are processed privately and never shared.',

          buttonPositive: 'Allow',
          buttonNegative: 'Skip',
        }
      );

      if (granted !== PermissionsAndroid.RESULTS.GRANTED) {
        onDone();
        return;
      }
    }

    setStep('importing');

    try {
      const smsList = await readSMSAndroid(90);

      if (smsList.length === 0) {
        await updateSyncStatus(0);
        setStep('done');
        return;
      }

      setProgress({
        current: 0,
        total: smsList.length,
        parsed: 0,
      });

      let totalParsed = 0;

      for (let i = 0; i < smsList.length; i += BATCH_SIZE) {
        const batch = smsList
          .slice(i, i + BATCH_SIZE)
          .map((sms) => ({
            text: sms.text,
            sms_id: sms.smsId,
            received_at: sms.receivedAt,
          }));

        try {
          const result = await parseSMSBatch(batch);

          totalParsed += result.parsed || 0;
        } catch (e) {
          console.warn('Batch error:', e.message);
        }

        setProgress({
          current: Math.min(i + BATCH_SIZE, smsList.length),
          total: smsList.length,
          parsed: totalParsed,
        });
      }

      await updateSyncStatus(totalParsed);

      setStep('done');
    } catch (e) {
      console.warn('Import error:', e.message);
      setStep('done');
    }
  }

  const pct =
    progress.total > 0
      ? Math.round((progress.current / progress.total) * 100)
      : 0;

  return (
    <View style={styles.root}>
      <LinearGradient
        colors={[COLORS.bg, '#0D0F14']}
        style={StyleSheet.absoluteFill}
      />

      {step === 'permission' && (
        <View style={styles.content}>
          <View style={styles.iconCircle}>
            <Ionicons name="phone-portrait" size={48} color={COLORS.accent} />
          </View>

          <Text style={styles.title}>
            Set up your finances
          </Text>

          <Text style={styles.sub}>
            PAWKET will read your bank SMS messages
            to automatically track your spending.
            {'\n\n'}
            Your messages are processed on your
            private server and never shared.
          </Text>

          <View style={styles.featureList}>
            {[
              ['card', 'Auto-detects bank transactions'],
              ['pricetag', 'Categorises spending intelligently'],
              ['bar-chart', 'Shows monthly analytics instantly'],
              ['lock-closed', 'Your data stays private'],
            ].map(([iconName, text]) => (
              <View key={text} style={styles.featureRow}>
                <Ionicons name={iconName} size={22} color={COLORS.accent} />

                <Text style={styles.featureText} numberOfLines={1} adjustsFontSizeToFit>
                  {text}
                </Text>
              </View>
            ))}
          </View>

          <GradientButton
            label="Allow SMS Access & Import"
            onPress={requestAndImport}
          />

          <Text
            style={styles.skipText}
            onPress={onDone}
          >
            Skip for now
          </Text>
        </View>
      )}

      {step === 'importing' && (
        <View style={styles.content}>
          <View style={styles.iconCircle}>
            <Ionicons name="flash" size={48} color={COLORS.accent} />
          </View>

          <Text style={styles.title}>
            Importing your transactions
          </Text>

          <Text style={styles.sub}>
            Reading your last 90 days of messages...
          </Text>

          <View style={styles.progressBarBg}>
            <View
              style={[
                styles.progressBarFill,
                { width: `${pct}%`, backgroundColor: COLORS.accent },
              ]}
            />
          </View>

          <Text style={styles.progressText} numberOfLines={1}>
            {pct}% — {progress.current} of{' '}
            {progress.total} messages
          </Text>

          <Text style={styles.parsedText} numberOfLines={1}>
            {progress.parsed} transactions found
          </Text>

          <Text style={styles.importNote}>
            This only happens once. Future syncs are
            instant.
          </Text>
        </View>
      )}

      {step === 'done' && (
        <View style={styles.content}>
          <View style={styles.iconCircle}>
            <Ionicons name="checkmark-circle" size={48} color={COLORS.high} />
          </View>

          <Text style={styles.title}>
            You're all set!
          </Text>

          <Text style={styles.sub}>
            Found {progress.parsed} transactions.
            {'\n'}
            Your dashboard is ready.
          </Text>

          <GradientButton
            label="Go to Dashboard"
            onPress={onDone}
          />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    justifyContent: 'center',
  },

  content: {
    padding: 32,
    alignItems: 'center',
  },

  iconCircle: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: COLORS.bgElevated,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
    borderWidth: 1,
    borderColor: COLORS.border,
  },

  title: {
    color: COLORS.textPrimary,
    fontSize: 26,
    fontWeight: '900',
    textAlign: 'center',
    marginBottom: 12,
  },

  sub: {
    color: COLORS.textSecondary,
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 32,
  },

  featureList: {
    alignSelf: 'stretch',
    marginBottom: 32,
    gap: 14,
  },

  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },

  featureText: {
    color: COLORS.textPrimary,
    fontSize: 15,
    fontWeight: '500',
  },

  progressBarBg: {
    width: '100%',
    height: 10,
    backgroundColor: COLORS.bgElevated,
    borderRadius: 999,
    marginBottom: 12,
    overflow: 'hidden',
  },

  progressBarFill: {
    height: 10,
    borderRadius: 999,
  },

  progressText: {
    color: COLORS.textPrimary,
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 6,
  },

  parsedText: {
    color: COLORS.high,
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 24,
  },

  importNote: {
    color: COLORS.textMuted,
    fontSize: 12,
    textAlign: 'center',
  },

  skipText: {
    color: COLORS.textMuted,
    fontSize: 13,
    marginTop: 20,
    padding: 10,
  },
});
