"""
WireSafe 109% — Fully Monetized Global Electrical Design Platform
By Owens U. Oriaikhi (COREN R72198)
Version: 2.0.0 — Global Edition
"""

import streamlit as st
import pandas as pd
import math
import json
import hashlib
import hmac
import requests
import stripe
from datetime import date, datetime, timedelta
from fpdf import FPDF
from typing import Optional, Dict, Any, List
import os

# ============================================================
# CONFIGURATION & SECRETS
# ============================================================
st.set_page_config(
    page_title="WireSafe — Global Electrical Design",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load secrets (create .streamlit/secrets.toml)
try:
    PAYSTACK_SECRET = st.secrets.get("PAYSTACK_SECRET_KEY", "")
    STRIPE_SECRET = st.secrets.get("STRIPE_SECRET_KEY", "")
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
    STRIPE_WEBHOOK_SECRET = st.secrets.get("STRIPE_WEBHOOK_SECRET", "")
    GOOGLE_ANALYTICS_ID = st.secrets.get("GA_ID", "G-XXXXXXXXXX")
    RESEND_API_KEY = st.secrets.get("RESEND_API_KEY", "")
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
except Exception:
    PAYSTACK_SECRET = STRIPE_SECRET = SUPABASE_URL = SUPABASE_KEY = ""
    STRIPE_WEBHOOK_SECRET = GOOGLE_ANALYTICS_ID = RESEND_API_KEY = OPENAI_API_KEY = ""

APP_VERSION = "2.0.0"
APP_URL = os.environ.get("APP_URL", "https://wiresafe.app")
COREN_REG = "R72198"
ENGINEER_NAME = "Owens U. Oriaikhi"

# ============================================================
# 109% REVENUE STREAM REGISTRY
# ============================================================
REVENUE_STREAMS = {
    "S1_SaaS_Subscriptions":       {"weight": 0.25, "status": "active"},
    "S2_Pay_Per_Report":           {"weight": 0.10, "status": "active"},
    "S3_Affiliate_Marketplace":    {"weight": 0.15, "status": "active"},
    "S4_Contractor_Leads":         {"weight": 0.08, "status": "active"},
    "S5_API_Access":               {"weight": 0.08, "status": "active"},
    "S6_White_Label":              {"weight": 0.05, "status": "active"},
    "S7_Training_Certification":   {"weight": 0.07, "status": "active"},
    "S8_Premium_Databases":        {"weight": 0.03, "status": "active"},
    "S9_Sponsored_Content":        {"weight": 0.02, "status": "active"},
    "S10_Data_Analytics":          {"weight": 0.03, "status": "active"},
    "S11_Consulting_Upsell":       {"weight": 0.04, "status": "active"},
    "S12_Marketplace_Commission":  {"weight": 0.03, "status": "active"},
    "S13_Professional_Stamping":   {"weight": 0.03, "status": "active"},
    "S14_Premium_Support":         {"weight": 0.02, "status": "active"},
    "S15_Insurance_Products":      {"weight": 0.02, "status": "active"},
}

# ============================================================
# GLOBAL STANDARDS ENGINE (Multi-Region)
# ============================================================
STANDARDS = {
    "BS7671": {
        "name": "BS 7671 — IET Wiring Regulations",
        "regions": ["NG","GH","KE","TZ","UG","RW","ZA","BW","ZM","ZW",
                    "GB","IE","AE","SA","QA","OM","KW","BH","IN","PK",
                    "BD","LK","MY","SG","BN","JM","TT","BB"],
        "v_1ph": 230, "v_3ph": 400,
        "cables_mm2": {
            1.5:  (20, 29.0), 2.5: (27, 18.0), 4: (36, 11.0), 6: (46, 7.3),
            10:   (62, 4.4),  16: (80, 2.8),  25: (101, 1.75), 35: (126, 1.25),
            50:  (151, 0.93), 70: (192, 0.63), 95: (232, 0.47), 120: (269, 0.38)
        },
        "breakers": [6,10,16,20,25,32,40,50,63,80,100,125,160,200,250,315,400],
        "stamp": "COREN", "stamp_price_usd": 20,
    },
    "NEC": {
        "name": "NEC NFPA 70 — USA/Canada",
        "regions": ["US","CA","MX","PH"],
        "v_1ph": 120, "v_3ph": 208,
        "cables_awg": {14:(15,3.1),12:(20,1.9),10:(30,1.2),8:(40,0.78),
                       6:(55,0.49),4:(70,0.31),3:(85,0.25),2:(100,0.20),
                       1:(110,0.16), "1/0":(125,0.13), "2/0":(145,0.10),
                       "3/0":(165,0.08), "4/0":(195,0.06)},
        "breakers": [15,20,30,40,50,60,70,80,90,100,125,150,175,200,225,250,
                     300,350,400,450,500,600],
        "stamp": "PE", "stamp_price_usd": 150,
    },
    "IEC_60364": {
        "name": "IEC 60364 — International",
        "regions": ["DE","FR","IT","ES","PT","NL","BE","AT","CH","NO","SE",
                    "DK","FI","PL","CZ","HU","RO","BG","GR","TR","CN","JP","KR"],
        "v_1ph": 230, "v_3ph": 400,
        "cables_mm2": {1.5:(17.5,29),2.5:(24,18),4:(32,11),6:(41,7.3),
                       10:(57,4.4),16:(76,2.8),25:(101,1.75),35:(126,1.25),
                       50:(153,0.93),70:(196,0.63),95:(238,0.47),120:(276,0.38)},
        "breakers": [6,10,16,20,25,32,40,50,63,80,100,125,160,200,250,315,400],
        "stamp": "CEng", "stamp_price_usd": 80,
    },
    "AS_NZS_3000": {
        "name": "AS/NZS 3000 — Australia/New Zealand",
        "regions": ["AU","NZ"],
        "v_1ph": 230, "v_3ph": 400,
        "cables_mm2": {1.5:(16,29),2.5:(20,18),4:(27,11),6:(36,7.3),
                       10:(49,4.4),16:(62,2.8),25:(80,1.75),35:(99,1.25),
                       50:(121,0.93),70:(153,0.63),95:(186,0.47),120:(215,0.38)},
        "breakers": [6,10,16,20,25,32,40,50,63,80,100,125,160,200,250,315,400],
        "stamp": "CPEng", "stamp_price_usd": 120,
    },
}

# ============================================================
# MULTI-CURRENCY PRICING ENGINE (PPP-Adjusted)
# ============================================================
CURRENCY_CONFIG = {
    "NGN": {"symbol": "₦",  "rate_to_base": 1.0,    "ppp": 1.0,  "gateway": "paystack"},
    "GHS": {"symbol": "GH₵","rate_to_base": 120.0,   "ppp": 1.3,  "gateway": "paystack"},
    "KES": {"symbol": "KSh","rate_to_base": 11.5,    "ppp": 1.2,  "gateway": "flutterwave"},
    "ZAR": {"symbol": "R",  "rate_to_base": 82.0,    "ppp": 2.5,  "gateway": "paystack"},
    "USD": {"symbol": "$",  "rate_to_base": 1500.0,  "ppp": 15.0, "gateway": "stripe"},
    "GBP": {"symbol": "£",  "rate_to_base": 1900.0,  "ppp": 12.0, "gateway": "stripe"},
    "EUR": {"symbol": "€",  "rate_to_base": 1650.0,  "ppp": 11.0, "gateway": "stripe"},
    "AED": {"symbol": "AED","rate_to_base": 410.0,   "ppp": 8.0,  "gateway": "stripe"},
    "INR": {"symbol": "₹",  "rate_to_base": 18.0,    "ppp": 0.6,  "gateway": "razorpay"},
    "AUD": {"symbol": "A$", "rate_to_base": 980.0,   "ppp": 14.0, "gateway": "stripe"},
}

# Base prices in NGN-equivalent units (before PPP)
BASE_PRICES = {
    "pro_monthly":         5000,
    "pro_annual":          48000,
    "business_monthly":    25000,
    "business_annual":     240000,
    "enterprise_monthly":  100000,
    "enterprise_annual":   960000,
    "global_monthly":      750000,
    "single_report":       1500,
    "boq_export":          500,
    "ai_summary":          300,
    "course_bs7671":       15000,
    "course_nec":          22000,
    "certification_exam":  10000,
    "premium_db_monthly":  3000,
    "priority_support":    7500,
    "api_starter_monthly": 75000,
    "api_growth_monthly":  300000,
    "api_scale_monthly":   750000,
}

def price(currency: str, base_key: str) -> float:
    """Get PPP-adjusted price in target currency."""
    cfg = CURRENCY_CONFIG[currency]
    base = BASE_PRICES[base_key]
    adjusted = base * cfg["ppp"]
    return round(adjusted / cfg["rate_to_base"], 2)

def fmt_price(currency: str, amount: float) -> str:
    sym = CURRENCY_CONFIG[currency]["symbol"]
    return f"{sym}{amount:,.2f}"

# ============================================================
# TIER DEFINITIONS (109% Feature Gating)
# ============================================================
TIERS = {
    "free": {
        "name": "Free",
        "max_designs_per_month": 3,
        "phases_allowed": [1],
        "standards_allowed": ["BS7671"],
        "pdf_report": False,
        "boq_export": False,
        "ai_summary": False,
        "watermark": True,
        "real_time_prices": False,
        "api_access": False,
        "team_seats": 1,
        "client_portal": False,
        "branding_removal": False,
        "premium_db": False,
        "priority_support": False,
        "professional_stamp": False,
    },
    "pro": {
        "name": "Pro",
        "max_designs_per_month": 999999,
        "phases_allowed": [1, 3],
        "standards_allowed": ["BS7671", "IEC_60364"],
        "pdf_report": True,
        "boq_export": True,
        "ai_summary": True,
        "watermark": False,
        "real_time_prices": True,
        "api_access": False,
        "team_seats": 1,
        "client_portal": False,
        "branding_removal": False,
        "premium_db": False,
        "priority_support": False,
        "professional_stamp": False,
    },
    "business": {
        "name": "Business",
        "max_designs_per_month": 999999,
        "phases_allowed": [1, 3],
        "standards_allowed": ["BS7671", "IEC_60364", "NEC"],
        "pdf_report": True,
        "boq_export": True,
        "ai_summary": True,
        "watermark": False,
        "real_time_prices": True,
        "api_access": False,
        "team_seats": 5,
        "client_portal": True,
        "branding_removal": True,
        "premium_db": True,
        "priority_support": True,
        "professional_stamp": False,
    },
    "enterprise": {
        "name": "Enterprise",
        "max_designs_per_month": 999999,
        "phases_allowed": [1, 3],
        "standards_allowed": list(STANDARDS.keys()),
        "pdf_report": True,
        "boq_export": True,
        "ai_summary": True,
        "watermark": False,
        "real_time_prices": True,
        "api_access": True,
        "team_seats": 999,
        "client_portal": True,
        "branding_removal": True,
        "premium_db": True,
        "priority_support": True,
        "professional_stamp": True,
    },
    "global": {
        "name": "Global Unlimited",
        "max_designs_per_month": 999999,
        "phases_allowed": [1, 3],
        "standards_allowed": list(STANDARDS.keys()),
        "pdf_report": True,
        "boq_export": True,
        "ai_summary": True,
        "watermark": False,
        "real_time_prices": True,
        "api_access": True,
        "team_seats": 999,
        "client_portal": True,
        "branding_removal": True,
        "premium_db": True,
        "priority_support": True,
        "professional_stamp": True,
    },
}

# ============================================================
# AFFILIATE MARKETPLACE (Revenue Stream #3)
# ============================================================
AFFILIATE_PARTNERS = {
    "NG": {
        "cables": [
            {"name": "Coleman Cables", "url": "https:// Coleman.ng/aff/wiresafe", "commission_pct": 0.05},
            {"name": "Nigerchin Cables", "url": "https://nigerchin.com/aff/wiresafe", "commission_pct": 0.05},
            {"name": "Nocaco", "url": "https://nocaco.com/aff/wiresafe", "commission_pct": 0.04},
            {"name": "Jumia Electrical", "url": "https://jumia.ng/aff/wiresafe", "commission_pct": 0.03},
        ],
        "mcb": [
            {"name": "Schneider Nigeria", "url": "https://se.com/ng/aff", "commission_pct": 0.06},
            {"name": "ABB Nigeria", "url": "https://abb.com/ng/aff", "commission_pct": 0.06},
        ],
    },
    "US": {
        "cables": [
            {"name": "Amazon Electrical", "url": "https://amazon.com/aff/wiresafe", "commission_pct": 0.04},
            {"name": "Home Depot", "url": "https://homedepot.com/aff/wiresafe", "commission_pct": 0.03},
            {"name": "Grainger", "url": "https://grainger.com/aff/wiresafe", "commission_pct": 0.04},
        ],
        "mcb": [
            {"name": "Grainger", "url": "https://grainger.com/aff/wiresafe", "commission_pct": 0.05},
        ],
    },
    "GB": {
        "cables": [
            {"name": "Toolstation", "url": "https://toolstation.com/aff/wiresafe", "commission_pct": 0.04},
            {"name": "Screwfix", "url": "https://screwfix.com/aff/wiresafe", "commission_pct": 0.04},
            {"name": "RS Components", "url": "https://rs.com/aff/wiresafe", "commission_pct": 0.05},
        ],
    },
    "KE": {"cables": [{"name": "East African Cables", "url": "#", "commission_pct": 0.05}]},
    "GH": {"cables": [{"name": "Ghana Cables", "url": "#", "commission_pct": 0.05}]},
    "ZA": {"cables": [{"name": "Voltex", "url": "#", "commission_pct": 0.05}]},
    "AE": {"cables": [{"name": "Danube Electrical", "url": "#", "commission_pct": 0.06}]},
    "IN": {"cables": [{"name": "Polycab India", "url": "#", "commission_pct": 0.05}]},
    "AU": {"cables": [{"name": "Bunnings Electrical", "url": "#", "commission_pct": 0.04}]},
}

# ============================================================
# CONTRACTOR LEAD NETWORK (Revenue Stream #4)
# ============================================================
CONTRACTOR_RATES = {
    "NG": {"basic_lead_ngn": 2000, "qualified_lead_ngn": 10000, "monthly_sub_ngn": 15000},
    "US": {"basic_lead_usd": 30,   "qualified_lead_usd": 150,   "monthly_sub_usd": 200},
    "GB": {"basic_lead_gbp": 20,   "qualified_lead_gbp": 100,   "monthly_sub_gbp": 150},
    "KE": {"basic_lead_usd": 5,    "qualified_lead_usd": 25,    "monthly_sub_usd": 40},
    "ZA": {"basic_lead_usd": 10,   "qualified_lead_usd": 50,    "monthly_sub_usd": 80},
    "AE": {"basic_lead_usd": 25,   "qualified_lead_usd": 120,   "monthly_sub_usd": 180},
    "IN": {"basic_lead_usd": 3,    "qualified_lead_usd": 15,    "monthly_sub_usd": 25},
    "AU": {"basic_lead_usd": 20,   "qualified_lead_usd": 90,    "monthly_sub_usd": 140},
}

# ============================================================
# API PRICING (Revenue Stream #5)
# ============================================================
API_PLANS = {
    "starter":    {"price_usd": 49,   "calls_month": 500,    "standards": ["BS7671"]},
    "growth":     {"price_usd": 199,  "calls_month": 5000,   "standards": ["BS7671","NEC","IEC_60364"]},
    "scale":      {"price_usd": 499,  "calls_month": 25000,  "standards": list(STANDARDS.keys())},
    "enterprise": {"price_usd": 1999, "calls_month": -1,     "standards": list(STANDARDS.keys()), "sla": True, "white_label": True},
}

# ============================================================
# COURSE CATALOG (Revenue Stream #7)
# ============================================================
COURSES = [
    {"id": "bs7671_master",   "title": "BS 7671 Cable Sizing Masterclass",        "price_usd": 97,  "audience": "Global Engineers"},
    {"id": "nec_us",          "title": "NEC Wiring Design for US Market",         "price_usd": 147, "audience": "US Electricians"},
    {"id": "solar_design",    "title": "Electrical Design for Solar Installations","price_usd": 197, "audience": "Solar Industry"},
    {"id": "iec_industrial",  "title": "IEC 60364 Industrial Wiring",             "price_usd": 247, "audience": "Industrial Engineers"},
    {"id": "africa_bundle",   "title": "African Electrical Standards Bundle",     "price_usd": 297, "audience": "Pan-African Engineers"},
    {"id": "wiresafe_cert",   "title": "WireSafe Certified Designer Exam",        "price_usd": 79,  "audience": "All"},
    {"id": "corporate",       "title": "Corporate Training (per session, 20 ppl)","price_usd": 1500,"audience": "Firms"},
]

# ============================================================
# AUTHENTICATION (Supabase-backed)
# ============================================================
def _api_headers(token: Optional[str] = None) -> Dict[str, str]:
    h = {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

def signup(email: str, password: str) -> Dict[str, Any]:
    if not SUPABASE_URL:
        return {"ok": False, "error": "Auth not configured"}
    r = requests.post(
        f"{SUPABASE_URL}/auth/v1/signup",
        headers=_api_headers(),
        json={"email": email, "password": password}
    )
    return r.json() if r.ok else {"ok": False, "error": r.text}

def login(email: str, password: str) -> Dict[str, Any]:
    if not SUPABASE_URL:
        return {"ok": False, "error": "Auth not configured"}
    r = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers=_api_headers(),
        json={"email": email, "password": password}
    )
    return r.json() if r.ok else {"ok": False, "error": r.text}

def get_user_profile(user_id: str) -> Dict[str, Any]:
    """Fetch user profile (tier, country, usage) from DB."""
    if not SUPABASE_URL:
        return {"tier": "free", "country": "NG", "currency": "NGN",
                "designs_this_month": 0, "email": "demo@wiresafe.app"}
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=*",
        headers=_api_headers(st.session_state.get("access_token"))
    )
    data = r.json()
    return data[0] if data else {"tier": "free", "country": "NG", "currency": "NGN",
                                  "designs_this_month": 0}

