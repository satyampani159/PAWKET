// src/screens/LoginScreen.js
import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Alert,
  Image,
  ScrollView,
  Keyboard,
  TouchableWithoutFeedback,
} from 'react-native';

import { LinearGradient } from 'expo-linear-gradient';
import { requestOTP, verifyOTP, saveToken, saveUser } from '../services/auth';
import { COLORS, FONTS, RADIUS } from '../constants/theme';

export default function LoginScreen({ onLoginSuccess }) {
  const [step, setStep] = useState('phone');
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [devOtp, setDevOtp] = useState('');
  const otpRefs = useRef([]);

  async function handleSendOTP() {
    const cleaned = phone.replace(/\s/g, '');

    if (cleaned.length < 10) {
      Alert.alert('Invalid Number', 'Enter a valid 10-digit mobile number.');
      return;
    }

    const fullPhone = cleaned.startsWith('+')
      ? cleaned
      : `+91${cleaned}`;

    setLoading(true);

    try {
      const res = await requestOTP(fullPhone);

      if (res.success) {
        const match = res.message?.match(/DEV: (\d{6})/);

        if (match) setDevOtp(match[1]);

        setStep('otp');
      } else {
        Alert.alert('Error', res.message || 'Could not send OTP.');
      }
    } catch (e) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyOTP() {
    const otpString = otp.join('');

    if (otpString.length !== 6) {
      Alert.alert('Enter OTP', 'Please enter the 6-digit OTP.');
      return;
    }

    const cleaned = phone.replace(/\s/g, '');
    const fullPhone = cleaned.startsWith('+')
      ? cleaned
      : `+91${cleaned}`;

    setLoading(true);

    try {
      const res = await verifyOTP(fullPhone, otpString);

      if (res.success && res.token) {
        await saveToken(res.token);

        await saveUser({
          user_id: res.user_id,
          phone: res.phone,
        });

        onLoginSuccess({
          isNewUser: res.is_new_user,
        });
      } else {
        Alert.alert(
          'Wrong OTP',
          'The OTP is incorrect or expired.'
        );

        setOtp(['', '', '', '', '', '']);
        otpRefs.current[0]?.focus();
      }
    } catch (e) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
    }
  }

  function handleOtpChange(val, index) {
    const newOtp = [...otp];

    newOtp[index] = val;

    setOtp(newOtp);

    if (val && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }

    if (!val && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
    >
      <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          bounces={false}
        >
          <LinearGradient
            colors={[COLORS.bg, COLORS.bgCard, '#0D0F14']}
            style={StyleSheet.absoluteFill}
          />

          <View style={styles.logoArea}>
            <Image
              source={require('../../assets/logo.png')}
              style={styles.logoImage}
              resizeMode="contain"
            />

            <Text style={styles.appName}>PAWKET</Text>

            <Text style={styles.tagline}>
              Your Wise Financial Watchdog
            </Text>
          </View>

          <View style={styles.card}>
            {step === 'phone' ? (
              <>
                <Text style={styles.cardTitle}>
                  Enter your number
                </Text>

                <Text style={styles.cardSub}>
                  We'll send a 6-digit OTP to verify
                </Text>

                <View style={styles.phoneRow}>
                  <View style={styles.countryCode}>
                    <Text style={styles.countryText}>
                      +91
                    </Text>
                  </View>

                  <TextInput
                    style={styles.phoneInput}
                    value={phone}
                    onChangeText={setPhone}
                    placeholder="98765 43210"
                    placeholderTextColor={COLORS.textMuted}
                    keyboardType="phone-pad"
                    maxLength={10}
                  />
                </View>

                <TouchableOpacity
                  style={styles.btn}
                  onPress={handleSendOTP}
                  disabled={loading}
                  activeOpacity={0.8}
                >
                  <View style={styles.btnSolid}>
                    {loading ? (
                      <ActivityIndicator color="#fff" />
                    ) : (
                      <Text style={styles.btnText}>
                        Send OTP
                      </Text>
                    )}
                  </View>
                </TouchableOpacity>
              </>
            ) : (
              <>
                <Text style={styles.cardTitle}>
                  Enter OTP
                </Text>

                <Text style={styles.cardSub}>
                  Sent to +91 {phone}
                </Text>

                {devOtp ? (
                  <View style={styles.devHint}>
                    <Text style={styles.devHintText}>
                      DEV MODE - OTP: {devOtp}
                    </Text>
                  </View>
                ) : null}

                <View style={styles.otpRow}>
                  {otp.map((digit, i) => (
                    <TextInput
                      key={i}
                      ref={(r) => (otpRefs.current[i] = r)}
                      style={[
                        styles.otpBox,
                        digit && styles.otpBoxFilled,
                      ]}
                      value={digit}
                      onChangeText={(v) =>
                        handleOtpChange(v.slice(-1), i)
                      }
                      keyboardType="numeric"
                      maxLength={1}
                      textAlign="center"
                      autoFocus={i === 0}
                    />
                  ))}
                </View>

                <TouchableOpacity
                  style={styles.btn}
                  onPress={handleVerifyOTP}
                  disabled={loading}
                  activeOpacity={0.8}
                >
                  <View style={styles.btnSolid}>
                    {loading ? (
                      <ActivityIndicator color="#fff" />
                    ) : (
                      <Text style={styles.btnText}>
                        Verify & Login
                      </Text>
                    )}
                  </View>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.backBtn}
                  onPress={() => {
                    setStep('phone');
                    setOtp(['', '', '', '', '', '']);
                    setDevOtp('');
                  }}
                >
                  <Text style={styles.backBtnText}>
                    Change number
                  </Text>
                </TouchableOpacity>
              </>
            )}
          </View>

          <Text style={styles.footer} numberOfLines={2} adjustsFontSizeToFit>
            By continuing you agree to our Terms & Privacy Policy
          </Text>
        </ScrollView>
      </TouchableWithoutFeedback>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },

  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
  },

  logoArea: {
    alignItems: 'center',
    marginBottom: 40,
  },

  logoImage: {
    width: 170,
    height: 170,
    marginBottom: 8,
  },

  appName: {
    color: COLORS.textPrimary,
    fontSize: 32,
    fontWeight: '900',
  },

  tagline: {
    color: COLORS.textSecondary,
    fontSize: 14,
    marginTop: 4,
  },

  card: {
    backgroundColor: COLORS.bgCard,
    borderRadius: 24,
    padding: 24,
    borderWidth: 1,
    borderColor: COLORS.border,
  },

  cardTitle: {
    color: COLORS.textPrimary,
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 6,
  },

  cardSub: {
    color: COLORS.textSecondary,
    fontSize: 14,
    marginBottom: 24,
  },

  phoneRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 20,
  },

  countryCode: {
    backgroundColor: COLORS.bgElevated,
    borderRadius: 12,
    padding: 14,
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },

  countryText: {
    color: COLORS.textPrimary,
    fontSize: 15,
  },

  phoneInput: {
    flex: 1,
    backgroundColor: COLORS.bgElevated,
    borderRadius: 12,
    padding: 14,
    color: COLORS.textPrimary,
    fontSize: 18,
    fontWeight: '700',
    borderWidth: 1,
    borderColor: COLORS.border,
  },

  devHint: {
    backgroundColor: COLORS.medium + '22',
    borderRadius: 12,
    padding: 10,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: COLORS.medium + '55',
  },

  devHintText: {
    color: COLORS.medium,
    fontSize: 13,
    fontWeight: '700',
    textAlign: 'center',
  },

  otpRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 24,
    justifyContent: 'center',
  },

  otpBox: {
    width: 44,
    height: 54,
    backgroundColor: COLORS.bgElevated,
    borderRadius: 12,
    color: COLORS.textPrimary,
    fontSize: 24,
    fontWeight: '700',
    borderWidth: 1,
    borderColor: COLORS.border,
  },

  otpBoxFilled: {
    borderColor: COLORS.accent,
  },

  btn: {
    borderRadius: 999,
    overflow: 'hidden',
  },

  btnSolid: {
    backgroundColor: COLORS.accent,
    padding: 16,
    alignItems: 'center',
    borderRadius: 999,
  },

  btnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },

  backBtn: {
    alignItems: 'center',
    marginTop: 16,
  },

  backBtnText: {
    color: COLORS.textMuted,
    fontSize: 13,
  },

  footer: {
    color: COLORS.textMuted,
    fontSize: 11,
    textAlign: 'center',
    marginTop: 32,
  },
});
