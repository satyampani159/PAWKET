// src/screens/ProfileScreen.js
import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView,
  TouchableOpacity, TextInput, Alert,
  ActivityIndicator, Platform, PermissionsAndroid,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { authHeaders, logout, updateSyncStatus } from '../services/auth';
import { API_BASE, parseSMSBatch } from '../services/api';
import { readSMSAndroid } from '../services/smsReader';
import { COLORS, FONTS, RADIUS, SHADOW } from '../constants/theme';
import { GradientButton } from '../components';

const GOALS = [
  { key: 'save_more',      label: 'Save More Money',      iconName: 'wallet' },
  { key: 'debt_free',      label: 'Become Debt Free',     iconName: 'lock-open' },
  { key: 'invest',         label: 'Grow Investments',     iconName: 'trending-up' },
  { key: 'buy_home',       label: 'Buy a Home',           iconName: 'home' },
  { key: 'retire_early',   label: 'Retire Early',         iconName: 'sunny' },
  { key: 'emergency_fund', label: 'Build Emergency Fund', iconName: 'shield-checkmark' },
];

const GENDERS = [
  { key: 'male',   label: 'Male',   iconName: 'male' },
  { key: 'female', label: 'Female', iconName: 'female' },
  { key: 'other',  label: 'Other',  iconName: 'person' },
];

const BATCH_SIZE = 100;

async function apiRequest(method, path, body = null) {
  const headers = await authHeaders();
  console.log('[Profile] Headers:', JSON.stringify(headers));
  const options = { method, headers };
  if (body) options.body = JSON.stringify(body);
  const res = await fetch(`${API_BASE}${path}`, options);
  console.log('[Profile] Response status:', res.status);
  return res.json();
}