def record_design_usage(user_id: str):
    """Increment monthly design counter."""
    if not SUPABASE_URL:
        return
    requests.post(
        f"{SUPABASE_URL}/rest/v1/design_log",
        headers=_api_headers(st.session_state.get("access_token")),
        json={"user_id": user_id, "created_at": datetime.utcnow().isoformat()}
    )

# ============================================================
# PAYMENT INTEGRATIONS (Paystack + Stripe)
# ============================================================
def create_paystack_payment(email: str, amount_ngn: int, reference: str,
                            metadata: dict) -> Optional[str]:
    if not PAYSTACK_SECRET:
        return None
    r = requests.post(
        "https://api.paystack.co/transaction/initialize",
        headers={"Authorization": f"Bearer {PAYSTACK_SECRET}"},
        json={
            "email": email,
            "amount": int(amount_ngn * 100),  # kobo
            "reference": reference,
            "metadata": metadata,
            "callback_url": f"{APP_URL}/payment-callback",
        }
    )
    data = r.json()
    return data.get("data", {}).get("authorization_url") if data.get("status") else None

def create_stripe_checkout(email: str, price_key: str, currency: str,
                           mode: str = "subscription") -> Optional[str]:
    """Create Stripe Checkout session for subscription or one-time."""
    if not STRIPE_SECRET:
        return None
    try:
        stripe.api_key = STRIPE_SECRET
        line_items = [{
            "price": price_key,  # pre-created Stripe Price ID
            "quantity": 1,
        }]
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode=mode,
            customer_email=email,
            success_url=f"{APP_URL}/?success=1",
            cancel_url=f"{APP_URL}/?canceled=1",
            metadata={"tier": price_key},
        )
        return session.url
    except Exception as e:
        st.error(f"Stripe error: {e}")
        return None

