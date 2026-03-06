from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

import streamlit as st

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
APP_TITLE = "AI Fraud Shield Pro"
APP_VERSION = "v7.1"
MODELS_DIR = Path(__file__).resolve().parent / "models"
APP_DIR = Path(__file__).resolve().parent

FRAUD_CATEGORIES = ("UPI Fraud", "Job Scam", "Lottery Scam", "Phishing", "Others")

# UI texts (only English)
UI_TEXT: dict[str, dict[str, str]] = {
    "title": {"en": "AI Fraud Shield Pro"},
    "hero_eyebrow": {"en": "Real-Time Threat Intelligence"},
    "hero_sub": {"en": "SMS · Message · Fraud Risk Analysis Engine"},
    "input_label": {"en": "Input Message"},
    "analyze": {"en": "Analyze"},
    "clear": {"en": "Clear"},
    "redact": {"en": "Redact"},
    "tips_title": {"en": "Preventive guidance"},
    "why_title": {"en": "Why this was flagged"},
    "resources_title": {"en": "Report & support resources"},
    "share": {"en": "Share"},
    "speak": {"en": "Speak"},
    "analysis_results": {"en": "Analysis Results"},
    "pattern_title": {"en": "Pattern analysis — highlighted keywords"},
    "logic_caption": {"en": "Decision logic is based on common scam patterns detected in the text."},
    "logic_none": {"en": "No strong scam patterns were detected in the text."},
    "audio_caption": {"en": "Audio uses your browser’s built‑in speech engine."},
    "tabs_analyze": {"en": "Analyze"},
    "tabs_about": {"en": "About"},
    "about_body": {"en": "### About this prototype\nThis is an **AI-based Fraud Risk Detection & Digital Awareness** tool for rural citizens.\n\n### How to use\n- Paste or dictate the suspicious SMS/WhatsApp message.\n- Tap **Analyze** to see the **scam probability (0–100%)**, risk class, and fraud type.\n- Use **Pattern analysis** + **Why this was flagged** to understand the decision.\n\n### What to do if it’s risky\n- **Do not share OTP / UPI PIN / passwords**\n- **Do not click links** in unknown messages\n- Report immediately: **1930** (National Cyber Helpline, India)\n\n### Notes\n- Some results depend on the available ML models; otherwise the app uses safe heuristics.\n- This is a safety-support tool, not legal/financial advice.\n"},
    "share_email": {"en": "Email"},
    "share_whatsapp": {"en": "WhatsApp"},
    "share_x": {"en": "X / Twitter"},
    "share_download": {"en": "Download"},
    "copy_label": {"en": "Copy text"},
    "voice_hint": {"en": "Tap the mic to dictate, or type/paste below."},
    "min_chars": {"en": "Please enter at least 10 characters."},
    "privacy_tip": {"en": "Tip: don’t paste OTP/UPI PIN. Use Redact to hide sensitive data."},
}

TIPS_I18N: dict[str, dict[str, list[str]]] = {
    "en": {
        "UPI Fraud": [
            "Never share your UPI PIN or OTP — not even with bank employees.",
            "Verify the recipient ID before confirming any payment.",
            "Banks never ask for KYC/passwords via SMS links.",
            "If money is at risk, report to 1930 immediately.",
        ],
        "Job Scam": [
            "No genuine employer charges registration/security fees.",
            "Verify the company on official channels before trusting.",
            "Unrealistic income promises are strong scam signals.",
            "Report at cybercrime.gov.in.",
        ],
        "Lottery Scam": [
            "You can’t win a lottery you never entered.",
            "Never pay a 'processing fee' to claim prizes.",
            "Don’t click unknown links to 'claim'.",
            "Report to 1930.",
        ],
        "Phishing": [
            "Don’t open links asking for KYC/OTP/password.",
            "Type the official URL yourself; don’t follow message links.",
            "Look for misspellings and lookalike domains.",
            "Report to 1930.",
        ],
        "Others": [
            "Don’t click shortened/unfamiliar links.",
            "Verify the sender via official channels.",
            "Never share Aadhaar/PAN/bank details over messages.",
            "Report to 1930.",
        ],
    }
}

