"""
services/parser.py
------------------
Extracts structured fields from raw SMS text using regex.
No ML here — pure pattern matching.

Returns a dict with: amount, merchant, bank, transaction_type, received_at
"""

import re
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Amount extraction
# ---------------------------------------------------------------------------

AMOUNT_PATTERNS = [
    r"(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d{1,2})?)",   # INR 500 / Rs. 500 / ₹500
    r"([\d,]+(?:\.\d{1,2})?)\s*(?:INR|Rs\.?|₹)",   # 500 INR / 500 Rs
    r"(?:debited|credited|paid|spent|charged)\s+(?:with\s+)?(?:INR|Rs\.?|₹)?\s*([\d,]+(?:\.\d{1,2})?)",
    r"(?:amount|amt)\s*(?:of\s+)?(?:INR|Rs\.?|₹)?\s*([\d,]+(?:\.\d{1,2})?)",
]

def extract_amount(text: str) -> Optional[float]:
    for pattern in AMOUNT_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(1).replace(",", "")
            try:
                return float(raw)
            except ValueError:
                continue
    return None


# ---------------------------------------------------------------------------
# Transaction type  (debit vs credit)
# ---------------------------------------------------------------------------

DEBIT_KEYWORDS = [
    "debited", "debit", "paid", "payment", "spent", "charged",
    "withdrawn", "withdrawal", "purchase", "sent", "transferred to",
]
CREDIT_KEYWORDS = [
    "credited", "credit", "received", "refund", "cashback",
    "transferred from", "deposited", "added",
]

def extract_type(text: str) -> str:
    t = text.lower()
    for kw in CREDIT_KEYWORDS:
        if kw in t:
            return "credit"
    for kw in DEBIT_KEYWORDS:
        if kw in t:
            return "debit"
    return "debit"  # default assumption


# ---------------------------------------------------------------------------
# Bank / sender extraction
# ---------------------------------------------------------------------------

BANK_PATTERNS = {
    "HDFC Bank":   r"\bhdfc\b",
    "ICICI Bank":  r"\bicici\b",
    "SBI":         r"\bsbi\b|\bstate bank\b",
    "Axis Bank":   r"\baxis bank\b",
    "Kotak":       r"\bkotak\b",
    "Yes Bank":    r"\byes bank\b",
    "PNB":         r"\bpnb\b|\bpunjab national\b",
    "IDFC First":  r"\bidfc\b",
    "IndusInd":    r"\bindusind\b",
    "Bank of Baroda": r"\bbob\b|\bbank of baroda\b",
    "Paytm":       r"\bpaytm\b|\bppbl\b",
    "PhonePe":     r"\bphonepe\b",
    "GPay":        r"\bgpay\b|\bgoogle pay\b",
    "Simpl":       r"\bsimpl\b",
    "LazyPay":     r"\blazypay\b",
}

def extract_bank(text: str) -> Optional[str]:
    t = text.lower()
    for bank, pattern in BANK_PATTERNS.items():
        if re.search(pattern, t):
            return bank
    return None


# ---------------------------------------------------------------------------
# Merchant extraction
# ---------------------------------------------------------------------------

# Known merchant keywords — ordered by specificity
KNOWN_MERCHANTS = [
    # Food
    "Swiggy", "Zomato", "Blinkit", "Zepto", "BigBasket",
    "Dunzo", "Faasos", "McDonald", "KFC", "Domino", "Subway",
    "Starbucks", "Pizza Hut",
    # Transport
    "Uber", "Ola", "Rapido", "IRCTC", "IndiGo", "SpiceJet",
    "Air India", "Vistara", "MakeMyTrip", "Yatra", "Goibibo",
    "Fastag",
    # Shopping
    "Amazon", "Flipkart", "Myntra", "Meesho", "Nykaa", "Ajio",
    # Health
    "Apollo", "Netmeds", "PharmEasy", "1mg", "MedPlus",
    # Finance
    "Zerodha", "Groww", "Upstox",
    # Utilities
    "Airtel", "Jio", "Netflix", "Hotstar", "Spotify", "Prime",
]

MERCHANT_PATTERN = "|".join(re.escape(m) for m in KNOWN_MERCHANTS)

# Generic "at <merchant>" patterns
AT_PATTERNS = [
    r"(?:at|@)\s+([A-Z][A-Za-z0-9\s&]{2,30}?)(?:\s+on|\s+for|\s+via|\.|,|$)",
    r"(?:paid to|sent to|transferred to)\s+([A-Z][A-Za-z0-9\s&]{2,30}?)(?:\s+on|\s+for|\s+via|\.|,|$)",
    r"(?:purchase at|txn at|spent at)\s+([A-Z][A-Za-z0-9\s&]{2,30}?)(?:\s+on|\s+for|\s+via|\.|,|$)",
]

def extract_merchant(text: str) -> Optional[str]:
    # First: check known merchants
    match = re.search(MERCHANT_PATTERN, text, re.IGNORECASE)
    if match:
        return match.group(0).title()

    # Second: generic "at <name>" pattern
    for pattern in AT_PATTERNS:
        match = re.search(pattern, text)
        if match:
            merchant = match.group(1).strip()
            if len(merchant) > 2:
                return merchant

    return None


# ---------------------------------------------------------------------------
# Date extraction
# ---------------------------------------------------------------------------

DATE_PATTERNS = [
    r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",                    # 05/07/2024
    r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})",
    r"(\d{4}-\d{2}-\d{2})",                                 # 2024-05-07
]

DATE_FORMATS = [
    "%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y", "%d/%m/%y",
    "%d %b %Y", "%d %B %Y",
    "%Y-%m-%d",
]

def extract_date(text: str) -> Optional[datetime]:
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(1)
            for fmt in DATE_FORMATS:
                try:
                    return datetime.strptime(raw, fmt)
                except ValueError:
                    continue
    return None


# ---------------------------------------------------------------------------
# Account number (masked) — useful for grouping by account
# ---------------------------------------------------------------------------

def extract_account(text: str) -> Optional[str]:
    match = re.search(r"(?:a/c|acct?|account)\s*(?:no\.?|number)?\s*[xX*]{0,6}(\d{4})", text, re.IGNORECASE)
    if match:
        return f"XX{match.group(1)}"
    match = re.search(r"[xX*]{2,}\d{4}", text)
    if match:
        return match.group(0).upper()
    return None


# ---------------------------------------------------------------------------
# Main parse function
# ---------------------------------------------------------------------------

def parse_sms(text: str) -> dict:
    """
    Parses a single SMS string and returns all extracted fields.
    Returns empty/None values for fields it can't extract — never raises.
    """
    return {
        "amount":           extract_amount(text),
        "merchant":         extract_merchant(text),
        "bank":             extract_bank(text),
        "transaction_type": extract_type(text),
        "received_at":      extract_date(text),
        "account":          extract_account(text),
    }