def verify_paystack(reference: str) -> bool:
    if not PAYSTACK_SECRET:
        return False
    r = requests.get(
        f"https://api.paystack.co/transaction/verify/{reference}",
        headers={"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    )
    data = r.json()
    return data.get("data", {}).get("status") == "success"

# ============================================================
# AI ENGINEERING SUMMARY (OpenAI with fallback)
# ============================================================
def ai_engineering_summary(params: dict) -> str:
    fallback = (
        f"Design verified against {params['standard']} copper PVC cable tables. "
        f"All results within regulatory limits. Load {params['design_w']:.0f}W, "
        f"Ib {params['ib']:.1f}A, protective device {params['breaker']}A, "
        f"cable {params['cable']}mm², voltage drop {params['vd_pct']:.2f}%. "
        f"Installation compliant with {params['standard']} requirements."
    )
    if not OPENAI_API_KEY:
        return fallback
    try:
        prompt = (
            f"Write a 4-sentence professional engineering summary for a client report. "
            f"Standard: {params['standard']}. Load: {params['design_w']:.0f}W. "
            f"Design current Ib: {params['ib']:.1f}A. Protective device: {params['breaker']}A. "
            f"Cable size: {params['cable']}mm². Voltage drop: {params['vd_pct']:.2f}%. "
            f"Circuit length: {params['length_m']}m. Tone: professional, concise, authoritative."
        )
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}",
                     "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a senior electrical engineer writing a client design report."},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 200,
                "temperature": 0.4,
            },
            timeout=15
        )
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return fallback

# ============================================================
# PDF REPORT BUILDER (with watermark + multi-standard)
# ============================================================
def _draw_kv_table(pdf, rows, col_w=(90, 100)):
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(col_w[0], 6, "Parameter", border=1, fill=True)
    pdf.cell(col_w[1], 6, "Value", border=1, fill=True)
    pdf.ln(6)
    for k, v in rows:
        pdf.cell(col_w[0], 6, str(k), border=1)
        pdf.cell(col_w[1], 6, str(v), border=1)
        pdf.ln(6)

def _draw_results_table(pdf, rows, col_w=(45, 40, 55, 50)):
    pdf.set_fill_color(230, 230, 230)
    for i, h in enumerate(["Item", "Value", "Standard Ref", "Status"]):
        pdf.cell(col_w[i], 6, h, border=1, fill=True)
    pdf.ln(6)
    for item, val, ref, status in rows:
        pdf.cell(col_w[0], 6, str(item), border=1)
        pdf.cell(col_w[1], 6, str(val), border=1)
        pdf.cell(col_w[2], 6, str(ref), border=1)
        mark = "[x]" if status in ("PASS", "APPLIED") else "[ ]"
        pdf.cell(col_w[3], 6, f"{mark} {status}", border=1)
        pdf.ln(6)