# Pre-compiled regex patterns
URL_PATTERN = re.compile(r"(https?://|www\.)\S+", re.I)
SHORT_URL_PATTERN = re.compile(r"\b(bit\.ly|tinyurl\.com|t\.co|rebrand\.ly|cutt\.ly)\b", re.I)
PHONE_PATTERN = re.compile(r"\b\d{10,12}\b")
MONEY_PATTERN = re.compile(r"(rs\.?\s*\d[\d,]*|\d[\d,]*\s*(lakh|crore|thousand|k)|₹\s*\d[\d,]*)", re.I)
EMAIL_PATTERN = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b")

KEYWORD_COLORS: dict[str, str] = {
    "upi": "#00d4ff", "gpay": "#00d4ff", "phonepe": "#00d4ff", "neft": "#00d4ff", "imps": "#00d4ff",
    "pin": "#ff1744", "otp": "#ff1744", "click": "#ff1744", "urgent": "#ff1744", "immediately": "#ff1744",
    "blocked": "#ff1744", "suspended": "#ff1744", "deactivated": "#ff1744",
    "lottery": "#ffb300", "won": "#ffb300", "prize": "#ffb300", "kbc": "#ffb300", "winner": "#ffb300",
    "congratulations": "#ffb300", "job": "#00e676", "salary": "#00e676", "work from home": "#00e676",
    "earn": "#00e676", "hiring": "#00e676", "kyc": "#a855f7", "verify": "#a855f7", "link": "#a855f7",
    "aadhaar": "#a855f7", "pan": "#a855f7", "bank": "#22d3ee", "account": "#22d3ee", "atm": "#22d3ee",
    "courier": "#fb923c", "parcel": "#fb923c", "customs": "#fb923c", "dhl": "#fb923c", "fedex": "#fb923c",
    "netflix": "#e879f9", "subscription": "#e879f9", "amazon prime": "#e879f9",
    "matrimony": "#f472b6", "shaadi": "#f472b6", "scholarship": "#34d399", "exam": "#34d399",
}
_KEYWORDS_SORTED = sorted(KEYWORD_COLORS.keys(), key=len, reverse=True)
KEYWORD_REGEX = re.compile("|".join(re.escape(k) for k in _KEYWORDS_SORTED), re.I)

# ----------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------
def tr(key: str) -> str:
    return UI_TEXT.get(key, {}).get("en", key)

def redact_sensitive(text: str) -> str:
    """Replace PII with placeholders."""
    t = str(text)
    t = URL_PATTERN.sub("[URL]", t)
    t = EMAIL_PATTERN.sub("[EMAIL]", t)
    t = PHONE_PATTERN.sub("[PHONE]", t)
    t = re.sub(r"\b\d{4,8}\b(?![-.]?\d)", "[NUMBER]", t)
    t = MONEY_PATTERN.sub("[AMOUNT]", t)
    return t