export default function ProfileScreen({ onLogout }) {
  const [profile, setProfile]           = useState(null);
  const [loading, setLoading]           = useState(true);
  const [saving, setSaving]             = useState(false);
  const [editing, setEditing]           = useState(false);
  const [syncing, setSyncing]           = useState(false);
  const [syncProgress, setSyncProgress] = useState(null);
  const [form, setForm] = useState({
    name: '', email: '', gender: '', age: '',
    financial_goal: '', monthly_income: '',
  });

  useEffect(() => { loadProfile(); }, []);

  async function loadProfile() {
  try {
    await new Promise(r => setTimeout(r, 500));
    const data = await apiRequest('GET', '/profile');
    if (data.detail) {
      console.warn('Profile auth error:', data.detail);
      setLoading(false);
      return;
    }
    setProfile(data);
    setForm({
      name:           data.name || '',
      email:          data.email || '',
      gender:         data.gender || '',
      age:            data.age ? String(data.age) : '',
      financial_goal: data.financial_goal || '',
      monthly_income: data.monthly_income ? String(data.monthly_income) : '',
    });
  } catch (e) {
    console.warn('Profile load error:', e.message);
  } finally {
    setLoading(false);
  }
}

  async function saveProfile() {
    setSaving(true);
    try {
      await apiRequest('PATCH', '/profile', {
        name:           form.name || null,
        email:          form.email || null,
        gender:         form.gender || null,
        age:            form.age ? parseInt(form.age) : null,
        financial_goal: form.financial_goal || null,
        monthly_income: form.monthly_income ? parseFloat(form.monthly_income) : null,
      });
      await loadProfile();
      setEditing(false);
      Alert.alert('Saved', 'Profile updated successfully.');
    } catch (e) {
      Alert.alert('Error', 'Could not save profile.');
    } finally {
      setSaving(false);
    }
  }

  async function handleSMSImport() {
    if (Platform.OS !== 'android') {
      Alert.alert('Android Only', 'SMS import is only available on Android.');
      return;
    }
    Alert.alert(
      'Import SMS',
      'This will scan your last 90 days of bank SMS and add missing transactions. Duplicates are skipped automatically.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Import', onPress: async () => {
            setSyncing(true);
            setSyncProgress({ current: 0, total: 0, parsed: 0, duplicates: 0 });
            try {
              const granted = await PermissionsAndroid.request(
                PermissionsAndroid.PERMISSIONS.READ_SMS,
                {
                  title: 'SMS Permission',
                  message: 'PAWKET needs to read your SMS to import transactions.',
                  buttonPositive: 'Allow',
                  buttonNegative: 'Cancel',
                }
              );
              if (granted !== PermissionsAndroid.RESULTS.GRANTED) {
                Alert.alert('Permission Denied', 'SMS permission required.');
                setSyncing(false);
                return;
              }
              const smsList = await readSMSAndroid(90);
              if (smsList.length === 0) {
                Alert.alert('No SMS Found', 'No financial SMS found in inbox.');
                setSyncing(false);
                return;
              }
              setSyncProgress({ current: 0, total: smsList.length, parsed: 0, duplicates: 0 });
              let totalParsed = 0;
              let totalDuplicates = 0;
              for (let i = 0; i < smsList.length; i += BATCH_SIZE) {
                const batch = smsList.slice(i, i + BATCH_SIZE).map(sms => ({
                  text: sms.text, sms_id: sms.smsId, received_at: sms.receivedAt,
                }));
                try {
                  const result = await parseSMSBatch(batch);
                  totalParsed     += result.parsed || 0;
                  totalDuplicates += result.duplicates || 0;
                } catch (e) { console.warn('Batch error:', e.message); }
                setSyncProgress({
                  current:    Math.min(i + BATCH_SIZE, smsList.length),
                  total:      smsList.length,
                  parsed:     totalParsed,
                  duplicates: totalDuplicates,
                });
              }
              await updateSyncStatus(totalParsed);
              Alert.alert('Import Complete',
                `Scanned ${smsList.length} messages\n${totalParsed} new transactions\n${totalDuplicates} duplicates skipped`);
            } catch (e) {
              Alert.alert('Error', e.message);
            } finally {
              setSyncing(false);
              setSyncProgress(null);
              loadProfile();
            }
          }
        },
      ]
    );
  }

  async function handleLogout() {
    Alert.alert('Logout', 'Are you sure?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Logout', style: 'destructive', onPress: async () => { await logout(); onLogout(); } },
    ]);
  }

  if (loading) return (
    <View style={styles.loader}><ActivityIndicator size="large" color={COLORS.accent} /></View>
  );

  const goal     = GOALS.find(g => g.key === profile?.financial_goal);
  const initials = profile?.name
    ? profile.name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
    : profile?.phone?.slice(-2) || '?';

  return (
    <ScrollView style={styles.root} contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>

      <LinearGradient colors={[COLORS.gradientA, COLORS.gradientB]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.header}>
        <View style={styles.avatarCircle}>
          <Text style={styles.avatarText}>{initials}</Text>
        </View>
        <Text style={styles.headerName} numberOfLines={1} adjustsFontSizeToFit minimumFontScale={0.5}>{profile?.name || 'Your Name'}</Text>
        <Text style={styles.headerPhone} numberOfLines={1}>{profile?.phone}</Text>
        <Text style={styles.memberSince} numberOfLines={1}>Member since {profile?.member_since}</Text>
        <View style={styles.statsRow}>
          <View style={styles.stat}>
            <Text style={styles.statValue} numberOfLines={1} adjustsFontSizeToFit>{profile?.transaction_count || 0}</Text>
            <Text style={styles.statLabel}>Transactions</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.stat}>
            <Text style={styles.statValue} numberOfLines={1}>{profile?.age || '—'}</Text>
            <Text style={styles.statLabel}>Age</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.stat}>
            <Text style={styles.statValue} numberOfLines={1} adjustsFontSizeToFit>{profile?.monthly_income ? `\u20B9${(profile.monthly_income/1000).toFixed(0)}k` : '—'}</Text>
            <Text style={styles.statLabel}>Income</Text>
          </View>
        </View>
      </LinearGradient>

      {/* ── SMS IMPORT CARD ── */}
      <View style={styles.syncCard}>
        <View style={styles.syncLeft}>
          <Ionicons name="phone-portrait" size={28} color={COLORS.accent} />
          <View>
            <Text style={styles.syncTitle}>SMS Transactions</Text>
            <Text style={styles.syncSub} numberOfLines={1} adjustsFontSizeToFit>
              {profile?.last_sync_at
                ? `Last synced: ${new Date(profile.last_sync_at).toLocaleDateString('en-IN')}`
                : 'Never synced - tap to import'}
            </Text>
          </View>
        </View>
        <TouchableOpacity style={[styles.syncBtn, syncing && { opacity: 0.6 }]} onPress={handleSMSImport} disabled={syncing}>
          {syncing ? <ActivityIndicator size="small" color="#fff" /> : <Text style={styles.syncBtnText}>Import</Text>}
        </TouchableOpacity>
      </View>

      {syncing && syncProgress && (
        <View style={styles.progressCard}>
          <View style={styles.progressBarBg}>
            <View style={[styles.progressBarFill, {
              width: syncProgress.total > 0 ? `${Math.round(syncProgress.current / syncProgress.total * 100)}%` : '0%'
            }]} />
          </View>
          <Text style={styles.progressText} numberOfLines={1}>{syncProgress.current} / {syncProgress.total} messages</Text>
          <Text style={styles.progressStats} numberOfLines={1}>{syncProgress.parsed} new - {syncProgress.duplicates} skipped</Text>
        </View>
      )}

      {goal && !editing && (
        <View style={styles.goalCard}>
          <Ionicons name={goal.iconName} size={32} color={COLORS.accent} />
          <View style={styles.goalInfo}>
            <Text style={styles.goalLabel}>Financial Goal</Text>
            <Text style={styles.goalValue} numberOfLines={1} adjustsFontSizeToFit>{goal.label}</Text>
          </View>
        </View>
      )}

      {profile?.goal_advice && !editing && (
        <View style={styles.adviceCard}>
          <Ionicons name="bulb" size={20} color={COLORS.accent} />
          <View style={styles.adviceContent}>
            <Text style={styles.adviceTitle}>Goal Tip</Text>
            <Text style={styles.adviceTip} numberOfLines={3} adjustsFontSizeToFit>{profile.goal_advice.tip}</Text>
            <Text style={styles.adviceFocus} numberOfLines={2} adjustsFontSizeToFit>{profile.goal_advice.focus}</Text>
          </View>
        </View>
      )}

      {!editing ? (
        <>
          <View style={styles.infoCard}>
            {[
              { label: 'Name',   value: profile?.name   || 'Not set' },
              { label: 'Email',  value: profile?.email  || 'Not set' },
              { label: 'Gender', value: profile?.gender ? profile.gender.charAt(0).toUpperCase() + profile.gender.slice(1) : 'Not set' },
              { label: 'Age',    value: String(profile?.age || 'Not set') },
            ].map((item, i, arr) => (
              <View key={item.label} style={[styles.infoRow, i < arr.length - 1 && styles.infoRowBorder]}>
                <Text style={styles.infoLabel}>{item.label}</Text>
                <Text style={styles.infoValue} numberOfLines={1} adjustsFontSizeToFit>{item.value}</Text>
              </View>
            ))}
          </View>
          <GradientButton label="Edit Profile" onPress={() => setEditing(true)} />
        </>
      ) : (
        <>
          <Text style={styles.fieldLabel}>Full Name</Text>
          <TextInput style={styles.input} value={form.name} onChangeText={v => setForm(f => ({ ...f, name: v }))} placeholder="Enter your name" placeholderTextColor={COLORS.textMuted} />
          <Text style={styles.fieldLabel}>Email</Text>
          <TextInput style={styles.input} value={form.email} onChangeText={v => setForm(f => ({ ...f, email: v }))} placeholder="Enter your email" placeholderTextColor={COLORS.textMuted} keyboardType="email-address" autoCapitalize="none" />
          <Text style={styles.fieldLabel}>Age</Text>
          <TextInput style={styles.input} value={form.age} onChangeText={v => setForm(f => ({ ...f, age: v }))} placeholder="Enter your age" placeholderTextColor={COLORS.textMuted} keyboardType="numeric" />
          <Text style={styles.fieldLabel}>Monthly Income (\u20B9)</Text>
          <TextInput style={styles.input} value={form.monthly_income} onChangeText={v => setForm(f => ({ ...f, monthly_income: v }))} placeholder="e.g. 50000" placeholderTextColor={COLORS.textMuted} keyboardType="numeric" />
          <Text style={styles.fieldLabel}>Gender</Text>
          <View style={styles.chipRow}>
            {GENDERS.map(g => (
              <TouchableOpacity key={g.key} style={[styles.chip, form.gender === g.key && styles.chipActive]} onPress={() => setForm(f => ({ ...f, gender: g.key }))}>
                <Ionicons name={g.iconName} size={16} color={form.gender === g.key ? COLORS.accent : COLORS.textSecondary} style={{ marginRight: 6 }} />
                <Text style={styles.chipText}>{g.label}</Text>
              </TouchableOpacity>
            ))}
          </View>
          <Text style={styles.fieldLabel}>Financial Goal</Text>
          <View style={styles.goalGrid}>
            {GOALS.map(g => (
              <TouchableOpacity key={g.key} style={[styles.goalOption, form.financial_goal === g.key && styles.goalOptionActive]} onPress={() => setForm(f => ({ ...f, financial_goal: g.key }))}>
                <Ionicons name={g.iconName} size={24} color={form.financial_goal === g.key ? COLORS.accent : COLORS.textSecondary} style={{ marginBottom: 6 }} />
                <Text style={[styles.goalOptionLabel, form.financial_goal === g.key && { color: COLORS.accent }]} numberOfLines={2} adjustsFontSizeToFit>{g.label}</Text>
              </TouchableOpacity>
            ))}
          </View>
          <GradientButton label="Save Profile" onPress={saveProfile} loading={saving} />
          <TouchableOpacity style={styles.cancelBtn} onPress={() => setEditing(false)}>
            <Text style={styles.cancelText}>Cancel</Text>
          </TouchableOpacity>
        </>
      )}

      <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
        <Ionicons name="log-out" size={18} color="#C46B6B" style={{ marginRight: 8 }} />
        <Text style={styles.logoutText}>Logout</Text>
      </TouchableOpacity>
      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root:    { flex: 1, backgroundColor: COLORS.bg },
  scroll:  { paddingBottom: 40 },
  loader:  { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.bg },
  header:       { padding: 28, paddingTop: 50, alignItems: 'center', borderBottomLeftRadius: 28, borderBottomRightRadius: 28 },
  avatarCircle: { width: 80, height: 80, borderRadius: 40, backgroundColor: 'rgba(255,255,255,0.2)', alignItems: 'center', justifyContent: 'center', marginBottom: 12, borderWidth: 3, borderColor: 'rgba(255,255,255,0.4)' },
  avatarText:   { color: '#fff', fontSize: 28, fontWeight: '900' },
  headerName:   { color: '#fff', fontSize: 22, fontWeight: '800', marginBottom: 4 },
  headerPhone:  { color: 'rgba(255,255,255,0.7)', fontSize: 14, marginBottom: 2 },
  memberSince:  { color: 'rgba(255,255,255,0.5)', fontSize: 12, marginBottom: 20 },
  statsRow:     { flexDirection: 'row', alignItems: 'center', backgroundColor: 'rgba(255,255,255,0.12)', borderRadius: 16, padding: 16, gap: 20 },
  stat:         { flex: 1, alignItems: 'center' },
  statValue:    { color: '#fff', fontSize: 20, fontWeight: '800' },
  statLabel:    { color: 'rgba(255,255,255,0.6)', fontSize: 11, marginTop: 2 },
  statDivider:  { width: 1, height: 30, backgroundColor: 'rgba(255,255,255,0.15)' },
  syncCard:     { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: COLORS.bgCard, borderRadius: 16, margin: 16, padding: 16 },
  syncLeft:     { flexDirection: 'row', alignItems: 'center', gap: 12 },
  syncTitle:    { color: COLORS.textPrimary, fontSize: 15, fontWeight: '700' },
  syncSub:      { color: COLORS.textMuted, fontSize: 11, marginTop: 2 },
  syncBtn:      { backgroundColor: COLORS.accent, borderRadius: 999, paddingHorizontal: 16, paddingVertical: 8 },
  syncBtnText:  { color: '#fff', fontSize: 13, fontWeight: '700' },
  progressCard:    { marginHorizontal: 16, marginTop: -8, marginBottom: 8, backgroundColor: COLORS.bgCard, borderRadius: 12, padding: 14 },
  progressBarBg:   { height: 6, backgroundColor: COLORS.bgElevated, borderRadius: 999, marginBottom: 8, overflow: 'hidden' },
  progressBarFill: { height: 6, backgroundColor: COLORS.accent, borderRadius: 999 },
  progressText:    { color: COLORS.textPrimary, fontSize: 13, fontWeight: '600' },
  progressStats:   { color: COLORS.textMuted, fontSize: 11, marginTop: 4 },
  goalCard:    { flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.bgCard, borderRadius: 16, marginHorizontal: 16, marginBottom: 8, padding: 16, gap: 14 },
  goalInfo:    { flex: 1 },
  goalLabel:   { color: COLORS.textMuted, fontSize: 11 },
  goalValue:   { color: COLORS.textPrimary, fontSize: 16, fontWeight: '700', marginTop: 2 },
  adviceCard:    { flexDirection: 'row', backgroundColor: COLORS.accent + '12', borderRadius: 16, marginHorizontal: 16, marginBottom: 16, padding: 16, gap: 12, borderWidth: 1, borderColor: COLORS.accent + '30' },
  adviceContent: { flex: 1 },
  adviceTitle:   { color: COLORS.accent, fontSize: 12, fontWeight: '700', marginBottom: 4 },
  adviceTip:     { color: COLORS.textPrimary, fontSize: 13, fontWeight: '500', marginBottom: 4, lineHeight: 18 },
  adviceFocus:   { color: COLORS.textSecondary, fontSize: 12, lineHeight: 17 },
  infoCard:      { backgroundColor: COLORS.bgCard, borderRadius: 16, marginHorizontal: 16, marginBottom: 16, overflow: 'hidden' },
  infoRow:       { flexDirection: 'row', justifyContent: 'space-between', padding: 16 },
  infoRowBorder: { borderBottomWidth: 1, borderBottomColor: COLORS.border },
  infoLabel:     { color: COLORS.textMuted, fontSize: 13 },
  infoValue:     { color: COLORS.textPrimary, fontSize: 13, fontWeight: '600' },
  fieldLabel: { color: COLORS.textSecondary, fontSize: 12, fontWeight: '600', marginHorizontal: 16, marginTop: 14, marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 },
  input:      { backgroundColor: COLORS.bgCard, borderRadius: 12, padding: 14, color: COLORS.textPrimary, fontSize: 15, marginHorizontal: 16, borderWidth: 1, borderColor: COLORS.border },
  chipRow:    { flexDirection: 'row', marginHorizontal: 16, gap: 8 },
  chip:       { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.bgCard, borderRadius: 999, padding: 10, borderWidth: 1, borderColor: COLORS.border },
  chipActive: { borderColor: COLORS.accent, backgroundColor: COLORS.accentSoft },
  chipText:   { color: COLORS.textPrimary, fontSize: 13, fontWeight: '500' },
  goalGrid:         { flexDirection: 'row', flexWrap: 'wrap', marginHorizontal: 12, gap: 8, marginBottom: 8 },
  goalOption:       { width: '47%', backgroundColor: COLORS.bgCard, borderRadius: 12, padding: 12, alignItems: 'center', borderWidth: 1, borderColor: COLORS.border },
  goalOptionActive: { borderColor: COLORS.accent, backgroundColor: COLORS.accentSoft },
  goalOptionLabel:  { color: COLORS.textSecondary, fontSize: 11, fontWeight: '500', textAlign: 'center' },
  cancelBtn:  { alignItems: 'center', padding: 16, marginTop: 8 },
  cancelText: { color: COLORS.textMuted, fontSize: 14 },
  logoutBtn:  { flexDirection: 'row', marginHorizontal: 16, marginTop: 24, backgroundColor: '#C46B6B18', borderRadius: 16, padding: 16, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#C46B6B30' },
  logoutText: { color: '#C46B6B', fontSize: 15, fontWeight: '700' },
});