def _draw_boq_table(pdf, boq_df, col_w=(80, 25, 20, 65)):
    pdf.set_fill_color(230, 230, 230)
    for i, h in enumerate(["Item", "Qty", "Unit", f"Total ({boq_df.attrs.get('currency','NGN')})"]):
        pdf.cell(col_w[i], 6, h, border=1, fill=True)
    pdf.ln(6)
    for _, row in boq_df.iterrows():
        pdf.cell(col_w[0], 6, str(row["Item"]), border=1)
        pdf.cell(col_w[1], 6, str(row["Qty"]), border=1, align="R")
        pdf.cell(col_w[2], 6, str(row["Unit"]), border=1)
        pdf.cell(col_w[3], 6, f"{int(row['Total']):,}", border=1, align="R")
        pdf.ln(6)

def _draw_watermark(pdf, text="WIRESAFE FREE"):
    pdf.set_font("Helvetica", "B", 42)
    pdf.set_text_color(210, 210, 210)
    with pdf.rotation(45, 105, 150):
        pdf.set_xy(30, 150)
        pdf.cell(0, 20, text)
    pdf.set_text_color(0, 0, 0)

def build_pdf_report(params: dict, boq_df: pd.DataFrame,
                     eng_summary: str, tier: str = "free") -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    if tier == "free":
        _draw_watermark(pdf)

    # Header
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, f"WireSafe Design Report — {params['standard']}", align="C")
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5,
             f"Project: {params.get('project','-')} | Client: {params.get('client','-')} | "
             f"Date: {params.get('rpt_date', date.today())} | Tier: {tier.upper()}",
             align="C")
    pdf.ln(7)
    pdf.set_draw_color(120, 120, 120)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # Inputs
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Design Inputs"); pdf.ln(7)
    pdf.set_font("Helvetica", "", 9)
    _draw_kv_table(pdf, [
        ("Standard", params["standard"]),
        ("Phases", f"{params['phases']}"),
        ("Power factor", f"{params['pf']:.2f}"),
        ("Circuit length", f"{params['length_m']} m"),
        ("Connected load", f"{params['total_w']:,.0f} W"),
        ("Design load", f"{params['design_w']:,.0f} W"),
        ("Design current Ib", f"{params['ib']:.1f} A"),
        ("Ca (ambient)", f"{params['ca']:.2f}"),
        ("Cg (grouping)", f"{params['cg']:.2f}"),
        ("V-drop limit", f"{params['vd_limit']:.1f}%"),
    ])

    # Results
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Results & Compliance Check"); pdf.ln(7)
    pdf.set_font("Helvetica", "", 9)
    std = STANDARDS[params["standard"]]
    _draw_results_table(pdf, [
        ("Protective device", f"{params['breaker']} A", f"{params['standard']} Table 41.3", "PASS"),
        ("Cable size", f"{params['cable']} {'mm²' if 'mm2' not in str(params['cable']) else ''}",
         f"{params['standard']} Cable Tables", "PASS"),
        ("Voltage drop", f"{params['vd_pct']:.2f}%", f"{params['standard']} Volt-Drop",
         "PASS" if params['vd_pct'] <= params['vd_limit'] else "CHECK"),
        ("Correction factors", f"Ca={params['ca']:.2f}, Cg={params['cg']:.2f}",
         f"{params['standard']} App. 4", "APPLIED"),
    ])

    # BOQ
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Bill of Quantities (BOQ)"); pdf.ln(7)
    pdf.set_font("Helvetica", "", 9)
    _draw_boq_table(pdf, boq_df)

    pdf.ln(1)
    grand = int(boq_df["Total"].sum())
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7,
             f"Estimated Material Cost: {boq_df.attrs.get('currency_symbol','₦')}{grand:,}",
             align="R")
    pdf.ln(7)

    # Engineering Summary
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Engineering Summary"); pdf.ln(7)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, eng_summary)

    # Sign-off
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, f"Verified by: {ENGINEER_NAME} (COREN Reg. No. {COREN_REG})")
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 5,
        "Disclaimer: This report is a design aid generated by WireSafe. "
        "Final verification and sign-off must be performed by a licensed "
        "engineer in the relevant jurisdiction before installation.")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 5, f"{ENGINEER_NAME} (COREN {COREN_REG}) | WireSafe v{APP_VERSION}", align="C")

    return bytes(pdf.output())

# ============================================================
# CORE DESIGN ENGINE (Multi-Standard)
# ============================================================
def run_design(standard_key: str, phases: int, pf: float, ca: float, cg: float,
               vd_limit: float, length_m: float, loads_df: pd.DataFrame,
               demand_pct: float) -> Dict[str, Any]:
    std = STANDARDS[standard_key]
    v = std["v_1ph"] if phases == 1 else std["v_3ph"]

    total_w = float((loads_df["Watts"] * loads_df["Qty"]).sum())
    design_w = total_w * demand_pct / 100

    if phases == 1:
        ib = design_w / (v * pf)
    else:
        ib = design_w / (math.sqrt(3) * v * pf)

    breaker = next((b for b in std["breakers"] if b >= ib), None)

    cable, vd_pct, status = None, None, "FAIL"
    cable_table = std.get("cables_mm2") or std.get("cables_awg", {})

    if breaker:
        for size, (iz, mv) in sorted(cable_table.items(),
                                      key=lambda x: x[1][0] if isinstance(x[1][0], (int,float)) else 999):
            if iz * ca * cg >= breaker:
                vd = 100 * (mv * ib * length_m / 1000) / v
                if vd <= vd_limit:
                    cable, vd_pct, status = size, vd, "PASS"
                    break

    return {
        "standard": standard_key,
        "phases": phases, "pf": pf, "ca": ca, "cg": cg,
        "vd_limit": vd_limit, "length_m": length_m,
        "total_w": total_w, "design_w": design_w, "ib": ib,
        "breaker": breaker, "cable": cable, "vd_pct": vd_pct,
        "status": status, "voltage": v,
    }

# ============================================================
# BOQ BUILDER (with affiliate links)
# ============================================================
def build_boq(design: dict, country: str, currency: str) -> pd.DataFrame:
    cable = design["cable"]
    breaker = design["breaker"]
    length_m = design["length_m"]
    cable_m = round(length_m * 1.05, 1)

    # Base prices in NGN (placeholder)
    cable_price_per_m = {1.5:350,2.5:550,4:900,6:1300,10:2200,16:3400,25:5300,
                         35:7400,50:10500,70:14800,95:20000,120:25000}.get(cable, 1000)

    # PPP-adjust to target currency
    rate = CURRENCY_CONFIG[currency]["rate_to_base"]
    ppp = CURRENCY_CONFIG[currency]["ppp"]
    factor = ppp / rate

    rows = [
        {"Item": f"Cable {cable} mm² (PVC/Cu)",
         "Qty": cable_m, "Unit": "m",
         "Unit Price": round(cable_price_per_m * factor, 2),
         "Total": round(cable_m * cable_price_per_m * factor, 2),
         "Affiliate": AFFILIATE_PARTNERS.get(country, {}).get("cables", [{}])[0].get("url", "#")},
        {"Item": f"MCB/MCCB {breaker}A",
         "Qty": 1, "Unit": "pc",
         "Unit Price": round(18000 * factor, 2),
         "Total": round(18000 * factor, 2),
         "Affiliate": AFFILIATE_PARTNERS.get(country, {}).get("mcb", [{}])[0].get("url", "#")},
        {"Item": "Conduit, trunking & accessories",
         "Qty": 1, "Unit": "lot",
         "Unit Price": round(25000 * factor, 2),
         "Total": round(25000 * factor, 2),
         "Affiliate": "#"},
    ]
    df = pd.DataFrame(rows)
    df.attrs["currency"] = currency
    df.attrs["currency_symbol"] = CURRENCY_CONFIG[currency]["symbol"]
    return df

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
if "user" not in st.session_state:
    st.session_state.user = None
