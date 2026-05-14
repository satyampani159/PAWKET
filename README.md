# 🐕 PAWKET — Your Wise Financial Watchdog

> An AI-powered personal finance app that automatically reads your bank SMS, categorises spending, detects patterns, and gives personalised financial advice.

---

## 📱 Screenshots

<!-- Add screenshots here after first build -->
<!-- ![Welcome Screen](docs/screenshots/welcome.png) -->
<!-- ![Dashboard](docs/screenshots/dashboard.png) -->
<!-- ![Analytics](docs/screenshots/analytics.png) -->

---

## ✨ Features

- **Auto SMS Reading** — reads bank messages on first launch, no manual entry
- **ML Categorisation** — 99% accuracy, 10 categories (food, EMI, transport, investment...)
- **Smart Deduplication** — detects UPI app + bank duplicate SMS automatically
- **Confidence Scoring** — shows prediction confidence with colour-coded dots 🟢🟡🔴
- **User Corrections** — tap any transaction to fix category (active learning)
- **Monthly Analytics** — KPIs, category breakdown, daily trend, top merchants
- **50/30/20 Advice** — personalised financial advice based on your spending + goals
- **Recurring Detection** — automatically identifies EMIs, subscriptions, rent
- **Profile System** — name, gender, age, financial goals, income
- **OTP Login** — phone number authentication, your data stays private
- **Animated Welcome** — Doberman logo traces itself on every launch
- **Bold Dark UI** — Cred-inspired design, electric violet + hot pink

---

## 🏗️ Architecture

```
PAWKET/
├── ml_pipeline/          Python — trains the two ML models
│   ├── label_rules.py    keyword rules for categorisation
│   ├── train_filter.py   bank vs spam classifier
│   ├── train_category.py spending category classifier
│   └── evaluate.py       model evaluation + reports
│
├── backend/              Python FastAPI — REST API server
│   ├── routers/          parse, analytics, advice, correct, profile, auth
│   ├── services/         parser, categorizer, analytics, finance_rules, deduplication
│   ├── ml/               loads trained .pkl models at startup
│   └── database/         SQLite via SQLAlchemy
│
└── mobile/               React Native (Expo) — Android + iOS app
    ├── src/screens/      Dashboard, Analytics, Transactions, Advice, Profile
    ├── src/services/     API calls, SMS reader, auth
    ├── src/store/        Zustand global state
    └── src/components/   TransactionCard, KPICard, CategoryPicker...
```

---

## 🤖 ML Models

| Model | Task | Accuracy |
|---|---|---|
| Filter model | Bank SMS vs spam/OTP | **98%** |
| Category model | 10-category spending classifier | **99%** |

**Tech:** TF-IDF + SGDClassifier (scikit-learn)
**Training data:** ~100,000 real Indian SMS messages
**Categories:** food · transport · shopping · health · emi · investment · transfer · utilities · education · daily_expense

---

## 🚀 Getting Started

### 1. Train the ML models

```bash
cd ml_pipeline
pip install -r requirements.txt

# Put your SMS dataset in ml_pipeline/data/SMS-Data.csv
py train_filter.py --data data/SMS-Data.csv
py train_category.py --data data/SMS-Data.csv
py evaluate.py --data data/SMS-Data.csv

# Copy models to backend
xcopy models ..\backend\ml\models /E /I
```

### 2. Run the backend

```bash
cd backend
pip install -r requirements.txt
py -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# API docs available at:
# http://localhost:8000/docs
```

### 3. Run the mobile app

```bash
cd mobile
npm install
npx expo start
```

Scan the QR code with **Expo Go** on your phone.

For a full build with SMS reading:
```bash
eas build --platform android --profile preview
```

---

## 🌐 Deployment

Backend is deployed on **Render**: `https://pawket-backend.onrender.com`

To deploy your own:
1. Push backend to GitHub
2. Connect to [render.com](https://render.com)
3. Select the `backend/` folder
4. Deploy — `render.yaml` handles the rest

After deployment update the mobile app:
```bash
cd backend
py update_api_url.py https://your-app.onrender.com
```

---

## 🔑 Environment Variables

Create `backend/.env`:
```
ML_MODELS_DIR=ml/models
DATABASE_URL=sqlite:///./finance.db
CORS_ORIGINS=*
```

---

## 📦 Tech Stack

| Layer | Tech |
|---|---|
| ML | Python, scikit-learn, TF-IDF, SGDClassifier |
| Backend | FastAPI, SQLAlchemy, SQLite, Pydantic |
| Mobile | React Native, Expo, Zustand, React Navigation |
| Auth | Phone OTP, JWT-style session tokens |
| Deployment | Render (backend), EAS Build (mobile) |

---

## 🗺️ Roadmap

- [ ] Push notifications for large transactions
- [ ] Budget alerts when category limit exceeded
- [ ] Export to PDF / CSV
- [ ] Compare month vs previous month
- [ ] Multi-bank account support
- [ ] Web dashboard
- [ ] iOS App Store release

---

## 👨‍💻 Author

**Satyam Pani**
Built with Claude AI assistance

---

## 📄 License

MIT License — free to use, modify, and distribute.