def clean_text(text: str) -> str:
    """Normalize text for ML model."""
    t = str(text).lower()
    t = URL_PATTERN.sub(" URL ", t)
    t = PHONE_PATTERN.sub(" PHONE ", t)
    t = MONEY_PATTERN.sub(" AMOUNT ", t)
    t = re.sub(r"[^a-zA-Z\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def highlight_keywords(raw: str) -> str:
    """Wrap keywords in coloured spans."""
    safe = html.escape(raw)
    def _repl(m: re.Match) -> str:
        token = m.group(0)
        color = KEYWORD_COLORS.get(token.lower(), "#00e5ff")
        return (f'<span style="background:rgba(0,0,0,.35);color:{color};'
                f'border-radius:4px;padding:1px 6px;font-weight:700;'
                f'border-bottom:2px solid {color}80;">{html.escape(token)}</span>')
    return KEYWORD_REGEX.sub(_repl, safe)

def detect_signals(raw: str) -> list[dict[str, Any]]:
    """Extract fraud signals from message."""
    msg = raw.lower()
    signals = []

    def add(signal_id: str, label: str, severity: str, evidence: str) -> None:
        signals.append({"id": signal_id, "label": label, "severity": severity, "evidence": evidence})

    if URL_PATTERN.search(msg):
        add("url", "Contains a link / URL", "high", "A URL was found in the message.")
    if SHORT_URL_PATTERN.search(msg):
        add("short_link", "Uses a shortened link", "high", "Shortened links often hide the real website.")
    if PHONE_PATTERN.search(msg):
        add("phone", "Contains a phone number", "medium", "A 10–12 digit number was detected.")
    if MONEY_PATTERN.search(msg):
        add("money", "Mentions money / amount", "medium", "An amount or currency pattern was detected.")
    if any(w in msg for w in ["otp", "pin", "password"]):
        add("secrets", "Asks for OTP / PIN / password", "high", "Scams commonly request OTP/PIN/password.")
    if any(w in msg for w in ["urgent", "immediately", "within", "24 hours", "limited time", "act now"]):
        add("urgency", "Creates urgency / time pressure", "medium", "Urgency is used to force quick action.")
    if any(w in msg for w in ["blocked", "suspended", "deactivated", "kyc", "verify", "update"]):
        add("account_threat", "Account threat / KYC warning", "high", "Account blocks/KYC threats are common phishing tactics.")
    if any(w in msg for w in ["win", "winner", "congratulations", "lottery", "prize", "kbc"]):
        add("lottery", "Prize / lottery claim", "high", "Lottery/prize claims are common scams.")
    if any(w in msg for w in ["job", "hiring", "work from home", "salary", "earn"]):
        add("job", "Job / earning offer", "medium", "Unverified job offers are a common scam pattern.")
    if any(w in msg for w in ["upi", "gpay", "phonepe", "paytm", "bank", "account", "neft", "imps"]):
        add("payments", "Payment/UPI/bank keywords", "medium", "Payment-related keywords increase risk.")
    if any(w in msg for w in ["click", "tap", "open", "download", "install"]):
        add("cta", "Asks you to click/open/install", "medium", "Calls-to-action can indicate phishing.")

    uniq = {s["id"]: s for s in signals}
    return list(uniq.values())

def rule_based_type(msg: str) -> str:
    """Fallback fraud type classifier."""
    m = msg.lower()
    if any(k in m for k in ["upi", "gpay", "phonepe", "paytm", "pin", "otp", "bank", "account", "atm", "neft", "imps"]):
        return "UPI Fraud"
    if any(k in m for k in ["job", "work from home", "salary", "part time", "earning", "vacancy", "hiring"]):
        return "Job Scam"
    if any(k in m for k in ["lottery", "won", "prize", "kbc", "winner", "lucky draw", "congratulations"]):
        return "Lottery Scam"
    if any(k in m for k in ["kyc", "update", "verify", "aadhaar", "pan", "link", "click", "deactivat", "suspended"]):
        return "Phishing"
    return "Others"

def normalize_fraud_type(ftype: str) -> str:
    """Map model output to one of the five categories."""
    s = (ftype or "").strip().lower()
    if any(k in s for k in ["upi", "bank", "banking", "gpay", "phonepe", "paytm", "neft", "imps"]):
        return "UPI Fraud"
    if any(k in s for k in ["job", "work from home", "wfh", "salary", "hiring", "vacancy"]):
        return "Job Scam"
    if any(k in s for k in ["lottery", "kbc", "prize", "winner", "lucky draw", "congratulations"]):
        return "Lottery Scam"
    if any(k in s for k in ["phishing", "kyc", "verify", "update", "aadhaar", "pan", "link", "deactivat", "suspend"]):
        return "Phishing"
    if s in {"none", "safe"}:
        return "None"
    return "Others"

def get_tips(ftype: str) -> list[str]:
    """Return prevention tips for the given fraud type."""
    if ftype not in FRAUD_CATEGORIES and ftype != "None":
        ftype = "Others"
    if ftype == "None":
        ftype = "Others"
    return TIPS_I18N["en"].get(ftype, TIPS_I18N["en"]["Others"])

# ----------------------------------------------------------------------
# Translation function
# ----------------------------------------------------------------------
def translate_to_english(text: str) -> tuple[str, bool]:
    """
    Translate text to English using Google Translate.
    Returns (translated_text, success_flag).
    """
    try:
        from googletrans import Translator
        translator = Translator()
        result = translator.translate(text, dest='en')
        return result.text, True
    except Exception as e:
        st.warning(f"Translation failed: {e}. Using original text.")
        return text, False

# ----------------------------------------------------------------------
# Model Loading
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class ModelBundle:
    risk_model: Any
    tfidf: Any
    label_encoder: Optional[Any] = None
    type_model: Optional[Any] = None

    @property
    def has_type_model(self) -> bool:
        return self.type_model is not None and self.label_encoder is not None

def _load_model(path: Path) -> Any:
    """Try joblib first, then pickle."""
    try:
        import joblib
        return joblib.load(path)
    except ImportError:
        import pickle
        with path.open("rb") as f:
            return pickle.load(f)

@st.cache_resource(show_spinner=False)
def load_models() -> Optional[ModelBundle]:
    """Load ML models from disk."""
    candidates = [MODELS_DIR, APP_DIR]
    risk = tfidf = None
    model_dir = None
    for base in candidates:
        try:
            risk = _load_model(base / "model_risk.pkl")
            tfidf = _load_model(base / "tfidf_vectorizer.pkl")
            model_dir = base
            break
        except FileNotFoundError:
            continue
    if risk is None or tfidf is None:
        return None

    label = type_model = None
    try:
        label = _load_model(model_dir / "label_encoder.pkl")
        type_model = _load_model(model_dir / "model_type.pkl")
    except FileNotFoundError:
        pass

    return ModelBundle(risk_model=risk, tfidf=tfidf, label_encoder=label, type_model=type_model)

def predict(bundle: Optional[ModelBundle], raw: str) -> tuple[float, str, str]:
    """
    Returns (probability_percent, risk_label, fraud_type).
    Works with or without ML models.
    """
    if bundle is None:
        ftype = rule_based_type(raw)
        if ftype == "Others":
            prob = 20.0
            risk = "Safe"
        else:
            prob = 80.0
            risk = "High Risk" if prob >= 70 else "Suspicious"
        return prob, risk, ftype

    vec = bundle.tfidf.transform([clean_text(raw)])
    try:
        proba = bundle.risk_model.predict_proba(vec)
        prob = float(proba[0][1]) * 100 if proba.shape[1] >= 2 else 0.0
    except Exception as e:
        st.warning(f"ML prediction error: {e}. Using fallback.")
        prob = 50.0

    risk = "Safe" if prob < 30 else ("Suspicious" if prob < 70 else "High Risk")

    if risk == "Safe":
        ftype = "None"
    elif bundle.has_type_model:
        try:
            label_id = bundle.type_model.predict(vec)[0]
            ftype = normalize_fraud_type(str(bundle.label_encoder.inverse_transform([label_id])[0]))
        except Exception:
            ftype = rule_based_type(raw)
    else:
        ftype = rule_based_type(raw)

    return prob, risk, ftype

# ----------------------------------------------------------------------
# UI Components
# ----------------------------------------------------------------------
def inject_css() -> None:
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');
:root {
    --bg:#05060d; --surface:#070a14; --panel:#0b1020; --border:#1a2a46;
    --accent:#00e5ff; --accent2:#8b5cf6; --safe:#00e676; --warn:#ffb300; --danger:#ff1744;
    --text:#e6f3ff; --text-soft:#a9c4dd; --muted:#5b7aa0;
    --font-head:'Syne',sans-serif; --font-body:'DM Sans',sans-serif;
}
html,body,.stApp{background:var(--bg)!important;color:var(--text)!important;font-family:var(--font-body)!important;}
.block-container{padding:1.5rem!important;max-width:1200px!important;}
header{background:transparent!important;}
.stButton>button{background:var(--panel)!important;border:1px solid var(--border)!important;color:var(--text-soft)!important;border-radius:8px!important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,var(--accent2),var(--accent))!important;border:none!important;color:#02040a!important;font-weight:700!important;}
.stTextArea textarea{background:var(--panel)!important;border:1px solid var(--border)!important;color:var(--text)!important;border-radius:8px!important;}
.hero{text-align:center;padding:2rem 0;}
.hero-title{font-family:var(--font-head)!important;font-weight:800;font-size:clamp(2rem,5vw,3.5rem);background:linear-gradient(135deg,#fff,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.hero-sub{color:var(--muted);text-transform:uppercase;letter-spacing:0.1em;}
.result-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;margin:1rem 0;}
.result-card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:1.2rem;text-align:center;}
.result-value{font-size:2rem;font-weight:800;line-height:1.2;}
.result-label{font-size:0.8rem;color:var(--muted);text-transform:uppercase;}
.verdict{padding:1.2rem;border-radius:12px;margin:1rem 0;}
.verdict.safe{background:rgba(0,230,118,0.1);border:1px solid var(--safe);}
.verdict.suspicious{background:rgba(255,179,0,0.1);border:1px solid var(--warn);}
.verdict.high-risk{background:rgba(255,23,68,0.1);border:1px solid var(--danger);}
.highlight-box{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:1rem;font-family:monospace;line-height:1.8;}
.footer{text-align:center;color:var(--muted);font-size:0.8rem;padding:2rem 0 0;}
</style>
    """, unsafe_allow_html=True)

def render_sidebar(bundle: Optional[ModelBundle]) -> None:
    with st.sidebar:
        st.markdown("**Test Messages**")
        sample_options = ["", "UPI Fraud", "Job Scam", "Lottery Scam", "Phishing", "Courier Scam", "Safe Message"]
        sample_key = "sample_dropdown"

        # Reset dropdown if flag is set
        if st.session_state.get("reset_sample_dropdown", False):
            st.session_state[sample_key] = ""
            st.session_state.reset_sample_dropdown = False

        sample_option = st.selectbox(
            "Choose a sample",
            sample_options,
            format_func=lambda x: "Select a sample..." if x == "" else x,
            key=sample_key,
        )

        if sample_option and sample_option != st.session_state.get("last_sample"):
            st.session_state.last_sample = sample_option
            sample_map = {
                "UPI Fraud": "Your UPI payment of Rs.5000 to Flipkart is pending. Click tinyurl.com/complete to pay now",
                "Job Scam": "Work from home job: Earn Rs.5000/day typing data. Contact on Telegram @jobs_india",
                "Lottery Scam": "Congratulations! You won Rs.25 lakhs in KBC Lucky Draw. Claim: rebrand.ly/claim-now",
                "Phishing": "Your Aadhaar card will be deactivated in 24 hours. Update now: uidai-update.com",
                "Courier Scam": "Your FedEx courier from USA is held at customs. Pay Rs.5000 to release: bit.ly/pay-now",
                "Safe Message": "Hi, how are you? Let's meet for dinner at 8 pm tonight",
            }
            st.session_state.input_text = sample_map.get(sample_option, "")
            st.session_state.analysis = None
            st.session_state.reset_sample_dropdown = True
            st.rerun()

        st.markdown("---")
        st.markdown("**Voice & Alerts**")
        st.toggle("Enable voice input", key="voice_enabled", value=True)
        st.toggle("Auto-speak results", key="auto_speak", value=True)

        st.markdown("---")
        st.markdown("**Model Status**")
        if bundle is None:
            st.warning("Running in heuristic mode (models not found)")
        else:
            st.success("ML models loaded")
            if bundle.has_type_model:
                st.caption("Fraud type model: available")
            else:
                st.caption("Fraud type model: fallback rules")

        st.markdown("---")
        st.markdown("**Emergency**")
        st.info("📞 **1930** – Cyber Helpline\n\n[cybercrime.gov.in](https://www.cybercrime.gov.in)")

def render_hero() -> None:
    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">{tr("title")}</div>
        <div class="hero-sub">{tr("hero_sub")} · {APP_VERSION}</div>
    </div>
    """, unsafe_allow_html=True)