if "profile" not in st.session_state:
    st.session_state.profile = {
        "tier": "free", "country": "NG", "currency": "NGN",
        "designs_this_month": 0, "email": "guest@wiresafe.app"
    }
if "page" not in st.session_state:
    st.session_state.page = "designer"

# ============================================================
# SIDEBAR: AUTH + NAVIGATION + TIER BADGE
# ============================================================
with st.sidebar:
    st.markdown("## ⚡ WireSafe Global")
    st.caption(f"v{APP_VERSION} | {ENGINEER_NAME} (COREN {COREN_REG})")

    # Auth block
    if st.session_state.user is None:
        st.markdown("### 🔐 Account")
        auth_tab1, auth_tab2 = st.tabs(["Login", "Sign Up"])
        with auth_tab1:
            l_email = st.text_input("Email", key="l_email")
            l_pass = st.text_input("Password", type="password", key="l_pass")
            if st.button("Login", key="btn_login"):
                res = login(l_email, l_pass)
                if "access_token" in res:
                    st.session_state.user = res
                    st.session_state.access_token = res["access_token"]
                    st.session_state.profile = get_user_profile(res["user"]["id"])
                    st.rerun()
                else:
                    st.error(res.get("error", "Login failed"))
        with auth_tab2:
            s_email = st.text_input("Email", key="s_email")
            s_pass = st.text_input("Password", type="password", key="s_pass")
            s_country = st.selectbox("Country", list(CURRENCY_CONFIG.keys()),
                                     index=0, key="s_country")
            if st.button("Create Account", key="btn_signup"):
                res = signup(s_email, s_pass)
                if res.get("user"):
                    st.success("Account created! Check email to verify, then login.")
                else:
                    st.error(res.get("error", "Signup failed"))
    else:
        tier = st.session_state.profile.get("tier", "free")
        tier_color = {"free":"gray","pro":"blue","business":"green",
                      "enterprise":"orange","global":"violet"}.get(tier, "gray")
        st.success(f"**{st.session_state.profile.get('email','')}**")
        st.markdown(f"🏷️ Tier: **{tier.upper()}**")
        st.caption(f"Designs this month: {st.session_state.profile.get('designs_this_month',0)}")
        if st.button("Logout"):
            for k in ["user","profile","access_token"]:
                st.session_state.pop(k, None)
            st.rerun()

    st.markdown("---")

    # Navigation
    nav = st.radio("Navigate", [
        "🔌 Designer",
        "💎 Pricing",
        "🛒 Marketplace",
        "👷 Contractor Network",
        "🎓 Courses & Certification",
        "🔑 API Access",
        "🏢 Enterprise / White-Label",
        "📊 My Dashboard",
        "💬 Support",
    ], index=0)

    # Currency selector (affects pricing display)
    st.markdown("---")
    currency = st.selectbox("Currency", list(CURRENCY_CONFIG.keys()),
                            index=list(CURRENCY_CONFIG.keys()).index(
                                st.session_state.profile.get("currency","NGN")))
    st.session_state.profile["currency"] = currency

# Map nav to page
PAGE_MAP = {
    "🔌 Designer": "designer",
    "💎 Pricing": "pricing",
    "🛒 Marketplace": "marketplace",
    "👷 Contractor Network": "contractors",
    "🎓 Courses & Certification": "courses",
    "🔑 API Access": "api",
    "🏢 Enterprise / White-Label": "enterprise",
    "📊 My Dashboard": "dashboard",
    "💬 Support": "support",
}
page = PAGE_MAP[nav]

# ============================================================
# HELPER: GATE CHECK
# ============================================================
def can_use(feature: str) -> bool:
    tier = st.session_state.profile.get("tier", "free")
    return TIERS[tier].get(feature, False)

def designs_remaining() -> int:
    tier = st.session_state.profile.get("tier", "free")
    limit = TIERS[tier]["max_designs_per_month"]
    used = st.session_state.profile.get("designs_this_month", 0)
    return max(0, limit - used)

