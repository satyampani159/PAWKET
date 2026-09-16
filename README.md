# PAWKET — Your Wise Financial Watchdog

> An AI-powered personal finance app that automatically reads bank SMS messages, categorises spending into 10 categories using machine learning, detects recurring financial patterns, and delivers personalised budgeting advice based on the 50/30/20 rule — all from your phone.

---

## Screenshots

| Welcome | Login | Dashboard |
|---------|-------|-----------|
| ![Welcome](docs/screenshots/welcome.png) | ![Login](docs/screenshots/login.png) | ![Dashboard](docs/screenshots/dashboard.png) |

| Analytics | Transactions | Advice | Profile |
|-----------|-------------|--------|---------|
| ![Analytics](docs/screenshots/analytics.png) | ![Transactions](docs/screenshots/transactions.png) | ![Advice](docs/screenshots/advice.png) | ![Profile](docs/screenshots/profile.png) |

> **Note:** All screenshots show the app running on **test/simulated data**, not real bank SMS. See [Data Disclaimer](#data-disclaimer) for details.

---

## How It Works — End-to-End Flow

PAWKET follows a multi-stage pipeline to transform raw SMS text into actionable financial insights:

```
Android SMS Inbox
       │
       ▼
┌─────────────────┐
│  SMS Reader      │  react-native-get-sms-android (90-day window)
│  (Mobile App)    │  Local filtering for financial keywords (debited, credited, INR, UPI...)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Filter Model    │  TF-IDF + SGDClassifier (binary)
│  (ML Stage 1)    │  Classifies: bank SMS (1) vs OTP/spam/promo (0)
│  Accuracy: 98%   │  Non-financial messages are discarded here
└────────┬────────┘
         │ financial SMS only
         ▼
┌─────────────────┐
│  Regex Parser    │  Extracts: amount, transaction type, bank, merchant, date, account
│  (Backend)       │  15 Indian bank patterns, 30+ merchant recognitions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Deduplication   │  Detects UPI app + bank duplicate SMS
│  (Backend)       │  Exact text match + amount+time window (5 min, ±₹1)
└────────┬────────┘
         │ unique transactions only
         ▼
┌─────────────────┐
│  Category Model  │  TF-IDF + SGDClassifier (10-class)
│  (ML Stage 2)    │  Confidence > 60% → use ML prediction
│  Accuracy: 98%   │  Confidence < 60% → fallback to pattern engine
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  User Correction │  Tap any transaction to fix category
│  (Active Learn)  │  User corrections override ML + pattern engine
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Analytics       │  Monthly KPIs, category breakdown, daily trend, top merchants
│  + Advice        │  50/30/20 rule, budget limits, recurring detection, personalised insights
└─────────────────┘
```

---

## Features

### Core Functionality
- **Auto SMS Reading** — reads bank messages on first launch, no manual entry required
- **Two-Stage ML Pipeline** — filter model discards non-financial SMS, category model classifies spending
- **Smart Deduplication** — detects UPI app + bank duplicate SMS automatically using amount+time window matching
- **Confidence Scoring** — shows prediction confidence with colour-coded indicators (green > 80%, yellow 60-80%, red < 60%)
- **User Corrections** — tap any transaction to fix its category (active learning loop)

### Analytics & Insights
- **Monthly KPIs** — total spend, average transaction, largest transaction, net income
- **Category Breakdown** — horizontal bar chart with percentage distribution across 10 categories
- **Daily Spend Trend** — bar chart showing spending patterns across days of the month
- **Top Merchants** — ranked list of merchants by total spend
- **50/30/20 Rule** — needs/wants/savings analysis based on income and spending
- **Budget Limits** — per-category budget recommendations as percentage of income
- **Recurring Detection** — identifies EMIs, subscriptions, rent, and other recurring payments
- **Personalised Insights** — overspending warnings, savings tips, food budget alerts

### Profile & Auth
- **OTP Login** — phone number authentication (currently in dev mode, see [Development Mode](#development-mode))
- **User Profile** — name, email, gender, age, financial goal, monthly income
- **Financial Goals** — goal-specific advice (save more, reduce debt, build emergency fund, invest more)

### UI/UX
- **Animated Welcome** — Doberman logo traces itself on launch
- **Dark Theme** — Cred-inspired design with electric violet + hot pink gradients
- **5-Tab Navigation** — Home, Transactions, Analytics, Advice, Profile
- **Filterable Transaction List** — filter by category with paginated results

---

## ML Models — Technical Details

### Architecture

Both models use **TF-IDF vectorisation** followed by **SGDClassifier** (Stochastic Gradient Descent with logistic loss). This combination was chosen for:
- **Speed**: SGD trains in seconds on 100K samples, suitable for frequent retraining
- **Memory**: TF-IDF sparse matrices + linear classifier = ~4MB total model size
- **Accuracy**: competitive with more complex models on text classification tasks

```python
Pipeline: TfidfVectorizer(max_features=50000, ngram_range=(1,2), sublinear_tf=True)
           → SGDClassifier(loss='log_loss', max_iter=1000, random_state=42)
```

### Filter Model (Bank SMS vs Non-Financial)

| Metric | Value |
|--------|-------|
| **Task** | Binary classification — bank transaction SMS vs OTP/spam/promotional |
| **Accuracy** | 98% |
| **Algorithm** | TF-IDF + SGDClassifier |
| **Features** | Up to 50,000 unigram + bigram features |
| **Training Data** | ~100,000 Indian SMS messages (`SMS-Data.csv`, 30MB) |
| **Model File** | `filter_model.pkl` (1.4 MB) |
| **Label Generation** | Automated keyword rules in `label_rules.py` (not human-annotated) |

**How it works**: The filter model acts as the first gate. Every incoming SMS is classified as either a bank/financial message (class 1) or non-financial (class 0). OTP messages, promotional SMS, spam, and unrelated messages are discarded at this stage, preventing false positives from entering the categorisation pipeline.

### Category Model (10-Class Spending Classifier)

| Metric | Value |
|--------|-------|
| **Task** | Multi-class classification across 10 spending categories |
| **Accuracy** | 98% (weighted average F1) |
| **Algorithm** | TF-IDF + SGDClassifier |
| **Features** | Up to 50,000 unigram + bigram features |
| **Training Data** | Same ~100,000 SMS dataset |
| **Model File** | `category_model.pkl` (2.9 MB) |

**Categories and per-class performance:**

| Category | F1 Score | Description |
|----------|----------|-------------|
| `education` | 1.00 | Udemy, Coursera, tuition, school fees |
| `utilities` | 0.98 | Airtel, Jio, Netflix, Spotify, electricity |
| `investment` | 0.98 | Zerodha, Groww, mutual funds, SIP |
| `emi` | 0.97 | Loan EMIs, credit card payments |
| `food` | 0.96 | Swiggy, Zomato, Starbucks, restaurants |
| `shopping` | 0.96 | Amazon, Flipkart, Myntra |
| `transfer` | 0.95 | UPI transfers, bank-to-bank |
| `others` | 0.93 | Uncategorized financial transactions |
| `health` | 0.88 | Apollo, PharmEasy, medical expenses |
| `transport` | 0.84 | Uber, Ola, petrol, parking |

**Two-stage categorisation logic:**
1. **Stage 1 — ML Prediction**: TF-IDF + SGDClassifier predicts category with confidence score
2. **Stage 2 — Pattern Fallback**: If ML confidence < 60% or prediction is "others", the pattern engine kicks in using merchant name matching and amount+time-of-day rules
3. **Priority**: User correction > pattern engine > ML prediction

### Training Pipeline

```bash
# Train both models
cd ml_pipeline
py train_filter.py --data data/SMS-Data.csv
py train_category.py --data data/SMS-Data.csv

# Evaluate with confusion matrices + classification reports
py evaluate.py --data data/SMS-Data.csv

# Copy trained models to backend
xcopy models ..\backend\ml\models /E /I
```

Output includes:
- `filter_model.pkl` — binary filter model
- `category_model.pkl` — 10-class category model
- `filter_confusion_matrix.png` — confusion matrix for filter
- `category_confusion_matrix.png` — confusion matrix for category
- `category_report.txt` — precision/recall/F1 per category

### Pattern Engine Fallback

When the ML model is uncertain, the pattern engine uses rule-based logic:

1. **Merchant Matching**: 30+ known merchants mapped to categories (Swiggy→food, Uber→transport, etc.)
2. **Amount + Time-of-Day Rules**: Large evening transactions → food, small late-night → transport
3. **Bank-Specific Patterns**: HDFC loan debits → emi, Zerodha credits → investment
4. **Keyword Fallback**: "subscription" → utilities, "tuition" → education

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check with ML model status |
| `GET` | `/health` | Full health check (DB + ML models) |
| `POST` | `/auth/request-otp` | Request OTP for phone login |
| `POST` | `/auth/verify-otp` | Verify OTP, create session |
| `GET` | `/auth/me` | Get current user profile |
| `DELETE` | `/auth/logout` | Invalidate session |
| `POST` | `/parse` | Parse single SMS text |
| `POST` | `/parse/batch` | Parse up to 500 SMS in batch |
| `GET` | `/analytics` | Monthly KPIs, category breakdown, daily trend |
| `GET` | `/analytics/months` | List available months |
| `GET` | `/analytics/transactions` | Paginated transaction list |
| `PATCH` | `/correct` | User corrects a transaction category |
| `GET` | `/advice` | 50/30/20 analysis, budgets, insights, recurring |

Full interactive API docs available at `/docs` (Swagger UI) when the backend is running.

---

## Data Disclaimer

**The app currently operates on test/simulated data, not real bank SMS from a live phone.**

### Why?

Google's Android security model restricts third-party apps from reading SMS messages without explicit user consent and the `READ_SMS` permission. However, starting with Android 13+, Google Play enforces additional restrictions:

1. **SMS Permission Revocation** — Google can revoke SMS read permissions from apps that don't meet their SMS app criteria
2. **Play Store Policy** — Apps must demonstrate they are the default SMS handler or have a legitimate use case for reading SMS
3. **Consent Flow** — Even with permission granted, the OS shows a system dialog that many users deny
4. **Scoped Storage** — Android 11+ limits direct access to SMS content provider for non-default SMS apps

These restrictions mean that while PAWKET's architecture supports real SMS reading via `react-native-get-sms-android`, **direct phone SMS import is blocked by Google's security policies for third-party apps**. The app cannot reliably read bank SMS from the phone in a production environment without becoming the default SMS handler.

### Current State

- **Test data source**: `backend/test_seed.py` generates ~70 realistic fake Indian bank SMS messages across all categories (food, transport, shopping, EMI, utilities, health, investment, education, transfer)
- **Auto-seeding**: `backend/services/auto_seed.py` inserts 50+ test transactions directly into the database on server startup (for Render deployments where DB resets)
- **ML models trained on real data**: The filter and category models were trained on ~100,000 real Indian SMS messages (`SMS-Data.csv`), so the ML pipeline itself is production-ready
- **Backend fully functional**: All endpoints (parse, analytics, advice, deduplication) work correctly with the test data

### What Would Be Needed for Production

1. **Default SMS App Registration** — Register PAWKET as the default SMS handler on Android (requires user consent and Google Play approval)
2. **SMS Backup API** — Use Android's `SmsContract` API through a backup/restore flow rather than direct reading
3. **Alternative Data Sources** — Bank API integrations via Account Aggregator framework (RBI-regulated) instead of SMS reading
4. **Manual Import** — Allow users to export SMS from their default SMS app and import into PAWKET

---

## Development Mode

### OTP Authentication

In development, the OTP system operates in **dev mode**:
- When a user requests an OTP, it is **printed to the backend console** instead of being sent via SMS
- The OTP is valid for 5 minutes and works identically to a production OTP flow
- This eliminates the need for an SMS gateway integration during development

```
[DEV MODE] OTP for +919876543210: 482916
```

### SMS Import

Since real SMS import is blocked by Google's security policies, the app uses:
- **Manual SMS paste**: Users can paste raw SMS text into the app for parsing
- **Test seed data**: Pre-loaded realistic transactions for demo purposes
- **Batch API**: `POST /parse/batch` accepts up to 500 SMS texts at once

---

## Architecture

```
PAWKET/
├── ml_pipeline/              Python — ML training pipeline
│   ├── data/
│   │   └── SMS-Data.csv      ~30MB dataset (~100K Indian SMS)
│   ├── models/
│   │   ├── filter_model.pkl        Bank vs spam classifier (1.4MB)
│   │   └── category_model.pkl      10-category classifier (2.9MB)
│   ├── label_rules.py        Keyword rules for auto-labelling training data
│   ├── train_filter.py       Trains binary filter model
│   ├── train_category.py     Trains 10-class category model
│   └── evaluate.py           Confusion matrices + classification reports
│
├── backend/                  Python FastAPI — REST API server
│   ├── main.py               App entrypoint, lifespan, CORS, router registration
│   ├── routers/              REST endpoint handlers
│   │   ├── auth.py           OTP login, session tokens, /me, logout
│   │   ├── parse.py          POST /parse and /parse/batch — core SMS processing
│   │   ├── analytics.py      GET /analytics, /transactions, /months
│   │   ├── correct.py        PATCH /correct — user category corrections
│   │   ├── advice.py         GET /advice — 50/30/20, insights, recurring
│   │   └── profile.py        GET/PATCH /profile — user profile management
│   ├── services/             Business logic layer
│   │   ├── parser.py         Regex-based SMS field extraction
│   │   ├── categorizer.py    Two-stage: ML model + pattern engine fallback
│   │   ├── analytics.py      Monthly KPIs, category breakdown, daily trend
│   │   ├── finance_rules.py  50/30/20 rule, budgets, recurring detection
│   │   ├── deduplication.py  UPI + bank duplicate SMS detection
│   │   └── auto_seed.py      Auto-seeds test data on empty DB
│   ├── ml/
│   │   └── ml_loader.py      Loads .pkl models at startup, prediction interface
│   ├── database/
│   │   └── database.py       SQLAlchemy models (User, OTP, Session, Transaction, etc.)
│   └── models/
│       └── schemas.py        Pydantic request/response schemas
│
└── mobile/                   React Native (Expo) — Android + iOS app
    ├── App.js                Root component: Welcome → Login → Onboarding → AppNavigator
    ├── src/
    │   ├── screens/          8 screens (Welcome, Login, Onboarding, Dashboard, etc.)
    │   ├── components/       TransactionCard, KPICard, CategoryBadge, etc.
    │   ├── services/         API client, auth, SMS reader
    │   ├── store/            Zustand global state management
    │   ├── navigation/       Bottom tab navigator (5 tabs)
    │   └── constants/        Theme, colours, category metadata
    └── assets/
        └── logo.png          Doberman app icon
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **ML Pipeline** | Python 3.12+, scikit-learn | TF-IDF + SGDClassifier for SMS classification |
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy 2.0 | REST API server with async support |
| **Database** | SQLite (SQLAlchemy ORM) | Transaction storage, user data, sessions |
| **Validation** | Pydantic 2.0 | Request/response schema validation |
| **Mobile** | React Native 0.81, Expo SDK 54 | Cross-platform mobile app |
| **State** | Zustand 4.5 | Lightweight global state management |
| **Navigation** | React Navigation 6 | Bottom tab navigator |
| **Auth** | Phone OTP, session tokens | `secrets.token_urlsafe` for token generation |
| **SMS Reader** | react-native-get-sms-android | Android native SMS access (90-day window) |
| **Deployment** | Render (backend), EAS Build (mobile) | Cloud hosting + native builds |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Expo CLI (`npm install -g expo-cli`)
- Android device or emulator (for SMS reading feature)

### 1. Train the ML Models

```bash
cd ml_pipeline
pip install -r requirements.txt

# Place your SMS dataset in ml_pipeline/data/SMS-Data.csv
py train_filter.py --data data/SMS-Data.csv
py train_category.py --data data/SMS-Data.csv
py evaluate.py --data data/SMS-Data.csv

# Copy trained models to backend
xcopy models ..\backend\ml\models /E /I
```

### 2. Run the Backend

```bash
cd backend
pip install -g expo-cli
py -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# API docs: http://localhost:8000/docs
```

### 3. Run the Mobile App

```bash
cd mobile
npm install
npx expo start
```

Scan the QR code with **Expo Go** on your Android phone.

For a production build with SMS reading:
```bash
eas build --platform android --profile preview
```

### 4. Seed Test Data

The backend auto-seeds 50+ test transactions on startup when the database is empty. To manually seed:

```bash
cd backend
py test_seed.py
```

This authenticates via OTP (dev mode), then sends ~70 realistic fake SMS to the parse endpoint.

---

## Deployment

**Backend** is deployed on **Render**: `https://pawket-backend.onrender.com`

### Deploy Your Own

1. Push backend to GitHub
2. Connect to [render.com](https://render.com)
3. Select the `backend/` folder
4. Deploy — the Dockerfile handles the rest

After deployment, update the mobile app's API URL:
```bash
cd backend
py update_api_url.py https://your-app.onrender.com
```

### Environment Variables

Create `backend/.env`:
```
ML_MODELS_DIR=ml/models
DATABASE_URL=sqlite:///./finance.db
CORS_ORIGINS=*
```

---

## Database Schema

Six tables via SQLAlchemy ORM:

| Table | Purpose |
|-------|---------|
| `users` | Phone, name, email, gender, age, financial_goal, monthly_income |
| `otp_records` | OTP storage with expiry and usage tracking |
| `sessions` | Session tokens with user_id, expiry, active flag |
| `transactions` | Full transaction record: raw SMS, parsed fields, ML prediction, user correction |
| `recurring_patterns` | Detected recurring payments: label, merchant, amount, frequency |
| `monthly_summaries` | Pre-computed monthly aggregates for fast dashboard loading |

---

## Known Limitations

1. **SMS Import Blocked by Google** — Cannot directly read bank SMS from phone due to Android security restrictions on third-party apps (see [Data Disclaimer](#data-disclaimer))
2. **Dev OTP Only** — OTP is printed to console, not sent via SMS (no SMS gateway integration)
3. **Test Data Only** — Current demo uses simulated transactions, not real bank data
4. **Android Only** — SMS reading uses Android-specific APIs; iOS not supported for auto-import
5. **Single Bank Account** — No multi-account support yet
6. **No Push Notifications** — Not implemented yet

---

## Roadmap

- [ ] Push notifications for large transactions
- [ ] Budget alerts when category limit exceeded
- [ ] Export to PDF / CSV
- [ ] Compare month vs previous month
- [ ] Multi-bank account support
- [ ] Account Aggregator API integration (bypass Google SMS restrictions)
- [ ] Web dashboard
- [ ] iOS App Store release
- [ ] SMS gateway integration for OTP delivery

---

## License

MIT License — free to use, modify, and distribute.