def render_input() -> bool:
    st.markdown(f"### {tr('input_label')}")

    # Apply pending modifications BEFORE the text_area widget
    if st.session_state.get("redact_requested", False):
        st.session_state.input_text = redact_sensitive(st.session_state.get("input_text", ""))
        st.session_state.redact_requested = False
        st.rerun()

    if st.session_state.get("clear_requested", False):
        st.session_state.input_text = ""
        st.session_state.clear_requested = False
        st.rerun()

    # Voice input (if enabled and available)
    if st.session_state.get("voice_enabled", True):
        try:
            from streamlit_mic_recorder import speech_to_text
            col1, col2 = st.columns([1, 5])
            with col1:
                voice_text = speech_to_text(
                    language="en",
                    start_prompt="🎤 Speak",
                    stop_prompt="⏹️ Stop",
                    just_once=True,
                    use_container_width=True,
                )
            with col2:
                st.caption(tr("voice_hint"))
            if voice_text and voice_text.strip() and voice_text.strip() != st.session_state.get("input_text", ""):
                st.session_state.input_text = voice_text.strip()
                st.session_state.analysis = None
                st.rerun()
        except ImportError:
            st.caption("Voice input unavailable (install streamlit-mic-recorder)")

    # Text input widget
    st.text_area(
        "Message",
        key="input_text",
        height=120,
        placeholder="Paste or type the suspicious message here...",
        max_chars=1000,
        label_visibility="collapsed",
    )
    char_count = len(st.session_state.input_text or "")
    st.caption(f"{char_count}/1000 characters")

    # Translation toggle
    st.checkbox("🌐 Translate to English before analysis (using Google Translate)", key="translate_input", value=False)

    # Action buttons (set flags)
    col1, col2, col3, col4 = st.columns([2, 1, 1, 5])
    with col1:
        analyze = st.button(tr("analyze"), type="primary", use_container_width=True)
    with col2:
        if st.button(tr("redact"), use_container_width=True):
            st.session_state.redact_requested = True
            st.rerun()
    with col3:
        if st.button(tr("clear"), use_container_width=True):
            st.session_state.clear_requested = True
            st.rerun()
    with col4:
        st.caption(tr("privacy_tip"))

    return analyze