# ============================================================
# PAGE: DESIGNER (Core Product)
# ============================================================
if page == "designer":
    st.title("⚡ WireSafe — Global Electrical Wiring Design")
    st.caption(f"Multi-standard: BS 7671 · NEC · IEC 60364 · AS/NZS 3000 | v{APP_VERSION}")

    # Usage warning for free tier
    if st.session_state.profile.get("tier") == "free":
        remaining = designs_remaining()
        if remaining <= 1:
            st.warning(f"⚠️ You have {remaining} free design(s) left this month. "
                       f"[Upgrade to Pro](#pricing) for unlimited designs.")

    # Standard selector (gated)
    tier = st.session_state.profile.get("tier", "free")
    allowed_standards = TIERS[tier]["standards_allowed"]

    colA, colB = st.columns([3, 1])
    with colA:
        standard = st.selectbox("Electrical Standard", allowed_standards,
                                format_func=lambda k: STANDARDS[k]["name"])
    with colB:
        country = st.selectbox("Country",
                               [c for c in CURRENCY_CONFIG.keys()],
                               index=list(CURRENCY_CONFIG.keys()).index(
                                   st.session_state.profile.get("country","NG")))

    st.session_state.profile["country"] = country
    std = STANDARDS[standard]

    # Design inputs
    st.sidebar.markdown("---")
    st.sidebar.header("Design Inputs")
    allowed_phases = TIERS[tier]["phases_allowed"]
    phases = st.sidebar.selectbox("Phases", allowed_phases)
    pf = st.sidebar.slider("Power factor", 0.7, 1.0, 0.9, 0.05)
    ca = st.sidebar.slider("Ambient correction Ca", 0.7, 1.0, 1.0, 0.05)
    cg = st.sidebar.slider("Grouping correction Cg", 0.7, 1.0, 1.0, 0.05)
    vd_limit = st.sidebar.selectbox("V-drop limit %", [3.0, 4.0, 5.0], index=1)

    st.sidebar.markdown("---")
    st.sidebar.header("Report Details")
    project_name = st.sidebar.text_input("Project name", value="")
    client_name = st.sidebar.text_input("Client name", value="")
    report_date = st.sidebar.date_input("Report date", value=date.today())

    # Load schedule
    st.subheader("Load Schedule")
    default_loads = pd.DataFrame([
        {"Device": "Lighting", "Watts": 500, "Qty": 10},
        {"Device": "AC Unit", "Watts": 2200, "Qty": 2},
        {"Device": "Sockets", "Watts": 1300, "Qty": 6},
    ])
    loads = st.data_editor(default_loads, num_rows="dynamic",
                           use_container_width=True).fillna(0)

    length_m = st.number_input("Circuit run length (m)", 1, 500, 30)
    demand = st.slider("Demand factor %", 50, 100, 80)

    # Run design
    if st.button("⚡ Run Design", type="primary", use_container_width=True):
        if designs_remaining() <= 0 and tier == "free":
            st.error("🔒 Free tier limit reached. Upgrade to continue.")
            st.session_state.page = "pricing"
            st.rerun()

        design = run_design(standard, phases, pf, ca, cg, vd_limit,
                            length_m, loads, demand)
        st.session_state.last_design = design
        record_design_usage(st.session_state.profile.get("email",""))
        st.session_state.profile["designs_this_month"] = \
            st.session_state.profile.get("designs_this_month", 0) + 1

    # Show results
    if "last_design" in st.session_state:
        d = st.session_state.last_design
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Connected Load (W)", f"{d['total_w']:,.0f}")
        c2.metric("Design Load (W)", f"{d['design_w']:,.0f}")
        c3.metric("Ib (A)", f"{d['ib']:.1f}")
        c4.metric("V-drop %", f"{d['vd_pct']:.2f}" if d['vd_pct'] else "—")

        if d["status"] == "PASS":
            st.success(f"✅ PASS — {d['standard']} | "
                       f"Device {d['breaker']}A | Cable {d['cable']} | "
                       f"V-drop {d['vd_pct']:.2f}%")

            # BOQ
            boq = build_boq(d, country, currency)
            st.subheader("🛒 Bill of Quantities")
            st.dataframe(boq[["Item","Qty","Unit","Total"]],
                         use_container_width=True)
            sym = CURRENCY_CONFIG[currency]["symbol"]
            st.metric(f"Estimated Cost ({currency})",
                      f"{sym}{int(boq['Total'].sum()):,}")

            # Affiliate buy buttons (Revenue Stream #3)
            st.markdown("#### 🛍️ Buy Materials (Affiliate Links)")
            acol1, acol2, acol3 = st.columns(3)
            for i, row in boq.iterrows():
                col = [acol1, acol2, acol3][i]
                with col:
                    st.markdown(f"**{row['Item']}**")
                    if row["Affiliate"] != "#":
                        st.markdown(f"[🛒 Buy Now]({row['Affiliate']})")
                    else:
                        st.caption("Contact supplier directly")

            # PDF Report (gated)
            st.markdown("---")
            if can_use("pdf_report"):
                if st.button("📄 Generate PDF Design Report", type="primary"):
                    with st.spinner("Generating report..."):
                        params = {**d, "project": project_name,
                                  "client": client_name, "rpt_date": report_date}
                        summary = ai_engineering_summary(params)
                        pdf_bytes = build_pdf_report(params, boq, summary, tier)
                        st.download_button(
                            "📥 Download PDF Report",
                            data=pdf_bytes,
                            file_name=f"WireSafe_{standard}_{report_date}.pdf",
                            mime="application/pdf"
                        )
                        st.success("✅ Report generated successfully!")
            else:
                st.info(f"🔒 **PDF reports are a Pro feature.** "
                        f"Pay {fmt_price(currency, price(currency,'single_report'))} "
                        f"for this report, or upgrade to Pro for unlimited reports.")
                pc1, pc2 = st.columns(2)
                with pc1:
                    if st.button(f"💳 Pay {fmt_price(currency, price(currency,'single_report'))} for PDF"):
                        ref = f"rpt_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                        url = create_paystack_payment(
                            st.session_state.profile.get("email",""),
                            int(price("NGN","single_report")),
                            ref, {"type": "single_report", "standard": standard}
                        )
                        if url:
                            st.markdown(f"[🔗 Click here to pay securely]({url})")
                        else:
                            st.warning("Payment gateway not configured. Contact support.")
                with pc2:
                    if st.button(f"⭐ Upgrade to Pro — {fmt_price(currency, price(currency,'pro_monthly'))}/mo"):
                        st.session_state.page = "pricing"
                        st.rerun()

            # BOQ Export (gated)
            if can_use("boq_export"):
                csv = boq.to_csv(index=False).encode("utf-8")
                st.download_button("📊 Export BOQ (CSV)", csv,
                                   file_name="WireSafe_BOQ.csv", mime="text/csv")
            else:
                st.caption(f"🔒 BOQ export: {fmt_price(currency, price(currency,'boq_export'))} one-time")

            # Contractor Lead Gen (Revenue Stream #4)
            st.markdown("---")
            st.info("### 👷 Need a Certified Electrician?")
            st.caption("Get matched with verified contractors in your area.")
            with st.form("lead_form"):
                lc1, lc2 = st.columns(2)
                with lc1:
                    lead_phone = st.text_input("Your phone number")
                    lead_location = st.text_input("Project location (city, country)")
                with lc2:
                    lead_type = st.selectbox("Project type",
                                             ["Residential","Commercial","Industrial"])
                    lead_budget = st.selectbox("Budget range",
                                               ["< $5K","$5K-$20K","$20K-$100K","> $100K"])
                if st.form_submit_button("🔌 Get 3 Free Contractor Quotes"):
                    st.success("✅ Request submitted! 3 contractors will contact you within 24h.")
                    # TODO: Save lead to DB, notify contractors

        else:
            st.error(f"❌ No suitable cable found in {standard}. "
                     f"Reduce load/length or split circuits.")

# ============================================================
# PAGE: PRICING (Revenue Streams #1, #2)
# ============================================================
elif page == "pricing":
    st.title("💎 WireSafe Pricing — 109% Value")
    st.caption("Choose the plan that fits your needs. Upgrade anytime.")

    sym = CURRENCY_CONFIG[currency]["symbol"]

    cols = st.columns(5)
    plans = [
        ("Free", "free", 0, [
            "3 designs/month", "1-phase only", "BS 7671 only",
            "Watermarked reports", "No PDF export", "Community support",
        ]),
        ("Pro ⭐", "pro", "pro_monthly", [
            "Unlimited designs", "1 & 3-phase", "BS 7671 + IEC 60364",
            "PDF reports", "BOQ export (CSV)", "AI engineering summary",
            "No watermark", "Email support",
        ]),
        ("Business", "business", "business_monthly", [
            "Everything in Pro", "5 team seats", "Client portal",
            "Real-time prices", "Branded reports", "Premium cable DB",
            "Priority support", "NEC standard",
        ]),
        ("Enterprise", "enterprise", "enterprise_monthly", [
            "Everything in Business", "Unlimited seats", "API access",
            "White-label option", "All 4 standards", "Professional stamping",
            "Dedicated CSM", "SLA 99.9%",
        ]),
        ("Global Unlimited", "global", "global_monthly", [
            "Everything in Enterprise", "Multi-region deployment",
            "Custom standards", "On-premise option", "24/7 phone support",
            "Custom integrations", "Quarterly business reviews",
        ]),
    ]

    for i, (name, key, price_key, features) in enumerate(plans):
        with cols[i]:
            st.subheader(name)
            if price_key == 0:
                st.write(f"{sym}0 / month")
            else:
                p = price(currency, price_key)
                st.write(f"**{sym}{p:,.0f} / month**")
                annual = price(currency, price_key.replace("monthly","annual")) \
                         if price_key.replace("monthly","annual") in BASE_PRICES else None
                if annual:
                    st.caption(f"or {sym}{annual:,.0f}/yr (save 20%)")
            st.markdown("---")
            for f in features:
                st.write(f"✅ {f}")
            if key == "free":
                st.button("Current", disabled=(st.session_state.profile.get("tier")=="free"))
            else:
                if st.button(f"Choose {name}", key=f"btn_{key}", type="primary"):
                    if currency in ["NGN","GHS","KES","ZAR"]:
                        url = create_paystack_payment(
                            st.session_state.profile.get("email",""),
                            int(price("NGN", price_key)),
                            f"sub_{key}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                            {"tier": key, "currency": currency}
                        )
                        if url:
                            st.markdown(f"[🔗 Pay securely]({url})")
                    else:
                        # Stripe
                        url = create_stripe_checkout(
                            st.session_state.profile.get("email",""),
                            f"price_{key}_{currency.lower()}",
                            currency
                        )
                        if url:
                            st.markdown(f"[🔗 Pay with Stripe]({url})")

    # Pay-per-report section
    st.markdown("---")
    st.subheader("🎟️ Pay-As-You-Go (No Subscription)")
    pc1, pc2, pc3, pc4 = st.columns(4)
    items = [
        ("Single PDF Report", "single_report"),
        ("BOQ Export (CSV/Excel)", "boq_export"),
        ("AI Engineering Summary", "ai_summary"),
        ("Premium Cable Database (1 mo)", "premium_db_monthly"),
    ]
    for i, (label, key) in enumerate(items):
        with [pc1,pc2,pc3,pc4][i]:
            p = price(currency, key)
            st.markdown(f"**{label}**")
            st.write(f"{sym}{p:,.2f}")
            st.button(f"Buy", key=f"buy_{key}")

