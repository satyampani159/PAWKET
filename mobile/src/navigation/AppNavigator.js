import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  AppState,
  Platform,
  Image,
  Keyboard,
} from 'react-native';

import { NavigationContainer } from '@react-navigation/native';

import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

import { createNativeStackNavigator } from '@react-navigation/native-stack';

import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Ionicons } from '@expo/vector-icons';

import { readSMSAndroid } from '../services/smsReader';
import { parseSMSBatch } from '../services/api';
import { updateSyncStatus } from '../services/auth';

import DashboardScreen from '../screens/DashboardScreen';
import AnalyticsScreen from '../screens/AnalyticsScreen';
import TransactionsScreen from '../screens/TransactionsScreen';
import AdviceScreen from '../screens/AdviceScreen';
import ProfileScreen from '../screens/ProfileScreen';
import ChartDetailScreen from '../screens/ChartDetailScreen';

import { COLORS, FONTS } from '../constants/theme';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

const TAB_ITEMS = [
  { name: 'Dashboard',    iconName: 'home',                label: 'Home' },
  { name: 'Transactions', iconName: 'receipt',             label: 'Transactions' },
  { name: 'Analytics',    iconName: 'bar-chart',           label: 'Analytics' },
  { name: 'Advice',       iconName: 'bulb',                label: 'Advice' },
  { name: 'Profile',      iconName: 'person',              label: 'Profile' },
];

async function syncNewSMS() {
  if (Platform.OS !== 'android') return;

  try {
    const smsList = await readSMSAndroid(7);

    if (!smsList.length) return;

    const batch = smsList.map((s) => ({
      text: s.text,
      sms_id: s.smsId,
      received_at: s.receivedAt,
    }));

    for (let i = 0; i < batch.length; i += 100) {
      await parseSMSBatch(batch.slice(i, i + 100));
    }

    await updateSyncStatus(smsList.length);
  } catch (e) {
    console.log('Sync error:', e.message);
  }
}

function CustomTabBar({ state, navigation }) {
  const insets = useSafeAreaInsets();
  const [keyboardOpen, setKeyboardOpen] = useState(false);

  useEffect(() => {
    const showEvt = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvt = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';
    const showSub = Keyboard.addListener(showEvt, () => setKeyboardOpen(true));
    const hideSub = Keyboard.addListener(hideEvt, () => setKeyboardOpen(false));
    return () => { showSub.remove(); hideSub.remove(); };
  }, []);

  if (keyboardOpen) return null;

  return (
    <View
      style={[
        styles.tabBar,
        { paddingBottom: insets.bottom + 8 },
      ]}
    >
      {state.routes.map((route, index) => {
        const isFocused = state.index === index;

        const tab = TAB_ITEMS.find(
          (t) => t.name === route.name
        );

        return (
          <TouchableOpacity
            key={route.key}
            style={styles.tabItem}
            activeOpacity={0.7}
            onPress={() => {
              if (!isFocused)
                navigation.navigate(route.name);
            }}
          >
            <Ionicons
              name={tab?.iconName || 'ellipse'}
              size={22}
              color={isFocused ? COLORS.accent : COLORS.textMuted}
            />

            <Text
              style={[
                styles.tabLabel,
                isFocused && styles.tabLabelActive,
              ]}
            >
              {tab?.label}
            </Text>

            {isFocused && <View style={styles.tabDot} />}
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

function MainTabs({ onLogout }) {
  const appState = useRef(AppState.currentState);

  useEffect(() => {
    syncNewSMS();

    const sub = AppState.addEventListener(
      'change',
      (next) => {
        if (
          appState.current.match(
            /inactive|background/
          ) &&
          next === 'active'
        ) {
          syncNewSMS();
        }

        appState.current = next;
      }
    );

    return () => sub.remove();
  }, []);

  return (
    <Tab.Navigator
      tabBar={(props) => (
        <CustomTabBar {...props} />
      )}
      screenOptions={{
        headerStyle: {
          backgroundColor: COLORS.bg,
        },

        headerTintColor: COLORS.textPrimary,

        headerTitleStyle: {
          ...FONTS.bold,
          fontSize: 18,
        },

        headerShadowVisible: false,
      }}
    >
      <Tab.Screen
  name="Dashboard"
  component={DashboardScreen}
  options={{
    headerTitle: () => (
      <View
        style={{
          flexDirection: 'row',
          alignItems: 'center',
        }}
      >
        <Image
          source={require('../../assets/logo.png')}
          style={{
            width: 34,
            height: 34,
            marginRight: 10,
          }}
          resizeMode="contain"
        />

        <Text
          style={{
            color: COLORS.textPrimary,
            fontSize: 22,
            fontWeight: '800',
            letterSpacing: 1,
          }}
        >
          PAWKET
        </Text>
      </View>
    ),
  }}
/>

      <Tab.Screen
        name="Transactions"
        component={TransactionsScreen}
        options={{ title: 'Transactions' }}
      />

      <Tab.Screen
        name="Analytics"
        component={AnalyticsScreen}
        options={{ title: 'Analytics' }}
      />

      <Tab.Screen
        name="Advice"
        component={AdviceScreen}
        options={{ title: 'Advice' }}
      />

      <Tab.Screen
        name="Profile"
        options={{ title: 'My Profile' }}
      >
        {() => (
          <ProfileScreen onLogout={onLogout} />
        )}
      </Tab.Screen>
    </Tab.Navigator>
  );
}

export default function AppNavigator({
  onLogout,
}) {
  return (
    <NavigationContainer
      theme={{
        dark: true,

        colors: {
          primary: COLORS.accent,
          background: COLORS.bg,
          card: COLORS.bgCard,
          text: COLORS.textPrimary,
          border: COLORS.border,
          notification: COLORS.accent,
        },
      }}
    >
      <Stack.Navigator
        screenOptions={{ headerShown: false }}
      >
        <Stack.Screen name="Main">
          {() => (
            <MainTabs onLogout={onLogout} />
          )}
        </Stack.Screen>
        <Stack.Screen name="ChartDetail" component={ChartDetailScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    flexDirection: 'row',
    backgroundColor: COLORS.bgCard,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    paddingTop: 10,
    paddingHorizontal: 4,
  },

  tabItem: {
    flex: 1,
    alignItems: 'center',
    gap: 3,
  },

  tabLabel: {
    color: COLORS.textMuted,
    fontSize: 9,
    ...FONTS.medium,
  },

  tabLabelActive: {
    color: COLORS.textPrimary,
    ...FONTS.bold,
  },

  tabDot: {
    position: 'absolute',
    bottom: -6,
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: COLORS.accent,
  },
});
