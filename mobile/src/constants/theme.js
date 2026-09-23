// src/constants/theme.js
// Professional dark theme — PAWKET brand (purple accent)

export const COLORS = {
  // Backgrounds — blue-grey dark
  bg:           '#0D0F14',
  bgCard:       '#161921',
  bgElevated:   '#1E2129',
  bgSheet:      '#1A1D25',

  // Brand — derived from logo gradient (purple → pink)
  gradientA:    '#7C3AED',
  gradientB:    '#EC4899',
  accent:       '#7B52E8',   // primary UI accent (violet)
  accentSoft:   '#7B52E820', // tinted background for active states

  // Category colours — muted
  food:         '#E07850',
  transport:    '#5B9FBF',
  shopping:     '#8B7BBF',
  health:       '#5BAF8E',
  emi:          '#C46B6B',
  investment:   '#5BAF8E',
  transfer:     '#6B8FD4',
  utilities:    '#C4A05C',
  education:    '#8B7BBF',
  daily:        '#C49060',
  others:       '#6B7280',

  // Confidence tiers
  high:         '#5BAF8E',
  medium:       '#C4A05C',
  low:          '#C46B6B',

  // Text
  textPrimary:   '#E8EAED',
  textSecondary: '#8B919E',
  textMuted:     '#4A5060',

  // Borders
  border:        '#23272F',
  borderBright:  '#2E333D',
};

export const CATEGORY_META = {
  food:          { label: 'Food & Dining',    icon: 'restaurant',   color: '#E07850' },
  transport:     { label: 'Transport',        icon: 'car',          color: '#5B9FBF' },
  shopping:      { label: 'Shopping',         icon: 'cart',         color: '#8B7BBF' },
  health:        { label: 'Health',           icon: 'heart',        color: '#5BAF8E' },
  emi:           { label: 'EMI & Loans',      icon: 'card',         color: '#C46B6B' },
  investment:    { label: 'Investment',       icon: 'trending-up',  color: '#5BAF8E' },
  transfer:      { label: 'Transfers',        icon: 'swap-horizontal', color: '#6B8FD4' },
  utilities:     { label: 'Utilities',        icon: 'flash',        color: '#C4A05C' },
  education:     { label: 'Education',        icon: 'school',       color: '#8B7BBF' },
  daily_expense: { label: 'Daily Expenses',   icon: 'wallet',       color: '#C49060' },
  others:        { label: 'Others',           icon: 'ellipsis-horizontal', color: '#6B7280' },
};

export const FONTS = {
  black:   { fontWeight: '900' },
  bold:    { fontWeight: '700' },
  semi:    { fontWeight: '600' },
  medium:  { fontWeight: '500' },
  regular: { fontWeight: '400' },
};

export const RADIUS = {
  sm:  8,
  md:  12,
  lg:  16,
  xl:  24,
  full: 999,
};

export const SHADOW = {
  card: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 4,
  },
  glow: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 6,
  },
};
