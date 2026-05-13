"""
label_rules.py
--------------
Single source of truth for all keyword-based labeling.
Both train_filter.py and train_category.py import from here.
When you want to improve accuracy, edit this file only.
"""

import re


# ---------------------------------------------------------------------------
# FILTER RULES  (is this a financial/bank SMS at all?)
# ---------------------------------------------------------------------------

# Strong signals that a message is a bank / financial transaction
FINANCIAL_POSITIVE_PATTERNS = [
    r"\bINR\b",
    r"\bRs\.?\s*\d",           # Rs 500 / Rs. 500 / Rs500
    r"\bdebited\b",
    r"\bcredited\b",
    r"\bdebit\b",
    r"\bcredit\b",
    r"\bwithdrawn\b",
    r"\bwithdrawal\b",
    r"\btransfer(red)?\b",
    r"\bpayment\b",
    r"\bpaid\b",
    r"\breceived\b",
    r"\brefund\b",
    r"\bemi\b",
    r"\bdue\b",
    r"\ba/c\b",
    r"\baccount\b",
    r"\bbalance\b",
    r"\bavl bal\b",
    r"\bavailable balance\b",
    r"\bupi\b",
    r"\bneft\b",
    r"\bimps\b",
    r"\brtgs\b",
    r"\batm\b",
    r"\bpos\b",
    r"\bspent\b",
    r"\btransaction\b",
    r"\bcharged\b",
    r"\bmobile banking\b",
    r"\bnet banking\b",
    r"\bwalletf?\b",
    r"\bpayment successful\b",
    r"\border (placed|confirmed|delivered)\b",
    r"\binvoice\b",
    r"\bsimpl\b",
    r"\blazypay\b",
    r"\bpaytm\b",
    r"\bphonepe\b",
    r"\bgpay\b",
    r"\bgoogle pay\b",
    r"\bbill (paid|generated|due)\b",
    r"\brecharge\b",            # mobile/DTH recharge = money spent
]

# Patterns that are strong signals the SMS is NOT financial
# (OTPs, promotional, spam, social updates)
FINANCIAL_NEGATIVE_PATTERNS = [
    r"\botp\b",
    r"\bone.time.password\b",
    r"\bverification code\b",
    r"\bverify\b",
    r"\bis your (zomato|swiggy|uber|ola|paytm|amazon)\b",
    r"\bclick here\b",
    r"\bdownload (the )?app\b",
    r"\bearn up to\b",
    r"\bjoin now\b",
    r"\bwatch (this )?video\b",
    r"\bfree\b.{0,30}\boffer\b",
    r"\bwin\b.{0,20}\bprize\b",
    r"\bcongratulations\b",
    r"\byou('ve| have) won\b",
    r"\bsubscribe\b",
    r"\bunsubscribe\b",
    r"\bupdate your (email|id|profile)\b",
]


def is_financial(text: str) -> int:
    """
    Returns 1 if the SMS is a financial/bank message, 0 otherwise.
    Logic: must match at least one positive pattern AND
           not be dominated by negative patterns.
    """
    t = text.lower()

    neg_hits = sum(1 for p in FINANCIAL_NEGATIVE_PATTERNS if re.search(p, t))
    pos_hits = sum(1 for p in FINANCIAL_POSITIVE_PATTERNS if re.search(p, t))

    # Hard veto: clear OTP / verification message
    if re.search(r"\botp\b|\bverification code\b|\bone.time.password\b", t):
        return 0

    # Needs at least 1 positive signal and more positive than negative
    if pos_hits >= 1 and pos_hits > neg_hits:
        return 1

    return 0


# ---------------------------------------------------------------------------
# CATEGORY RULES  (what kind of spending is this?)
# ---------------------------------------------------------------------------

# Order matters — first match wins.
# Put more-specific rules before more-general ones.

