// App.js
import React, { useState, useEffect } from 'react';
import { StatusBar, View, ActivityIndicator } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { getToken, getMe } from './src/services/auth';
import WelcomeScreen    from './src/screens/WelcomeScreen';
import LoginScreen      from './src/screens/LoginScreen';
import OnboardingScreen from './src/screens/OnboardingScreen';
import AppNavigator     from './src/navigation/AppNavigator';
import ErrorBoundary    from './src/components/ErrorBoundary';

export default function App() {
  // Always show welcome first, then check auth
  const [showWelcome, setShowWelcome] = useState(true);
  const [authState, setAuthState]     = useState('loading');

  // Check auth in background while welcome plays
  useEffect(() => {
    (async () => {
      try {
        const token = await getToken();
        if (!token) { setAuthState('login'); return; }
        const me = await getMe();
        setAuthState(me?.user_id ? 'app' : 'login');
      } catch {
        setAuthState('login');
      }
    })();
  }, []);

  // Welcome finishes → show whatever auth state resolved to
  function handleWelcomeDone() {
    setShowWelcome(false);
  }

  // Loading spinner (only if welcome done but auth still resolving)
  if (!showWelcome && authState === 'loading') return (
    <View style={{ flex:1, backgroundColor:'#0A0A0F', alignItems:'center', justifyContent:'center' }}>
      <StatusBar barStyle="light-content" backgroundColor="#0A0A0F" />
      <ActivityIndicator size="large" color="#7C3AED" />
    </View>
  );

  return (
    <SafeAreaProvider>
      <StatusBar barStyle="light-content" backgroundColor="#0A0A0F" />

      {/* Welcome always renders on top until done */}
      {showWelcome && <WelcomeScreen onFinish={handleWelcomeDone} />}

      {/* Auth flow underneath — renders in background */}
      {!showWelcome && authState === 'login' && (
        <LoginScreen
          onLoginSuccess={({ isNewUser }) =>
            setAuthState(isNewUser ? 'onboarding' : 'app')
          }
        />
      )}

      {!showWelcome && authState === 'onboarding' && (
        <OnboardingScreen onDone={() => setAuthState('app')} />
      )}

      {!showWelcome && authState === 'app' && (
        <ErrorBoundary>
          <AppNavigator onLogout={() => setAuthState('login')} />
        </ErrorBoundary>
      )}
    </SafeAreaProvider>
  );
}
