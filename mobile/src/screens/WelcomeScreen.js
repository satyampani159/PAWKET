import React, { useEffect, useRef } from 'react';
import {
  View,
  Animated,
  StyleSheet,
  Easing,
  Image,
  StatusBar,
} from 'react-native';

import { LinearGradient } from 'expo-linear-gradient';

import {
  useFonts,
  DancingScript_600SemiBold,
} from '@expo-google-fonts/dancing-script';

export default function WelcomeScreen({ onFinish }) {
  const [fontsLoaded] = useFonts({
    DancingScript_600SemiBold,
  });

  const screenOpacity = useRef(
    new Animated.Value(1)
  ).current;

  const welcomeOpacity = useRef(
    new Animated.Value(0)
  ).current;

  const welcomeTranslate = useRef(
    new Animated.Value(-14)
  ).current;

  const logoOpacity = useRef(
    new Animated.Value(0)
  ).current;

  const logoScale = useRef(
    new Animated.Value(0.68)
  ).current;

  const titleOpacity = useRef(
    new Animated.Value(0)
  ).current;

  const taglineOpacity = useRef(
    new Animated.Value(0)
  ).current;

  useEffect(() => {
    Animated.sequence([
      Animated.parallel([
        Animated.timing(welcomeOpacity, {
          toValue: 1,
          duration: 180,
          easing: Easing.out(Easing.quad),
          useNativeDriver: true,
        }),

        Animated.timing(welcomeTranslate, {
          toValue: 0,
          duration: 180,
          easing: Easing.out(Easing.quad),
          useNativeDriver: true,
        }),
      ]),

      Animated.parallel([
        Animated.timing(logoOpacity, {
          toValue: 1,
          duration: 160,
          useNativeDriver: true,
        }),

        Animated.spring(logoScale, {
          toValue: 1,
          friction: 5,
          tension: 85,
          useNativeDriver: true,
        }),
      ]),

      Animated.timing(titleOpacity, {
        toValue: 1,
        duration: 220,
        easing: Easing.out(Easing.ease),
        useNativeDriver: true,
      }),

      Animated.timing(taglineOpacity, {
        toValue: 1,
        duration: 180,
        useNativeDriver: true,
      }),

Animated.delay(1650),

      Animated.timing(screenOpacity, {
        toValue: 0,
        duration: 240,
        easing: Easing.in(Easing.ease),
        useNativeDriver: true,
      }),
    ]).start(() => onFinish?.());
  }, []);

  if (!fontsLoaded) return null;

  return (
    <Animated.View
      style={[
        styles.root,
        { opacity: screenOpacity },
      ]}
    >
      <StatusBar
        barStyle="light-content"
        backgroundColor="#050816"
      />

      <LinearGradient
        colors={['#050816', '#07111F', '#0B1220']}
        style={StyleSheet.absoluteFill}
      />

      <Animated.Text
        style={[
          styles.welcomeText,
          {
            opacity: welcomeOpacity,
            transform: [
              { translateX: welcomeTranslate },
            ],
          },
        ]}
      >
        Welcome to
      </Animated.Text>

      <Animated.View
        style={[
          styles.logoCard,
          {
            opacity: logoOpacity,
            transform: [{ scale: logoScale }],
          },
        ]}
      >
        <Image
          source={require('../../assets/logo.png')}
          style={styles.logoImage}
          resizeMode="contain"
        />
      </Animated.View>

      <Animated.Text
        style={[
          styles.title,
          { opacity: titleOpacity },
        ]}
      >
        PAWKET
      </Animated.Text>

      <Animated.Text
        style={[
          styles.tagline,
          { opacity: taglineOpacity },
        ]}
      >
        Your Wise Financial Watchdog
      </Animated.Text>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  root: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
    backgroundColor: '#050816',
  },

  welcomeText: {
    color: '#D1D5DB',
    fontSize: 42,
    fontFamily: 'DancingScript_600SemiBold',
    marginBottom: 18,
    letterSpacing: 0.3,
  },

  logoCard: {
    width: 180,
    height: 180,
    alignItems: 'center',
    justifyContent: 'center',

    shadowColor: '#000000',
    shadowOpacity: 0.45,
    shadowRadius: 22,
    shadowOffset: {
      width: 0,
      height: 14,
    },

    elevation: 24,
    marginBottom: 18,
  },

  logoImage: {
    width: 180,
    height: 180,
  },

  title: {
    color: '#FFFFFF',
    fontSize: 36,
    fontWeight: '900',
    letterSpacing: 5,
    marginBottom: 8,
  },

  tagline: {
    color: '#94A3B8',
    fontSize: 14,
    letterSpacing: 0.4,
    textAlign: 'center',
  },
});