def render_results(analysis: dict) -> None:
    r = analysis
    prob = r["prob"]
    risk = r["risk"]
    ftype = r["ftype"] if r["ftype"] != "None" else "No Fraud Detected"

    risk_class = {"Safe": "safe", "Suspicious": "suspicious", "High Risk": "high-risk"}[risk]
    prob_color = {"Safe": "var(--safe)", "Suspicious": "var(--warn)", "High Risk": "var(--danger)"}[risk]

    st.markdown("---")
    st.markdown(f"### {tr('analysis_results')}")

    st.markdown(f"""
    <div class="result-grid">
        <div class="result-card">
            <div class="result-value" style="color:{prob_color}">{prob:.1f}%</div>
            <div class="result-label">Scam probability</div>
        </div>
        <div class="result-card">
            <div class="result-value" style="color:{prob_color}">{risk}</div>
            <div class="result-label">Risk level</div>
        </div>
        <div class="result-card">
            <div class="result-value" style="color:var(--accent2)">{ftype}</div>
            <div class="result-label">Fraud type</div>
        </div>
        <div class="result-card">
            <div class="result-value" style="color:{prob_color}">{
                "No Action" if risk == "Safe" else ("Report Now" if risk == "High Risk" else "Be Cautious")
            }</div>
            <div class="result-label">Recommended action</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    verdict_msgs = {
        "Safe": ("✅ Safe message", "This message appears legitimate. Stay vigilant."),
        "Suspicious": ("⚠️ Suspicious message", "Suspicious patterns detected. Don’t click links or respond until you verify the sender."),
        "High Risk": ("🚨 High risk — likely scam", f"This is highly likely a **{ftype}**. Do not respond/call back/click links. Report to 1930.")
    }
    title, body = verdict_msgs[risk]
    st.markdown(f"""
    <div class="verdict {risk_class}">
        <strong style="font-size:1.2rem;">{title}</strong><br>
        {body}
    </div>
    """, unsafe_allow_html=True)

    # Show original and translated if applicable
    if "original_text" in r and r["original_text"] != r["raw"]:
        with st.expander("Original message (before translation)"):
            st.write(r["original_text"])

    if st.session_state.get("auto_speak", True):
        hash_key = hashlib.md5(f"{risk}_{ftype}_{prob:.0f}".encode()).hexdigest()
        if st.session_state.get("spoken_hash") != hash_key:
            st.session_state.spoken_hash = hash_key
            if risk == "High Risk":
                speak_text = f"High risk scam detected. Fraud type: {ftype}. Do not respond."
            elif risk == "Suspicious":
                speak_text = f"Suspicious message. Possible {ftype}. Be cautious."
            else:
                speak_text = "Message appears safe. Stay vigilant."
            speak(speak_text)

    if st.button(tr("speak"), use_container_width=False):
        speak(f"Risk: {risk}. Type: {ftype}.")

    with st.expander(tr("pattern_title"), expanded=True):
        st.markdown(f'<div class="highlight-box">{r["highlighted"]}</div>', unsafe_allow_html=True)

    with st.expander(tr("why_title"), expanded=True):
        if r.get("signals"):
            st.caption(tr("logic_caption"))
            for s in r["signals"]:
                severity = s["severity"].upper()
                st.markdown(f"- **{severity}**: {s['label']} — {s['evidence']}")
        else:
            st.caption(tr("logic_none"))

    with st.expander(tr("tips_title")):
        for tip in r["tips"]:
            st.markdown(f"- {tip}")

    with st.expander(tr("resources_title")):
        st.markdown("""
        - **1930** — National Cyber Helpline (India)
        - **cybercrime.gov.in** — online reporting
        - **112 / 100** — emergency / local police
        """)

    st.markdown(f"#### {tr('share')}")
    share_text = (
        f"Fraud Alert\n"
        f"Risk: {risk} ({prob:.0f}%)\n"
        f"Type: {ftype}\n"
        f"Report: 1930 | cybercrime.gov.in"
    )
    encoded = quote(share_text)

    cols = st.columns(4)
    with cols[0]:
        st.link_button("📧 Email", f"mailto:?subject={quote('Fraud Alert')}&body={encoded}", use_container_width=True)
    with cols[1]:
        st.link_button("💬 WhatsApp", f"https://wa.me/?text={encoded}", use_container_width=True)
    with cols[2]:
        st.link_button("🐦 X", f"https://twitter.com/intent/tweet?text={encoded[:240]}", use_container_width=True)
    with cols[3]:
        st.download_button("📥 Download", share_text, file_name="fraud-alert.txt", use_container_width=True)

def speak(text: str, repeat: int = 1) -> None:
    safe = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
    js = f"""
    <script>
    (function() {{
        if (!window.speechSynthesis) return;
        var msg = '{safe}', n = {repeat};
        function say(i) {{
            if (i >= n) return;
            var u = new SpeechSynthesisUtterance(msg);
            u.rate = 0.92; u.pitch = 1;
            u.onend = function() {{ say(i+1); }};
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(u);
        }}
        setTimeout(say, 250, 0);
    }})();
    </script>
    """
    st.components.v1.html(js, height=0)

def render_footer() -> None:
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        🛡️ AI Fraud Shield Pro · Powered by Machine Learning<br>
        Report suspicious messages to 1930 · Always verify before sharing personal information
    </div>
    """, unsafe_allow_html=True)

