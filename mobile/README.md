# mobile/  — React Native (Expo) Finance App

Bold, dark, colorful — Cred-inspired design.

## Folder structure

```
mobile/
├── App.js                        ← root entry point
├── app.json                      ← Expo config
├── package.json
├── babel.config.js
└── src/
    ├── constants/
    │   └── theme.js              ← colors, fonts, shadows
    ├── services/
    │   ├── api.js                ← all backend API calls
    │   └── smsReader.js          ← Android SMS reading
    ├── store/
    │   └── useStore.js           ← Zustand global state
    ├── components/
    │   └── index.js              ← TransactionCard, KPICard, CategoryPicker...
    ├── screens/
    │   ├── DashboardScreen.js    ← home — KPIs, top category, recent txns
    │   ├── AnalyticsScreen.js    ← monthly charts and breakdowns
    │   ├── TransactionsScreen.js ← full list with category filter
    │   ├── AddSMSScreen.js       ← manual paste + Android bulk import
    │   └── AdviceScreen.js       ← 50/30/20, budgets, insights
    └── navigation/
        └── AppNavigator.js       ← tab + stack navigation
```

## Setup

### 1. Install Expo CLI (once)
```bash
npm install -g expo-cli
```

### 2. Install app dependencies
```bash
cd mobile
npm install
```

### 3. Point the app to your backend
Open `src/services/api.js` and update `API_BASE`:

```js
// For Android emulator:
const API_BASE = 'http://10.0.2.2:8000';

// For real Android phone on same WiFi:
// Find your PC's IP: run ipconfig → IPv4 Address
const API_BASE = 'http://192.168.1.XXX:8000';

// For iOS simulator:
const API_BASE = 'http://localhost:8000';
```

### 4. Start the app
```bash
npx expo start
```

This opens a QR code. Scan it with:
- **Android**: Expo Go app (install from Play Store)
- **iOS**: Camera app (scan → opens in Expo Go)

Or press:
- `a` → Android emulator
- `i` → iOS simulator

## Screens

| Screen | What it does |
|---|---|
| 🏠 Dashboard | Hero spend card, KPIs, category bar, recent 8 transactions |
| 📋 Transactions | Full paginated list, filter by category, tap to correct |
| ➕ Add | Paste SMS manually OR bulk import (Android) |
| 📊 Analytics | Monthly KPIs, category bars, daily trend chart, top merchants |
| 🧠 Advice | 50/30/20 analysis, per-category budgets, insights, recurring detection |

## Category correction

Tap any transaction → bottom sheet appears → pick correct category.
This calls `PATCH /correct` on the backend and updates the display immediately.
Confidence dots: 🟢 ≥85% · 🟡 60–85% · 🔴 <60%

## Android SMS permissions

The `READ_SMS` permission is declared in `app.json`.
When you build an APK, Android will ask the user to grant it.
During Expo Go testing, SMS reading may require a dev build.

## Building for real devices

```bash
# Install EAS CLI
npm install -g eas-cli

# Build Android APK
eas build --platform android --profile preview

# Build iOS IPA (requires Apple Developer account)
eas build --platform ios
```