CATEGORY_RULES = [
    # ---- Food & Dining ----
    (
        "food",
        [
            r"\bswiggy\b", r"\bzomato\b", r"\bubereats\b", r"\bfaasos\b",
            r"\bdunzo\b", r"\bblinkit\b", r"\bzepto\b", r"\binstamrt\b",
            r"\bbigbasket\b", r"\bgrofer\b", r"\bjiomart\b",
            r"\brestaurant\b", r"\bcafe\b", r"\bdining\b", r"\bfood\b",
            r"\bpizza\b", r"\bburger\b", r"\bmcdonald\b", r"\bkfc\b",
            r"\bdomino\b", r"\bsubway\b", r"\bstarbucks\b", r"\bccd\b",
            r"\bgroceri\b", r"\bsupermarket\b", r"\bbakery\b",
        ],
    ),
    # ---- Transport & Travel ----
    (
        "transport",
        [
            r"\buber\b", r"\bola\b", r"\brapido\b", r"\bnamma metro\b",
            r"\btrip ended\b", r"\bride completed\b", r"\bride ended\b",
            r"\bmetro\b", r"\bauto\b", r"\bcab\b", r"\btaxi\b",
            r"\birctc\b", r"\btrain\b", r"\bflight\b", r"\bairline\b",
            r"\bindigo\b", r"\bspicejet\b", r"\bair india\b", r"\bvistara\b",
            r"\bbus\b", r"\bboat\b", r"\bferry\b",
            r"\bmakemytrip\b", r"\byatra\b", r"\bgoibibo\b", r"\bcleartrip\b",
            r"\bfuel\b", r"\bpetrol\b", r"\bdiesel\b", r"\bparking\b",
            r"\btoll\b", r"\bfastag\b",
        ],
    ),
    # ---- Shopping & E-commerce ----
    (
        "shopping",
        [
            r"\bamazon\b", r"\bflipkart\b", r"\bmyntra\b", r"\bajio\b",
            r"\bmeesho\b", r"\bnykaa\b", r"\bpuma\b", r"\bnikee?\b",
            r"\badidas\b", r"\bzara\b", r"\bh&m\b", r"\bwestside\b",
            r"\bshoppin\b", r"\bpurchase\b", r"\border (placed|confirmed)\b",
            r"\bdelivery\b", r"\bshipment\b",
        ],
    ),
    # ---- Health & Medical ----
    (
        "health",
        [
            r"\bpharmac\b", r"\bmedical\b", r"\bhospital\b", r"\bclinic\b",
            r"\bdoctor\b", r"\blab\b", r"\btest report\b", r"\bdiagnostic\b",
            r"\bapollo\b", r"\bnetmeds\b", r"\b1mg\b", r"\bpharmeas\b",
            r"\bpharmeasy\b", r"\bmedicine\b", r"\bconsultation\b",
            r"\bhealthcare\b", r"\binsurance premium\b", r"\bhealth insurance\b",
            r"\bpharmacy\b", r"\bdental\b", r"\bsurgery\b", r"\bmedplus\b",
        ],
    ),
    # ---- EMI & Loans ----
    (
        "emi",
        [
            r"\bemi\b", r"\bloan\b", r"\brepayment\b", r"\bloan emi\b",
            r"\binstalment\b", r"\binstallment\b", r"\bcredit card (due|bill|payment)\b",
            r"\bcard payment\b", r"\bno cost emi\b", r"\bpersonal loan\b",
            r"\bhome loan\b", r"\bcar loan\b", r"\bbajaj finserv\b",
            r"\bhdfc loan\b", r"\bicici loan\b",
        ],
    ),
    # ---- Investment & Savings ----
    (
        "investment",
        [
            r"\bzerodha\b", r"\bgroww\b", r"\bupstox\b", r"\bkuvera\b",
            r"\bcoin by zerodha\b", r"\bmutual fund\b", r"\bsip\b",
            r"\bnifty\b", r"\bsensex\b", r"\bstock\b", r"\bshare\b",
            r"\bdividend\b", r"\bfd\b", r"\bfixed deposit\b", r"\brd\b",
            r"\brecurring deposit\b", r"\bnps\b", r"\bppf\b", r"\belss\b",
            r"\bgold bond\b", r"\bcrypto\b", r"\bhdfc mutual\b",
            r"\bsip.*processed\b", r"\binvestment.*processed\b",
        ],
    ),
    # ---- Friends & Peer Transfers (UPI person-to-person) ----
    (
        "transfer",
        [
            r"\bsent to\b", r"\breceived from\b", r"\bpaid to\b",
            r"\btransferred to\b", r"\bsplit\b", r"\bsettle\b",
            r"\bphonepe\b.{0,40}\bsent\b",
            r"\bgpay\b.{0,40}\bsent\b",
            r"\bpaytm\b.{0,40}\bsent\b",
            r"\bsent rs\b", r"\bpaid rs\b.{0,30}\bto\b",
            r"\bp2p\b",
        ],
    ),
    # ---- Utilities & Bills ----
    (
        "utilities",
        [
            r"\belectricity\b", r"\bwater bill\b", r"\bgas bill\b",
            r"\bbroadband\b", r"\bwifi\b", r"\binternet\b", r"\bcable tv\b",
            r"\bdth\b", r"\btata sky\b", r"\bdish tv\b", r"\bairtel\b",
            r"\bjio\b", r"\bvi\b.{0,10}\brecharge\b", r"\bbsnl\b",
            r"\bmobile recharge\b", r"\bpostpaid\b", r"\bpostpaid bill\b",
            r"\bprepaid\b", r"\bprepaid recharge\b",
            r"\bnetflix\b", r"\bprime\b", r"\bhotstar\b", r"\bspotify\b",
            r"\bott\b", r"\bsubscription\b",
            r"\bbill paid\b", r"\bbill payment\b",
        ],
    ),
    # ---- Education ----
    (
        "education",
        [
            r"\bbyju\b", r"\bunacademy\b", r"\bvedantu\b", r"\bcourser\b",
            r"\budemy\b", r"\btuition\b", r"\bschool fee\b", r"\bcollege fee\b",
            r"\bfees?\b.{0,20}\bpaid\b", r"\badmission\b", r"\bexam fee\b",
            r"\bcourse fee\b", r"\bcoaching\b", r"\bskillshare\b",
            r"\bunacademy subscription\b", r"\beducation fee\b",
        ],
    ),
]


def label_category(text: str) -> str:
    """
    Returns a category string for a given SMS text.
    Falls back to 'others' if no rule matches.
    """
    t = text.lower()
    for category, patterns in CATEGORY_RULES:
        for pattern in patterns:
            if re.search(pattern, t):
                return category
    return "others"