def render_about() -> None:
    st.markdown(tr("about_body"))

# ----------------------------------------------------------------------
# Main App
# ----------------------------------------------------------------------
def init_session_state() -> None:
    defaults = {
        "input_text": "",
        "analysis": None,
        "spoken_hash": None,
        "voice_enabled": True,
        "auto_speak": True,
        "last_sample": None,
        "redact_requested": False,
        "clear_requested": False,
        "translate_input": False,
        "reset_sample_dropdown": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="🛡️", layout="wide")
    init_session_state()
    inject_css()

    bundle = load_models()
    render_sidebar(bundle)
    render_hero()

    tab1, tab2 = st.tabs([tr("tabs_analyze"), tr("tabs_about")])
    with tab1:
        analyze_clicked = render_input()
        if analyze_clicked:
            raw = st.session_state.input_text.strip()
            if len(raw) < 10:
                st.warning(tr("min_chars"))
            else:
                original = raw
                translated = raw
                if st.session_state.get("translate_input", False):
                    with st.spinner("Translating to English..."):
                        translated, success = translate_to_english(raw)
                        if success:
                            st.info(f"Translated text: {translated}")
                with st.spinner("Analyzing..."):
                    prob, risk, ftype = predict(bundle, translated)
                st.session_state.analysis = {
                    "raw": translated,
                    "original_text": original if original != translated else None,
                    "prob": prob,
                    "risk": risk,
                    "ftype": ftype if ftype in FRAUD_CATEGORIES or ftype == "None" else "Others",
                    "highlighted": highlight_keywords(translated),
                    "tips": get_tips(ftype if risk != "Safe" else "Others"),
                    "signals": detect_signals(translated),
                    "mode": "ml" if bundle is not None else "heuristic",
                }
        if st.session_state.analysis:
            render_results(st.session_state.analysis)
    with tab2:
        render_about()

    render_footer()

if __name__ == "__main__":
    main()
