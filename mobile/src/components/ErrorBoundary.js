import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, FONTS, RADIUS } from '../constants/theme';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.warn('ErrorBoundary caught:', error, info?.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <View style={styles.container}>
          <Text style={styles.title}>Something went wrong</Text>
          <Text style={styles.sub}>An unexpected error occurred. Please try again.</Text>
          <TouchableOpacity
            style={styles.btn}
            activeOpacity={0.7}
            onPress={() => this.setState({ hasError: false })}
          >
            <Text style={styles.btnText}>Retry</Text>
          </TouchableOpacity>
        </View>
      );
    }
    return this.props.children;
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.bg,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  title: { color: COLORS.textPrimary, fontSize: 18, ...FONTS.bold, marginBottom: 8 },
  sub: { color: COLORS.textSecondary, fontSize: 14, textAlign: 'center', marginBottom: 24, ...FONTS.medium },
  btn: {
    backgroundColor: COLORS.accent,
    borderRadius: RADIUS.full,
    paddingHorizontal: 28,
    paddingVertical: 12,
  },
  btnText: { color: '#fff', fontSize: 15, ...FONTS.semi },
});