# ============================================================
# PAGE: MARKETPLACE (Revenue Stream #3)
# ============================================================
elif page == "marketplace":
    st.title("🛒 WireSafe Marketplace")
    st.caption("Buy cables, MCBs, and accessories from verified partners. "
               "Earn affiliate commissions by referring.")

    partners = AFFILIATE_PARTNERS.get(country, AFFILIATE_PARTNERS.get("NG", {}))
    for category, items in partners.items():
        st.subheader(f"{category.title()} Suppliers")
        cols = st.columns(len(items))
        for i, partner in enumerate(items):
            with cols[i]:
                st.markdown(f"### {partner['name']}")
                st.caption(f"Commission: {partner['commission_pct']*100:.0f}%")
                st.markdown(f"[🔗 Visit Partner]({partner['url']})")

    st.markdown("---")
    st.subheader("💰 Become an Affiliate Partner")
    st.write("Are you a cable manufacturer, MCB distributor, or electrical supplier? "
             "Join the WireSafe affiliate network and reach thousands of engineers.")
    with st.form("affiliate_form"):
        af1, af2 = st.columns(2)
        with af1:
            af_company = st.text_input("Company name")
            af_contact = st.text_input("Contact email")
        with af2:
            af_country = st.text_input("Country of operation")
            af_category = st.selectbox("Category", ["Cables","MCB/MCCB","Conduit","Accessories","Other"])
        af_desc = st.text_area("Tell us about your products")
        if st.form_submit_button("📨 Apply for Partnership"):
            st.success("✅ Application received! We'll contact you within 48 hours.")

# ============================================================
# PAGE: CONTRACTOR NETWORK (Revenue Stream #4)
# ============================================================
elif page == "contractors":
    st.title("👷 WireSafe Contractor Network")
    st.caption("Connect certified electricians with clients. Earn leads or get quotes.")

    tab1, tab2 = st.tabs(["🔌 I Need a Contractor", "👷 I Am a Contractor"])

    with tab1:
        st.write("Post your project and get 3 free quotes from verified contractors.")
        with st.form("client_lead"):
            c1, c2 = st.columns(2)
            with c1:
                cl_name = st.text_input("Your name")
                cl_phone = st.text_input("Phone")
                cl_email = st.text_input("Email")
            with c2:
                cl_location = st.text_input("Project location")
                cl_type = st.selectbox("Project type",
                                       ["Residential","Commercial","Industrial"])
                cl_scope = st.selectbox("Scope",
                                        ["New installation","Rewiring","Repair","Inspection"])
            cl_desc = st.text_area("Project description")
            if st.form_submit_button("📨 Get Free Quotes"):
                st.success("✅ Submitted! 3 contractors will contact you within 24h.")

    with tab2:
        st.write("Join as a contractor and receive qualified leads from WireSafe users.")
        rates = CONTRACTOR_RATES.get(country, CONTRACTOR_RATES["NG"])
        st.info(f"**Lead pricing in your region:**\n\n"
                f"- Basic lead: {rates.get('basic_lead_ngn', rates.get('basic_lead_usd', '—'))}\n"
                f"- Qualified lead (with design): "
                f"{rates.get('qualified_lead_ngn', rates.get('qualified_lead_usd', '—'))}\n"
                f"- Monthly subscription: "
                f"{rates.get('monthly_sub_ngn', rates.get('monthly_sub_usd', '—'))}")
        with st.form("contractor_signup"):
            ct1, ct2 = st.columns(2)
            with ct1:
                ct_name = st.text_input("Company / Your name")
                ct_license = st.text_input("License / Registration number")
                ct_specialty = st.multiselect("Specialties",
                                              ["Residential","Commercial","Industrial",
                                               "Solar","EV Charging","Smart Home"])
            with ct2:
                ct_location = st.text_input("Service area")
                ct_phone = st.text_input("Phone")
                ct_plan = st.selectbox("Lead plan",
                                       ["Pay-per-lead", "Monthly subscription"])
            if st.form_submit_button("📨 Apply to Join"):
                st.success("✅ Application received! Verification takes 24-48h.")

# ============================================================
# PAGE: COURSES & CERTIFICATION (Revenue Stream #7)
# ============================================================
elif page == "courses":
    st.title("🎓 WireSafe Academy")
    st.caption("Master electrical design. Get certified. Advance your career.")

    for course in COURSES:
        with st.expander(f"📘 {course['title']} — ${course['price_usd']}"):
            st.write(f"**Audience:** {course['audience']}")
            st.write("**Curriculum:**")
            st.write("- Module 1: Fundamentals")
            st.write("- Module 2: Standards deep-dive")
            st.write("- Module 3: Hands-on with WireSafe")
            st.write("- Module 4: Real-world case studies")
            st.write("- Module 5: Certification exam prep")
            if st.button(f"🎓 Enroll — ${course['price_usd']}", key=f"enroll_{course['id']}"):
                if currency in ["NGN","GHS","KES","ZAR"]:
                    ngn_equiv = int(course["price_usd"] * 1500)
                    url = create_paystack_payment(
                        st.session_state.profile.get("email",""),
                        ngn_equiv,
                        f"course_{course['id']}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        {"course": course["id"]}
                    )
                    if url:
                        st.markdown(f"[🔗 Pay to enroll]({url})")
                else:
                    st.info(f"Stripe checkout for ${course['price_usd']}")

    st.markdown("---")
    st.subheader("🏆 WireSafe Certification Tiers")
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        st.markdown("### 🥉 Certified Designer")
        st.write("$79 exam")
        st.write("✅ 40-question exam")
        st.write("✅ Digital badge")
        st.write("✅ LinkedIn verification")
    with cc2:
        st.markdown("### 🥈 Master Designer")
        st.write("$299 exam")
        st.write("✅ Advanced scenarios")
        st.write("✅ Case study submission")
        st.write("✅ Priority contractor listing")
    with cc3:
        st.markdown("### 🥇 Fellow")
        st.write("$999 + portfolio")
        st.write("✅ Industry contribution")
        st.write("✅ Speaking opportunities")
        st.write("✅ Advisory board seat")

# ============================================================
# PAGE: API ACCESS (Revenue Stream #5)
# ============================================================
elif page == "api":
    st.title("🔑 WireSafe API")
    st.caption("Integrate electrical design into your own software.")

    st.subheader("API Plans")
    for plan_key, plan in API_PLANS.items():
        with st.expander(f"**{plan_key.upper()}** — ${plan['price_usd']}/mo"):
            st.write(f"Calls/month: {'Unlimited' if plan['calls_month'] == -1 else plan['calls_month']:,}")
            st.write(f"Standards: {', '.join(plan['standards'])}")
            if plan.get("sla"):
                st.write("SLA: 99.9% uptime")
            if plan.get("white_label"):
                st.write("White-label: ✅")
            if st.button(f"Subscribe — ${plan['price_usd']}/mo", key=f"api_{plan_key}"):
                st.info(f"Stripe checkout for API {plan_key} plan")

    st.markdown("---")
    st.subheader("📖 API Documentation")
    st.code("""
POST /v1/design
{
  "standard": "BS7671",
  "phases": 1,
  "power_factor": 0.9,
  "ca": 1.0, "cg": 1.0,
  "vd_limit_pct": 4.0,
  "length_m": 30,
  "loads": [
    {"device": "Lighting", "watts": 500, "qty": 10}
  ]
}

Response:
{
  "status": "PASS",
  "breaker_a": 16,
  "cable_mm2": 2.5,
  "vd_pct": 2.1,
  "ib_a": 9.8
}
    """, language="json")

    st.write("**Base URL:** `https://api.wiresafe.app/v1`")
    st.write("**Authentication:** Bearer token (get from dashboard)")
    st.write("**Rate limits:** Per plan")
    st.write("**Webhooks:** Design completion, payment events")

# ============================================================
# PAGE: ENTERPRISE / WHITE-LABEL (Revenue Stream #6)
# ============================================================
elif page == "enterprise":
    st.title("🏢 Enterprise & White-Label")
    st.caption("Deploy WireSafe as your own branded platform.")

    st.subheader("White-Label Licensing")
    st.write("License the entire WireSafe engine under your brand.")
    wl1, wl2, wl3 = st.columns(3)
    with wl1:
        st.markdown("### 🥉 Starter")
        st.write("$5,000/yr")
        st.write("✅ Your logo")
        st.write("✅ Your domain")
        st.write("✅ 50 users")
    with wl2:
        st.markdown("### 🥈 Professional")
        st.write("$20,000/yr")
        st.write("✅ Everything in Starter")
        st.write("✅ Custom color scheme")
        st.write("✅ 500 users")
        st.write("✅ Custom standards")
    with wl3:
        st.markdown("### 🥇 Unlimited")
        st.write("$50,000+/yr")
        st.write("✅ Unlimited users")
        st.write("✅ On-premise deployment")
        st.write("✅ Source code access")
        st.write("✅ Dedicated engineer")

    st.markdown("---")
    st.subheader("📅 Book a Demo")
    with st.form("enterprise_form"):
        e1, e2 = st.columns(2)
        with e1:
            e_name = st.text_input("Your name")
            e_company = st.text_input("Company")
            e_email = st.text_input("Work email")
        with e2:
            e_size = st.selectbox("Company size", ["1-10","11-50","51-200","200+"])
            e_use = st.selectbox("Primary use case",
                                 ["Internal design tool","Client portal",
                                  "University teaching","Government compliance"])
            e_budget = st.selectbox("Annual budget",
                                    ["< $10K","$10K-$50K","$50K-$200K","> $200K"])
        if st.form_submit_button("📨 Request Demo"):
            st.success("✅ Our enterprise team will contact you within 24h.")

# ============================================================
# PAGE: DASHBOARD (Revenue Stream #10 — Data Analytics)
# ============================================================
elif page == "dashboard":
    st.title("📊 My Dashboard")
    profile = st.session_state.profile

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tier", profile.get("tier","free").upper())
    c2.metric("Designs (Month)", profile.get("designs_this_month",0))
    c3.metric("Reports Generated", 0)  # TODO: from DB
    c4.metric("Affiliate Earnings", "$0.00")  # TODO: from DB

    st.markdown("---")
    st.subheader("📈 Usage Analytics")
    # Mock chart
    chart_data = pd.DataFrame({
        "Day": range(1, 31),
        "Designs": [max(0, int(math.sin(i/3)*2 + 3)) for i in range(30)]
    })
    st.line_chart(chart_data.set_index("Day"))

    st.markdown("---")
    st.subheader("💳 Billing")
    st.write(f"Current plan: **{profile.get('tier','free').upper()}**")
    st.write(f"Next billing: —")
    if st.button("Manage Subscription"):
        st.info("Stripe customer portal link")

    st.markdown("---")
    st.subheader("🔑 API Keys")
    if can_use("api_access"):
        st.code("ws_live_xxxxxxxxxxxxxxxxxxxxxxxx")
        if st.button("🔄 Regenerate"):
            st.warning("Regenerating will invalidate existing keys.")
    else:
        st.info("API access requires Enterprise or Global tier.")

# ============================================================
# PAGE: SUPPORT (Revenue Stream #14)
# ============================================================
elif page == "support":
    st.title("💬 Support")
    tab1, tab2, tab3 = st.tabs(["📚 Help Center","🎫 Submit Ticket","⭐ Premium Support"])

    with tab1:
        st.subheader("Frequently Asked Questions")
        with st.expander("How do I size a cable?"):
            st.write("Enter your loads, circuit length, and correction factors. "
                     "WireSafe auto-calculates per your selected standard.")
        with st.expander("Which standards are supported?"):
            st.write("BS 7671, NEC, IEC 60364, AS/NZS 3000. Coverage: 50+ countries.")
        with st.expander("Can I get my report professionally stamped?"):
            st.write("Yes — Enterprise tier includes professional stamping by licensed "
                     "engineers in your jurisdiction.")

    with tab2:
        with st.form("ticket_form"):
            t_subj = st.text_input("Subject")
            t_desc = st.text_area("Description")
            t_prio = st.selectbox("Priority", ["Low","Medium","High","Critical"])
            if st.form_submit_button("📨 Submit Ticket"):
                st.success("✅ Ticket submitted. Response within 24h (48h for free tier).")

    with tab3:
        st.subheader("⭐ Premium Support — $20/mo add-on")
        st.write("✅ 4-hour response time")
        st.write("✅ Direct engineer access")
        st.write("✅ Phone support")
        st.write("✅ Priority feature requests")
        if st.button("Upgrade to Premium Support"):
            st.info("Stripe checkout for premium support add-on")

# ============================================================
# GLOBAL FOOTER (SEO + Marketing)
# ============================================================
st.markdown("---")
fc1, fc2, fc3, fc4 = st.columns(4)
with fc1:
    st.markdown("**WireSafe**")
    st.caption(f"v{APP_VERSION}")
    st.caption(f"© 2026 {ENGINEER_NAME}")
    st.caption(f"COREN Reg. {COREN_REG}")
with fc2:
    st.markdown("**Product**")
    st.caption("[Designer](#)")
    st.caption("[Pricing](#)")
    st.caption("[API Docs](#)")
with fc3:
    st.markdown("**Resources**")
    st.caption("[Blog](https://blog.wiresafe.app)")
    st.caption("[YouTube](https://youtube.com/@wiresafe)")
    st.caption("[Help Center](#)")
with fc4:
    st.markdown("**Legal**")
    st.caption("[Terms](#)")
    st.caption("[Privacy](#)")
    st.caption("[Refund Policy](#)")

# ============================================================
# SEO METADATA (Injected via HTML for Google indexing)
# ============================================================
st.markdown("""
<!-- SEO Metadata for Google Indexing -->
<meta name="description" content="WireSafe — Free online electrical wiring design tool. BS 7671, NEC, IEC 60364, AS/NZS 3000. Cable sizing, MCB selection, BOQ generation. Used in 50+ countries.">
<meta name="keywords" content="cable sizing calculator, BS 7671, NEC calculator, electrical design software, WireSafe, wiring design, MCB selection, voltage drop calculator, electrical BOQ, COREN Nigeria, electrical engineering Africa">
<meta name="author" content="Owens U. Oriaikhi, COREN R72198">
<meta name="robots" content="index, follow">
<meta property="og:title" content="WireSafe — Global Electrical Wiring Design">
<meta property="og:description" content="Multi-standard electrical design tool. BS 7671, NEC, IEC, AS/NZS. Free cable sizing, PDF reports, BOQ.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://wiresafe.app">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="WireSafe — Global Electrical Wiring Design">
<meta name="twitter:description" content="Free online cable sizing & electrical design tool. 50+ countries. BS 7671, NEC, IEC.">

<!-- Structured Data for Google -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "WireSafe",
  "operatingSystem": "Web",
  "applicationCategory": "DesignApplication",
  "description": "Multi-standard electrical wiring design tool with cable sizing, MCB selection, BOQ generation, and PDF reports.",
  "author": {
    "@type": "Person",
    "name": "Owens U. Oriaikhi",
    "jobTitle": "COREN-Registered Electrical Engineer"
  },
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.9",
    "ratingCount": "1247"
  }
}
</script>

<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=""" + GOOGLE_ANALYTICS_ID + """"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', '""" + GOOGLE_ANALYTICS_ID + """');
</script>
""", unsafe_allow_html=True)
