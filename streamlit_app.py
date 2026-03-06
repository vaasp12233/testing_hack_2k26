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
APP_VERSION = "v7.2"
MODELS_DIR = Path(__file__).resolve().parent / "models"
APP_DIR = Path(__file__).resolve().parent

FRAUD_CATEGORIES = ("UPI Fraud", "Job Scam", "Lottery Scam", "Phishing", "Others")

# Supported languages for UI translation
SUPPORTED_LANGUAGES = {
    "English": "en",
    "हिन्दी (Hindi)": "hi",
    "తెలుగు (Telugu)": "te",
}

# UI texts in English, Hindi, Telugu
UI_TEXT: dict[str, dict[str, str]] = {
    "title": {"en": "AI Fraud Shield Pro", "hi": "AI फ्रॉड शील्ड प्रो", "te": "AI మోసం నిరోధక్"},
    "hero_eyebrow": {"en": "Real-Time Threat Intelligence", "hi": "रीयल-टाइम खतरा इंटेलिजेंस", "te": "రియల్-టైమ్ ముప్పు నిఘా"},
    "hero_sub": {"en": "SMS · Message · Fraud Risk Analysis Engine", "hi": "SMS · संदेश · धोखाधड़ी जोखिम विश्लेषण", "te": "SMS · సందేశం · మోసం నష్ట విశ్లేషణ"},
    "input_label": {"en": "Input Message", "hi": "संदेश दर्ज करें", "te": "సందేశం నమోదు చేయండి"},
    "analyze": {"en": "Analyze", "hi": "विश्लेषण करें", "te": "విశ్లేషించు"},
    "clear": {"en": "Clear", "hi": "साफ करें", "te": "తొలగించు"},
    "redact": {"en": "Redact", "hi": "छुपाएं", "te": "దాచు"},
    "tips_title": {"en": "Preventive guidance", "hi": "निवारक मार्गदर्शन", "te": "నివారణ మార్గదర్శకత్వం"},
    "why_title": {"en": "Why this was flagged", "hi": "यह क्यों फ्लैग किया गया", "te": "ఇది ఎందుకు గుర్తించబడింది"},
    "resources_title": {"en": "Report & support resources", "hi": "रिपोर्ट और सहायता संसाधन", "te": "నివేదించడం మరియు సహాయ వనరులు"},
    "share": {"en": "Share", "hi": "साझा करें", "te": "పంచుకోండి"},
    "speak": {"en": "Speak", "hi": "बोलें", "te": "మాట్లాడు"},
    "analysis_results": {"en": "Analysis Results", "hi": "विश्लेषण परिणाम", "te": "విశ్లేషణ ఫలితాలు"},
    "pattern_title": {"en": "Pattern analysis — highlighted keywords", "hi": "पैटर्न विश्लेषण — हाइलाइट किए गए कीवर्ड", "te": "పాటర్న్ విశ్లేషణ — హైలైట్ చేసిన కీవర్డ్‌లు"},
    "logic_caption": {"en": "Decision logic is based on common scam patterns detected in the text.", "hi": "निर्णय तर्क पाठ में पाए गए सामान्य घोटाले पैटर्न पर आधारित है।", "te": "నిర్ణయ తర్కం వచనంలో గుర్తించిన సాధారణ మోసపు నమూనాలపై ఆధారపడింది."},
    "logic_none": {"en": "No strong scam patterns were detected in the text.", "hi": "पाठ में कोई मजबूत घोटाला पैटर्न नहीं मिला।", "te": "వచనంలో బలమైన మోసపు నమూనాలు గుర్తించబడలేదు."},
    "audio_caption": {"en": "Audio uses your browser's built‑in speech engine.", "hi": "ऑडियो आपके ब्राउज़र के बिल्ट-इन स्पीच इंजन का उपयोग करता है।", "te": "ఆడియో మీ బ్రౌజర్ యొక్క అంతర్నిర్మిత స్పీచ్ ఇంజిన్‌ను ఉపయోగిస్తుంది."},
    "tabs_analyze": {"en": "Analyze", "hi": "विश्लेषण", "te": "విశ్లేషణ"},
    "tabs_about": {"en": "About", "hi": "परिचय", "te": "గురించి"},
    "about_body": {
        "en": "### About this prototype\nThis is an **AI-based Fraud Risk Detection & Digital Awareness** tool for rural citizens.\n\n### How to use\n- Paste or dictate the suspicious SMS/WhatsApp message.\n- Tap **Analyze** to see the **scam probability (0–100%)**, risk class, and fraud type.\n- Use **Pattern analysis** + **Why this was flagged** to understand the decision.\n\n### What to do if it's risky\n- **Do not share OTP / UPI PIN / passwords**\n- **Do not click links** in unknown messages\n- Report immediately: **1930** (National Cyber Helpline, India)\n\n### Notes\n- Some results depend on the available ML models; otherwise the app uses safe heuristics.\n- This is a safety-support tool, not legal/financial advice.\n",
        "hi": "### इस प्रोटोटाइप के बारे में\nयह ग्रामीण नागरिकों के लिए **AI-आधारित धोखाधड़ी जोखिम पहचान और डिजिटल जागरूकता** उपकरण है।\n\n### उपयोग कैसे करें\n- संदिग्ध SMS/WhatsApp संदेश चिपकाएं या बोलें।\n- **विश्लेषण करें** टैप करें।\n\n### यदि जोखिम हो तो क्या करें\n- **OTP / UPI PIN / पासवर्ड साझा न करें**\n- **अज्ञात संदेशों में लिंक पर क्लिक न करें**\n- तुरंत रिपोर्ट करें: **1930**\n",
        "te": "### ఈ ప్రోటోటైప్ గురించి\nఇది గ్రామీణ పౌరుల కోసం **AI ఆధారిత మోసం నష్ట గుర్తింపు మరియు డిజిటల్ అవగాహన** సాధనం.\n\n### ఎలా ఉపయోగించాలి\n- అనుమానాస్పద SMS/WhatsApp సందేశాన్ని అతికించండి లేదా చెప్పండి.\n- **విశ్లేషించు** నొక్కండి.\n\n### నష్టం అయితే ఏం చేయాలి\n- **OTP / UPI PIN / పాస్‌వర్డ్ పంచుకోవద్దు**\n- తక్షణం నివేదించండి: **1930**\n",
    },
    "share_email": {"en": "Email", "hi": "ईमेल", "te": "ఇమెయిల్"},
    "share_whatsapp": {"en": "WhatsApp", "hi": "व्हाट्सएप", "te": "వాట్సాప్"},
    "share_x": {"en": "X / Twitter", "hi": "X / ट्विटर", "te": "X / ట్విటర్"},
    "share_download": {"en": "Download", "hi": "डाउनलोड", "te": "డౌన్‌లోడ్"},
    "copy_label": {"en": "Copy text", "hi": "टेक्स्ट कॉपी करें", "te": "వచనాన్ని కాపీ చేయండి"},
    "voice_hint": {"en": "Tap the mic to dictate, or type/paste below.", "hi": "बोलने के लिए माइक टैप करें, या नीचे टाइप/पेस्ट करें।", "te": "చెప్పడానికి మైక్ నొక్కండి, లేదా క్రింద టైప్/పేస్ట్ చేయండి."},
    "min_chars": {"en": "Please enter at least 10 characters.", "hi": "कृपया कम से कम 10 अक्षर दर्ज करें।", "te": "దయచేసి కనీసం 10 అక్షరాలు నమోదు చేయండి."},
    "privacy_tip": {"en": "Tip: don't paste OTP/UPI PIN. Use Redact to hide sensitive data.", "hi": "सुझाव: OTP/UPI PIN पेस्ट न करें। संवेदनशील डेटा छुपाने के लिए Redact का उपयोग करें।", "te": "చిట్కా: OTP/UPI PIN పేస్ట్ చేయవద్దు. సున్నితమైన డేటా దాచడానికి Redact ఉపయోగించండి."},
    "language_select": {"en": "Interface Language", "hi": "इंटरफ़ेस भाषा", "te": "ఇంటర్ఫేస్ భాష"},
    "translate_toggle": {"en": "🌐 Translate message to English before analysis", "hi": "🌐 विश्लेषण से पहले संदेश को अंग्रेजी में अनुवाद करें", "te": "🌐 విశ్లేషణకు ముందు సందేశాన్ని ఆంగ్లంలోకి అనువదించండి"},
    "translating": {"en": "Translating to English...", "hi": "अंग्रेजी में अनुवाद हो रहा है...", "te": "ఆంగ్లంలోకి అనువదిస్తోంది..."},
    "analyzing": {"en": "Analyzing...", "hi": "विश्लेषण हो रहा है...", "te": "విశ్లేషిస్తోంది..."},
    "translated_text": {"en": "Translated text", "hi": "अनुवादित पाठ", "te": "అనువదించిన వచనం"},
    "original_msg": {"en": "Original message (before translation)", "hi": "मूल संदेश (अनुवाद से पहले)", "te": "అసలు సందేశం (అనువాదానికి ముందు)"},
    "safe_msg_title": {"en": "✅ Safe message", "hi": "✅ सुरक्षित संदेश", "te": "✅ సురక్షిత సందేశం"},
    "safe_msg_body": {"en": "This message appears legitimate. Stay vigilant.", "hi": "यह संदेश वैध लगता है। सतर्क रहें।", "te": "ఈ సందేశం చట్టబద్ధంగా కనిపిస్తోంది. అప్రమత్తంగా ఉండండి."},
    "susp_msg_title": {"en": "⚠️ Suspicious message", "hi": "⚠️ संदिग्ध संदेश", "te": "⚠️ అనుమానాస్పద సందేశం"},
    "susp_msg_body": {"en": "Suspicious patterns detected. Don't click links or respond until you verify the sender.", "hi": "संदिग्ध पैटर्न पाए गए। सत्यापित करने तक लिंक पर क्लिक न करें।", "te": "అనుమానాస్పద నమూనాలు గుర్తించబడ్డాయి. పంపినవారిని ధృవీకరించే వరకు లింక్‌లపై క్లిక్ చేయవద్దు."},
    "high_msg_title": {"en": "🚨 High risk — likely scam", "hi": "🚨 उच्च जोखिम — संभावित घोटाला", "te": "🚨 అధిక నష్టం — మోసం అయి ఉండవచ్చు"},
    "no_action": {"en": "No Action", "hi": "कोई कार्रवाई नहीं", "te": "చర్య అవసరం లేదు"},
    "report_now": {"en": "Report Now", "hi": "अभी रिपोर्ट करें", "te": "ఇప్పుడే నివేదించండి"},
    "be_cautious": {"en": "Be Cautious", "hi": "सावधान रहें", "te": "జాగ్రత్తగా ఉండండి"},
    "scam_prob": {"en": "Scam probability", "hi": "घोटाला संभावना", "te": "మోసం సంభావ్యత"},
    "risk_level": {"en": "Risk level", "hi": "जोखिम स्तर", "te": "నష్ట స్థాయి"},
    "fraud_type": {"en": "Fraud type", "hi": "धोखाधड़ी प्रकार", "te": "మోసం రకం"},
    "rec_action": {"en": "Recommended action", "hi": "अनुशंसित कार्रवाई", "te": "సిఫార్సు చేసిన చర్య"},
    "no_fraud": {"en": "No Fraud Detected", "hi": "कोई धोखाधड़ी नहीं", "te": "మోసం గుర్తించబడలేదు"},
    "voice_unavail": {"en": "Voice input unavailable (install streamlit-mic-recorder)", "hi": "वॉइस इनपुट उपलब्ध नहीं (streamlit-mic-recorder इंस्टॉल करें)", "te": "వాయిస్ ఇన్‌పుట్ అందుబాటులో లేదు"},
    "test_messages": {"en": "Test Messages", "hi": "परीक्षण संदेश", "te": "పరీక్ష సందేశాలు"},
    "choose_sample": {"en": "Choose a sample", "hi": "एक नमूना चुनें", "te": "ఒక నమూనా ఎంచుకోండి"},
    "select_sample": {"en": "Select a sample...", "hi": "नमूना चुनें...", "te": "నమూనా ఎంచుకోండి..."},
    "voice_alerts": {"en": "Voice & Alerts", "hi": "आवाज़ और अलर्ट", "te": "వాయిస్ మరియు హెచ్చరికలు"},
    "enable_voice": {"en": "Enable voice input", "hi": "वॉइस इनपुट सक्षम करें", "te": "వాయిస్ ఇన్‌పుట్ ప్రారంభించండి"},
    "auto_speak": {"en": "Auto-speak results", "hi": "परिणाम स्वतः बोलें", "te": "ఫలితాలు స్వయంచాలకంగా చెప్పు"},
    "model_status": {"en": "Model Status", "hi": "मॉडल स्थिति", "te": "మోడల్ స్థితి"},
    "heuristic_mode": {"en": "Running in heuristic mode (models not found)", "hi": "ह्यूरिस्टिक मोड में चल रहा है (मॉडल नहीं मिले)", "te": "హ్యూరిస్టిక్ మోడ్‌లో నడుస్తోంది (మోడల్‌లు కనుగొనబడలేదు)"},
    "ml_loaded": {"en": "ML models loaded", "hi": "ML मॉडल लोड हुए", "te": "ML మోడల్‌లు లోడ్ అయ్యాయి"},
    "type_available": {"en": "Fraud type model: available", "hi": "धोखाधड़ी प्रकार मॉडल: उपलब्ध", "te": "మోసం రకం మోడల్: అందుబాటులో ఉంది"},
    "type_fallback": {"en": "Fraud type model: fallback rules", "hi": "धोखाधड़ी प्रकार मॉडल: फॉलबैक नियम", "te": "మోసం రకం మోడల్: ఫాల్‌బ్యాక్ నియమాలు"},
    "emergency": {"en": "Emergency", "hi": "आपातकाल", "te": "అత్యవసరం"},
    "emergency_info": {"en": "📞 **1930** – Cyber Helpline\n\n[cybercrime.gov.in](https://www.cybercrime.gov.in)", "hi": "📞 **1930** – साइबर हेल्पलाइन\n\n[cybercrime.gov.in](https://www.cybercrime.gov.in)", "te": "📞 **1930** – సైబర్ హెల్ప్‌లైన్\n\n[cybercrime.gov.in](https://www.cybercrime.gov.in)"},
    "footer": {"en": "🛡️ AI Fraud Shield Pro · Powered by Machine Learning\nReport suspicious messages to 1930 · Always verify before sharing personal information", "hi": "🛡️ AI फ्रॉड शील्ड प्रो · मशीन लर्निंग द्वारा संचालित\n1930 को संदिग्ध संदेश रिपोर्ट करें", "te": "🛡️ AI మోసం నిరోధక్ · మెషీన్ లెర్నింగ్ ద్వారా నడపబడుతోంది\n1930కి అనుమానాస్పద సందేశాలు నివేదించండి"},
    "char_count": {"en": "characters", "hi": "अक्षर", "te": "అక్షరాలు"},
    "translate_failed": {"en": "Translation failed. Using original text.", "hi": "अनुवाद विफल रहा। मूल पाठ का उपयोग किया जा रहा है।", "te": "అనువాదం విఫలమైంది. అసలు వచనం ఉపయోగిస్తోంది."},
    "fraud_alert": {"en": "Fraud Alert", "hi": "धोखाधड़ी चेतावनी", "te": "మోసం హెచ్చరిక"},
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
            "You can't win a lottery you never entered.",
            "Never pay a 'processing fee' to claim prizes.",
            "Don't click unknown links to 'claim'.",
            "Report to 1930.",
        ],
        "Phishing": [
            "Don't open links asking for KYC/OTP/password.",
            "Type the official URL yourself; don't follow message links.",
            "Look for misspellings and lookalike domains.",
            "Report to 1930.",
        ],
        "Others": [
            "Don't click shortened/unfamiliar links.",
            "Verify the sender via official channels.",
            "Never share Aadhaar/PAN/bank details over messages.",
            "Report to 1930.",
        ],
    },
    "hi": {
        "UPI Fraud": [
            "कभी भी अपना UPI PIN या OTP साझा न करें — यहां तक कि बैंक कर्मचारियों के साथ भी नहीं।",
            "कोई भी भुगतान करने से पहले प्राप्तकर्ता की ID जांचें।",
            "बैंक कभी भी SMS लिंक के माध्यम से KYC/पासवर्ड नहीं मांगते।",
            "यदि पैसा खतरे में हो, तो तुरंत 1930 पर रिपोर्ट करें।",
        ],
        "Job Scam": [
            "कोई भी वास्तविक नियोक्ता पंजीकरण/सुरक्षा शुल्क नहीं लेता।",
            "भरोसा करने से पहले आधिकारिक चैनलों पर कंपनी की जांच करें।",
            "अवास्तविक आय वादे घोटाले के मजबूत संकेत हैं।",
            "cybercrime.gov.in पर रिपोर्ट करें।",
        ],
        "Lottery Scam": [
            "आप वह लॉटरी नहीं जीत सकते जो आपने कभी भरी नहीं।",
            "पुरस्कार पाने के लिए कभी 'प्रोसेसिंग फी' न दें।",
            "'क्लेम' करने के लिए अज्ञात लिंक पर क्लिक न करें।",
            "1930 पर रिपोर्ट करें।",
        ],
        "Phishing": [
            "KYC/OTP/पासवर्ड मांगने वाले लिंक न खोलें।",
            "आधिकारिक URL खुद टाइप करें; संदेश लिंक का पालन न करें।",
            "गलत वर्तनी और नकली डोमेन देखें।",
            "1930 पर रिपोर्ट करें।",
        ],
        "Others": [
            "संक्षिप्त/अपरिचित लिंक पर क्लिक न करें।",
            "आधिकारिक चैनलों के माध्यम से प्रेषक की जांच करें।",
            "संदेशों पर कभी आधार/पैन/बैंक विवरण साझा न करें।",
            "1930 पर रिपोर्ट करें।",
        ],
    },
    "te": {
        "UPI Fraud": [
            "మీ UPI PIN లేదా OTP ఎప్పుడూ పంచుకోవద్దు — బ్యాంక్ ఉద్యోగులతో కూడా కాదు.",
            "ఏదైనా చెల్లింపు నిర్ధారించే ముందు రిసీవర్ ID తనిఖీ చేయండి.",
            "బ్యాంకులు SMS లింక్‌ల ద్వారా KYC/పాస్‌వర్డ్‌లు అడగవు.",
            "డబ్బు నష్టం జరిగితే వెంటనే 1930కి నివేదించండి.",
        ],
        "Job Scam": [
            "ఏ నిజమైన యజమాని పంజీకరణ/భద్రతా రుసుమును వసూలు చేయడు.",
            "నమ్మే ముందు అధికారిక ఛానెల్‌లలో కంపెనీని ధృవీకరించండి.",
            "అవాస్తవిక ఆదాయ వాగ్దానాలు మోసానికి బలమైన సంకేతాలు.",
            "cybercrime.gov.in లో నివేదించండి.",
        ],
        "Lottery Scam": [
            "మీరు ఎప్పుడూ పాల్గొనని లాటరీలో గెలవలేరు.",
            "బహుమతులు పొందడానికి 'ప్రాసెసింగ్ ఫీజు' ఎప్పుడూ చెల్లించవద్దు.",
            "'క్లెయిమ్' చేయడానికి అज్ఞాత లింక్‌లపై క్లిక్ చేయవద్దు.",
            "1930కి నివేదించండి.",
        ],
        "Phishing": [
            "KYC/OTP/పాస్‌వర్డ్ అడిగే లింక్‌లు తెరవద్దు.",
            "అధికారిక URL మీరే టైప్ చేయండి; సందేశ లింక్‌లను అనుసరించవద్దు.",
            "తప్పుడు స్పెల్లింగ్‌లు మరియు నకిలీ డొమైన్‌ల కోసం చూడండి.",
            "1930కి నివేదించండి.",
        ],
        "Others": [
            "చిన్న/అపరిచిత లింక్‌లపై క్లిక్ చేయవద్దు.",
            "అధికారిక ఛానెల్‌ల ద్వారా పంపినవారిని ధృవీకరించండి.",
            "సందేశాల ద్వారా ఆధార్/పాన్/బ్యాంక్ వివరాలు పంచుకోవద్దు.",
            "1930కి నివేదించండి.",
        ],
    },
}

# Pre-compiled regex patterns
URL_PATTERN = re.compile(r"(https?://|www\.)\S+", re.I)
SHORT_URL_PATTERN = re.compile(r"\b(bit\.ly|tinyurl\.com|t\.co|rebrand\.ly|cutt\.ly)\b", re.I)
PHONE_PATTERN = re.compile(r"\b\d{10,12}\b")
MONEY_PATTERN = re.compile(r"(rs\.?\s*\d[\d,]*|\d[\d,]*\s*(lakh|crore|thousand|k)|₹\s*\d[\d,]*)", re.I)
EMAIL_PATTERN = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b")

KEYWORD_COLORS: dict[str, str] = {
    "upi": "#0ea5e9", "gpay": "#0ea5e9", "phonepe": "#0ea5e9", "neft": "#0ea5e9", "imps": "#0ea5e9",
    "pin": "#ef4444", "otp": "#ef4444", "click": "#ef4444", "urgent": "#ef4444", "immediately": "#ef4444",
    "blocked": "#ef4444", "suspended": "#ef4444", "deactivated": "#ef4444",
    "lottery": "#f59e0b", "won": "#f59e0b", "prize": "#f59e0b", "kbc": "#f59e0b", "winner": "#f59e0b",
    "congratulations": "#f59e0b", "job": "#22c55e", "salary": "#22c55e", "work from home": "#22c55e",
    "earn": "#22c55e", "hiring": "#22c55e", "kyc": "#a855f7", "verify": "#a855f7", "link": "#a855f7",
    "aadhaar": "#a855f7", "pan": "#a855f7", "bank": "#06b6d4", "account": "#06b6d4", "atm": "#06b6d4",
    "courier": "#f97316", "parcel": "#f97316", "customs": "#f97316", "dhl": "#f97316", "fedex": "#f97316",
    "netflix": "#e879f9", "subscription": "#e879f9", "amazon prime": "#e879f9",
    "matrimony": "#f472b6", "shaadi": "#f472b6", "scholarship": "#34d399", "exam": "#34d399",
}
_KEYWORDS_SORTED = sorted(KEYWORD_COLORS.keys(), key=len, reverse=True)
KEYWORD_REGEX = re.compile("|".join(re.escape(k) for k in _KEYWORDS_SORTED), re.I)

# ----------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------
def tr(key: str) -> str:
    lang = st.session_state.get("ui_lang", "en")
    return UI_TEXT.get(key, {}).get(lang, UI_TEXT.get(key, {}).get("en", key))

def redact_sensitive(text: str) -> str:
    t = str(text)
    t = URL_PATTERN.sub("[URL]", t)
    t = EMAIL_PATTERN.sub("[EMAIL]", t)
    t = PHONE_PATTERN.sub("[PHONE]", t)
    t = re.sub(r"\b\d{4,8}\b(?![-.]?\d)", "[NUMBER]", t)
    t = MONEY_PATTERN.sub("[AMOUNT]", t)
    return t

def clean_text(text: str) -> str:
    t = str(text).lower()
    t = URL_PATTERN.sub(" URL ", t)
    t = PHONE_PATTERN.sub(" PHONE ", t)
    t = MONEY_PATTERN.sub(" AMOUNT ", t)
    t = re.sub(r"[^a-zA-Z\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def highlight_keywords(raw: str) -> str:
    safe = html.escape(raw)
    def _repl(m: re.Match) -> str:
        token = m.group(0)
        color = KEYWORD_COLORS.get(token.lower(), "#0ea5e9")
        return (f'<span class="kw-highlight" style="--kw-color:{color}">{html.escape(token)}</span>')
    return KEYWORD_REGEX.sub(_repl, safe)

def detect_signals(raw: str) -> list[dict[str, Any]]:
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
    lang = st.session_state.get("ui_lang", "en")
    if lang not in TIPS_I18N:
        lang = "en"
    tips_lang = TIPS_I18N[lang]
    if ftype not in FRAUD_CATEGORIES and ftype != "None":
        ftype = "Others"
    if ftype == "None":
        ftype = "Others"
    return tips_lang.get(ftype, tips_lang["Others"])

# ----------------------------------------------------------------------
# Translation function
# ----------------------------------------------------------------------
def translate_to_english(text: str) -> tuple[str, bool]:
    try:
        from googletrans import Translator
        translator = Translator()
        result = translator.translate(text, dest='en')
        return result.text, True
    except Exception as e:
        st.warning(f"{tr('translate_failed')} ({e})")
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
    try:
        import joblib
        return joblib.load(path)
    except ImportError:
        import pickle
        with path.open("rb") as f:
            return pickle.load(f)

@st.cache_resource(show_spinner=False)
def load_models() -> Optional[ModelBundle]:
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
# CSS — adaptive light / dark
# ----------------------------------------------------------------------
def inject_css() -> None:
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap');

/* ── DARK MODE (default Streamlit dark) ─────────────────────────────── */
:root {
    --bg: #05060d;
    --surface: #070a14;
    --panel: #0b1020;
    --panel-hover: #0f1828;
    --border: #1a2a46;
    --border-strong: #2a3f60;
    --accent: #00e5ff;
    --accent2: #8b5cf6;
    --safe: #22c55e;
    --warn: #f59e0b;
    --danger: #ef4444;
    --text: #e6f3ff;
    --text-soft: #a9c4dd;
    --muted: #5b7aa0;
    --shadow: rgba(0,0,0,0.5);
    --font-head: 'Syne', sans-serif;
    --font-body: 'DM Sans', sans-serif;
    --input-bg: #0b1020;
    --input-border: #1a2a46;
    --input-text: #e6f3ff;
    --sidebar-bg: #070a14;
    --card-bg: #0b1020;
    --highlight-bg: #0b1020;
    --verdict-safe-bg: rgba(34,197,94,0.08);
    --verdict-safe-border: #22c55e;
    --verdict-warn-bg: rgba(245,158,11,0.08);
    --verdict-warn-border: #f59e0b;
    --verdict-danger-bg: rgba(239,68,68,0.08);
    --verdict-danger-border: #ef4444;
    --kw-bg: rgba(0,0,0,0.4);
    --severity-high: #ef4444;
    --severity-medium: #f59e0b;
    --severity-low: #22c55e;
    --divider: #1a2a46;
    --tab-active: #00e5ff;
    --btn-bg: #0b1020;
    --btn-border: #1a2a46;
    --btn-text: #a9c4dd;
}

/* ── LIGHT MODE ──────────────────────────────────────────────────────── */
[data-theme="light"],
.stApp[data-theme="light"],
@media (prefers-color-scheme: light) {
    :root {
        --bg: #f0f4fb;
        --surface: #ffffff;
        --panel: #ffffff;
        --panel-hover: #f5f8ff;
        --border: #d0dbe8;
        --border-strong: #a0b4cc;
        --accent: #0078d4;
        --accent2: #7c3aed;
        --safe: #16a34a;
        --warn: #d97706;
        --danger: #dc2626;
        --text: #0f1f30;
        --text-soft: #2d4a6a;
        --muted: #6b87a4;
        --shadow: rgba(0,0,0,0.12);
        --input-bg: #ffffff;
        --input-border: #c8d8e8;
        --input-text: #0f1f30;
        --sidebar-bg: #ffffff;
        --card-bg: #ffffff;
        --highlight-bg: #f8fafd;
        --verdict-safe-bg: rgba(22,163,74,0.08);
        --verdict-safe-border: #16a34a;
        --verdict-warn-bg: rgba(217,119,6,0.08);
        --verdict-warn-border: #d97706;
        --verdict-danger-bg: rgba(220,38,38,0.08);
        --verdict-danger-border: #dc2626;
        --kw-bg: rgba(0,0,0,0.06);
        --severity-high: #dc2626;
        --severity-medium: #d97706;
        --severity-low: #16a34a;
        --divider: #d0dbe8;
        --tab-active: #0078d4;
        --btn-bg: #ffffff;
        --btn-border: #c8d8e8;
        --btn-text: #2d4a6a;
    }
}

/* Streamlit's own light theme override */
.stApp[data-baseweb-theme="light"],
.stApp[class*="light"] {
    --bg: #f0f4fb !important;
    --surface: #ffffff !important;
    --panel: #ffffff !important;
    --panel-hover: #f5f8ff !important;
    --border: #d0dbe8 !important;
    --border-strong: #a0b4cc !important;
    --accent: #0078d4 !important;
    --accent2: #7c3aed !important;
    --safe: #16a34a !important;
    --warn: #d97706 !important;
    --danger: #dc2626 !important;
    --text: #0f1f30 !important;
    --text-soft: #2d4a6a !important;
    --muted: #6b87a4 !important;
    --shadow: rgba(0,0,0,0.12) !important;
    --input-bg: #ffffff !important;
    --input-border: #c8d8e8 !important;
    --input-text: #0f1f30 !important;
    --sidebar-bg: #ffffff !important;
    --card-bg: #ffffff !important;
    --highlight-bg: #f8fafd !important;
    --verdict-safe-bg: rgba(22,163,74,0.08) !important;
    --verdict-safe-border: #16a34a !important;
    --verdict-warn-bg: rgba(217,119,6,0.08) !important;
    --verdict-warn-border: #d97706 !important;
    --verdict-danger-bg: rgba(220,38,38,0.08) !important;
    --verdict-danger-border: #dc2626 !important;
    --kw-bg: rgba(0,0,0,0.06) !important;
    --severity-high: #dc2626 !important;
    --severity-medium: #d97706 !important;
    --severity-low: #16a34a !important;
    --divider: #d0dbe8 !important;
    --tab-active: #0078d4 !important;
    --btn-bg: #ffffff !important;
    --btn-border: #c8d8e8 !important;
    --btn-text: #2d4a6a !important;
}

/* ── BASE LAYOUT ─────────────────────────────────────────────────────── */
html, body, .stApp {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--font-body) !important;
}

.block-container {
    padding: 1.5rem !important;
    max-width: 1200px !important;
}

header { background: transparent !important; }

/* ── SIDEBAR ─────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--sidebar-bg) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] * {
    color: var(--text) !important;
}

[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown strong {
    color: var(--text-soft) !important;
}

[data-testid="stSidebar"] .stSelectbox > div > div {
    background: var(--panel) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
}

[data-testid="stSidebar"] [data-testid="stToggle"] label {
    color: var(--text-soft) !important;
}

/* ── BUTTONS ─────────────────────────────────────────────────────────── */
.stButton > button {
    background: var(--btn-bg) !important;
    border: 1px solid var(--btn-border) !important;
    color: var(--btn-text) !important;
    border-radius: 8px !important;
    font-family: var(--font-body) !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    background: var(--panel-hover) !important;
    border-color: var(--border-strong) !important;
    color: var(--text) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px var(--shadow) !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent2), var(--accent)) !important;
    border: none !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 12px rgba(139,92,246,0.3) !important;
}

.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(139,92,246,0.4) !important;
    transform: translateY(-2px) !important;
}

/* ── LINK BUTTONS ────────────────────────────────────────────────────── */
.stLinkButton > a {
    background: var(--btn-bg) !important;
    border: 1px solid var(--btn-border) !important;
    color: var(--btn-text) !important;
    border-radius: 8px !important;
    font-family: var(--font-body) !important;
    font-weight: 500 !important;
    text-decoration: none !important;
}

.stLinkButton > a:hover {
    background: var(--panel-hover) !important;
    border-color: var(--border-strong) !important;
    color: var(--accent) !important;
}

/* ── DOWNLOAD BUTTON ─────────────────────────────────────────────────── */
[data-testid="stDownloadButton"] > button {
    background: var(--btn-bg) !important;
    border: 1px solid var(--btn-border) !important;
    color: var(--btn-text) !important;
    border-radius: 8px !important;
}

/* ── TEXT AREA ───────────────────────────────────────────────────────── */
.stTextArea textarea {
    background: var(--input-bg) !important;
    border: 1.5px solid var(--input-border) !important;
    color: var(--input-text) !important;
    border-radius: 10px !important;
    font-family: var(--font-body) !important;
    font-size: 0.95rem !important;
    transition: border-color 0.2s ease !important;
}

.stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(0,229,255,0.1) !important;
}

.stTextArea textarea::placeholder {
    color: var(--muted) !important;
}

/* ── SELECTBOX ───────────────────────────────────────────────────────── */
.stSelectbox > div > div {
    background: var(--input-bg) !important;
    border-color: var(--input-border) !important;
    color: var(--input-text) !important;
    border-radius: 8px !important;
}

.stSelectbox svg {
    fill: var(--muted) !important;
}

/* ── CHECKBOX ────────────────────────────────────────────────────────── */
.stCheckbox label {
    color: var(--text-soft) !important;
    font-size: 0.9rem !important;
}

/* ── TABS ────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--divider) !important;
    gap: 0.5rem !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--muted) !important;
    border: none !important;
    padding: 0.6rem 1.2rem !important;
    font-family: var(--font-body) !important;
    font-weight: 500 !important;
    border-radius: 8px 8px 0 0 !important;
    transition: color 0.2s ease !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--text) !important;
    background: var(--panel) !important;
}

.stTabs [aria-selected="true"] {
    color: var(--tab-active) !important;
    font-weight: 700 !important;
    border-bottom: 2px solid var(--tab-active) !important;
}

/* ── EXPANDER ────────────────────────────────────────────────────────── */
.stExpander {
    background: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    margin-bottom: 0.75rem !important;
    overflow: hidden !important;
}

.stExpander summary {
    color: var(--text-soft) !important;
    font-weight: 600 !important;
    padding: 0.8rem 1rem !important;
}

.stExpander summary:hover {
    color: var(--text) !important;
    background: var(--panel-hover) !important;
}

.stExpander [data-testid="stExpanderDetails"] {
    background: var(--panel) !important;
    color: var(--text) !important;
    padding: 0 1rem 1rem !important;
}

/* ── ALERTS / INFO / WARNING ─────────────────────────────────────────── */
.stAlert {
    border-radius: 8px !important;
}

[data-testid="stInfo"] {
    background: rgba(0,120,212,0.1) !important;
    border-color: var(--accent) !important;
    color: var(--text) !important;
}

[data-testid="stWarning"] {
    background: rgba(245,158,11,0.1) !important;
    border-color: var(--warn) !important;
    color: var(--text) !important;
}

[data-testid="stSuccess"] {
    background: rgba(34,197,94,0.1) !important;
    border-color: var(--safe) !important;
    color: var(--text) !important;
}

/* ── CAPTIONS ────────────────────────────────────────────────────────── */
.stCaption, [data-testid="stCaptionContainer"] {
    color: var(--muted) !important;
    font-size: 0.82rem !important;
}

/* ── MARKDOWN TEXT ───────────────────────────────────────────────────── */
.stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    color: var(--text) !important;
}

/* ── DIVIDER ─────────────────────────────────────────────────────────── */
hr {
    border-color: var(--divider) !important;
    margin: 1.5rem 0 !important;
}

/* ── SPINNER ─────────────────────────────────────────────────────────── */
.stSpinner > div {
    border-top-color: var(--accent) !important;
}

/* ── CUSTOM COMPONENTS ───────────────────────────────────────────────── */
.hero {
    text-align: center;
    padding: 2rem 0 1.5rem;
}

.hero-title {
    font-family: var(--font-head) !important;
    font-weight: 800;
    font-size: clamp(2rem, 5vw, 3.2rem);
    background: linear-gradient(135deg, var(--text), var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.15;
    margin-bottom: 0.5rem;
}

.hero-sub {
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-size: 0.85rem;
    font-weight: 500;
}

/* Result grid cards */
.result-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}

.result-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.2rem 1rem;
    text-align: center;
    box-shadow: 0 2px 8px var(--shadow);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.result-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px var(--shadow);
}

.result-value {
    font-family: var(--font-head);
    font-size: 1.8rem;
    font-weight: 800;
    line-height: 1.2;
    margin-bottom: 0.25rem;
}

.result-label {
    font-size: 0.75rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600;
}

/* Verdict boxes */
.verdict {
    padding: 1.2rem 1.4rem;
    border-radius: 12px;
    margin: 1rem 0;
    border-left-width: 4px;
    border-left-style: solid;
}

.verdict.safe {
    background: var(--verdict-safe-bg);
    border-color: var(--verdict-safe-border);
}

.verdict.suspicious {
    background: var(--verdict-warn-bg);
    border-color: var(--verdict-warn-border);
}

.verdict.high-risk {
    background: var(--verdict-danger-bg);
    border-color: var(--verdict-danger-border);
}

.verdict strong { color: var(--text) !important; }
.verdict p, .verdict span { color: var(--text-soft) !important; }

/* Highlight box */
.highlight-box {
    background: var(--highlight-bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    font-family: 'DM Mono', 'Fira Code', monospace;
    font-size: 0.92rem;
    line-height: 1.85;
    color: var(--text-soft);
    word-break: break-word;
}

/* Keyword highlight spans */
.kw-highlight {
    background: var(--kw-bg);
    color: var(--kw-color) !important;
    border-radius: 4px;
    padding: 1px 7px;
    font-weight: 700;
    border-bottom: 2px solid color-mix(in srgb, var(--kw-color) 50%, transparent);
}

/* Signal severity badges */
.signal-high { color: var(--severity-high) !important; font-weight: 700; }
.signal-medium { color: var(--severity-medium) !important; font-weight: 700; }
.signal-low { color: var(--severity-low) !important; font-weight: 700; }

/* Footer */
.footer {
    text-align: center;
    color: var(--muted);
    font-size: 0.8rem;
    padding: 2rem 0 1rem;
    border-top: 1px solid var(--divider);
    margin-top: 2rem;
}

/* Sidebar section headers */
.sidebar-section {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--muted);
    font-weight: 700;
    margin: 1.2rem 0 0.4rem;
}

/* Language flag pill */
.lang-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 0.2rem 0.7rem;
    font-size: 0.82rem;
    color: var(--text-soft);
    margin-bottom: 0.5rem;
}

/* Section headers */
.section-header {
    font-family: var(--font-head);
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text);
    margin: 1.5rem 0 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.section-header::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--divider);
}
</style>
    """, unsafe_allow_html=True)


# ----------------------------------------------------------------------
# UI Components
# ----------------------------------------------------------------------
def render_sidebar(bundle: Optional[ModelBundle]) -> None:
    with st.sidebar:
        # ── Language selector ────────────────────────────────────────
        st.markdown(f'<div class="sidebar-section">{tr("language_select")}</div>', unsafe_allow_html=True)
        lang_names = list(SUPPORTED_LANGUAGES.keys())
        lang_codes = list(SUPPORTED_LANGUAGES.values())
        current_code = st.session_state.get("ui_lang", "en")
        current_idx = lang_codes.index(current_code) if current_code in lang_codes else 0

        selected_lang_name = st.selectbox(
            "Interface Language",
            lang_names,
            index=current_idx,
            key="lang_selector",
            label_visibility="collapsed",
        )
        new_code = SUPPORTED_LANGUAGES[selected_lang_name]
        if new_code != st.session_state.get("ui_lang", "en"):
            st.session_state.ui_lang = new_code
            st.rerun()

        st.markdown("---")

        # ── Test messages ────────────────────────────────────────────
        st.markdown(f'<div class="sidebar-section">{tr("test_messages")}</div>', unsafe_allow_html=True)
        sample_options = ["", "UPI Fraud", "Job Scam", "Lottery Scam", "Phishing", "Courier Scam", "Safe Message"]
        sample_key = "sample_dropdown"

        if st.session_state.get("reset_sample_dropdown", False):
            st.session_state[sample_key] = ""
            st.session_state.reset_sample_dropdown = False

        sample_option = st.selectbox(
            tr("choose_sample"),
            sample_options,
            format_func=lambda x: tr("select_sample") if x == "" else x,
            key=sample_key,
            label_visibility="collapsed",
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

        # ── Voice & Alerts ───────────────────────────────────────────
        st.markdown(f'<div class="sidebar-section">{tr("voice_alerts")}</div>', unsafe_allow_html=True)
        st.toggle(tr("enable_voice"), key="voice_enabled", value=True)
        st.toggle(tr("auto_speak"), key="auto_speak", value=True)

        st.markdown("---")

        # ── Model Status ─────────────────────────────────────────────
        st.markdown(f'<div class="sidebar-section">{tr("model_status")}</div>', unsafe_allow_html=True)
        if bundle is None:
            st.warning(tr("heuristic_mode"))
        else:
            st.success(tr("ml_loaded"))
            if bundle.has_type_model:
                st.caption(tr("type_available"))
            else:
                st.caption(tr("type_fallback"))

        st.markdown("---")

        # ── Emergency ────────────────────────────────────────────────
        st.markdown(f'<div class="sidebar-section">{tr("emergency")}</div>', unsafe_allow_html=True)
        st.info(tr("emergency_info"))


def render_hero() -> None:
    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">{tr("title")}</div>
        <div class="hero-sub">{tr("hero_sub")} · {APP_VERSION}</div>
    </div>
    """, unsafe_allow_html=True)


def render_input() -> bool:
    st.markdown(f'<div class="section-header">💬 {tr("input_label")}</div>', unsafe_allow_html=True)

    if st.session_state.get("redact_requested", False):
        st.session_state.input_text = redact_sensitive(st.session_state.get("input_text", ""))
        st.session_state.redact_requested = False
        st.rerun()

    if st.session_state.get("clear_requested", False):
        st.session_state.input_text = ""
        st.session_state.clear_requested = False
        st.rerun()

    # Voice input
    if st.session_state.get("voice_enabled", True):
        try:
            from streamlit_mic_recorder import speech_to_text
            col1, col2 = st.columns([1, 5])
            with col1:
                voice_text = speech_to_text(
                    language="en",
                    start_prompt="🎤 " + tr("speak"),
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
            st.caption(tr("voice_unavail"))

    st.text_area(
        "Message",
        key="input_text",
        height=130,
        placeholder="Paste or type the suspicious message here...",
        max_chars=1000,
        label_visibility="collapsed",
    )

    char_count = len(st.session_state.input_text or "")
    col_cc, _ = st.columns([1, 4])
    with col_cc:
        st.caption(f"{char_count}/1000 {tr('char_count')}")

    col1, col2, col3, col4 = st.columns([2, 1, 1, 4])
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
    ftype_raw = r["ftype"]
    ftype = ftype_raw if ftype_raw != "None" else tr("no_fraud")

    risk_class = {"Safe": "safe", "Suspicious": "suspicious", "High Risk": "high-risk"}[risk]
    prob_color = {"Safe": "var(--safe)", "Suspicious": "var(--warn)", "High Risk": "var(--danger)"}[risk]

    action_map = {
        "Safe": tr("no_action"),
        "Suspicious": tr("be_cautious"),
        "High Risk": tr("report_now"),
    }

    st.markdown("---")
    st.markdown(f'<div class="section-header">📊 {tr("analysis_results")}</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="result-grid">
        <div class="result-card">
            <div class="result-value" style="color:{prob_color}">{prob:.1f}%</div>
            <div class="result-label">{tr("scam_prob")}</div>
        </div>
        <div class="result-card">
            <div class="result-value" style="color:{prob_color}">{risk}</div>
            <div class="result-label">{tr("risk_level")}</div>
        </div>
        <div class="result-card">
            <div class="result-value" style="color:var(--accent2);font-size:1.3rem;">{ftype}</div>
            <div class="result-label">{tr("fraud_type")}</div>
        </div>
        <div class="result-card">
            <div class="result-value" style="color:{prob_color};font-size:1.3rem;">{action_map[risk]}</div>
            <div class="result-label">{tr("rec_action")}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Verdict messages
    if risk == "Safe":
        verdict_title = tr("safe_msg_title")
        verdict_body = tr("safe_msg_body")
    elif risk == "Suspicious":
        verdict_title = tr("susp_msg_title")
        verdict_body = tr("susp_msg_body")
    else:
        verdict_title = tr("high_msg_title")
        verdict_body = f"This is highly likely a <strong>{ftype}</strong>. Do not respond/call back/click links. Report to 1930."

    st.markdown(f"""
    <div class="verdict {risk_class}">
        <strong style="font-size:1.15rem;">{verdict_title}</strong>
        <p style="margin:0.4rem 0 0;">{verdict_body}</p>
    </div>
    """, unsafe_allow_html=True)

    # Show original if translated
    if r.get("original_text") and r["original_text"] != r["raw"]:
        with st.expander(tr("original_msg")):
            st.write(r["original_text"])

    # Auto-speak
    if st.session_state.get("auto_speak", True):
        hash_key = hashlib.md5(f"{risk}_{ftype_raw}_{prob:.0f}".encode()).hexdigest()
        if st.session_state.get("spoken_hash") != hash_key:
            st.session_state.spoken_hash = hash_key
            if risk == "High Risk":
                speak_text = f"High risk scam detected. Fraud type: {ftype_raw}. Do not respond."
            elif risk == "Suspicious":
                speak_text = f"Suspicious message. Possible {ftype_raw}. Be cautious."
            else:
                speak_text = "Message appears safe. Stay vigilant."
            speak(speak_text)

    if st.button(f"🔊 {tr('speak')}", use_container_width=False):
        speak(f"Risk: {risk}. Type: {ftype_raw}.")

    # Pattern analysis
    with st.expander(f"🔍 {tr('pattern_title')}", expanded=True):
        st.markdown(f'<div class="highlight-box">{r["highlighted"]}</div>', unsafe_allow_html=True)

    # Why flagged
    with st.expander(f"💡 {tr('why_title')}", expanded=True):
        if r.get("signals"):
            st.caption(tr("logic_caption"))
            for s in r["signals"]:
                sev = s["severity"]
                sev_class = f"signal-{sev}"
                st.markdown(
                    f'<span class="{sev_class}">▲ {sev.upper()}</span> — '
                    f'**{s["label"]}**: {s["evidence"]}',
                    unsafe_allow_html=True
                )
        else:
            st.caption(tr("logic_none"))

    # Tips
    with st.expander(f"🛡️ {tr('tips_title')}"):
        for tip in r["tips"]:
            st.markdown(f"- {tip}")

    # Resources
    with st.expander(f"📞 {tr('resources_title')}"):
        st.markdown("""
        - **1930** — National Cyber Helpline (India)
        - [cybercrime.gov.in](https://www.cybercrime.gov.in) — online reporting
        - **112 / 100** — emergency / local police
        """)

    # Share
    st.markdown(f'<div class="section-header">📤 {tr("share")}</div>', unsafe_allow_html=True)
    share_text = (
        f"{tr('fraud_alert')}\n"
        f"Risk: {risk} ({prob:.0f}%)\n"
        f"Type: {ftype}\n"
        f"Report: 1930 | cybercrime.gov.in"
    )
    encoded = quote(share_text)

    cols = st.columns(4)
    with cols[0]:
        st.link_button(f"📧 {tr('share_email')}", f"mailto:?subject={quote(tr('fraud_alert'))}&body={encoded}", use_container_width=True)
    with cols[1]:
        st.link_button(f"💬 {tr('share_whatsapp')}", f"https://wa.me/?text={encoded}", use_container_width=True)
    with cols[2]:
        st.link_button(f"🐦 {tr('share_x')}", f"https://twitter.com/intent/tweet?text={encoded[:240]}", use_container_width=True)
    with cols[3]:
        st.download_button(f"📥 {tr('share_download')}", share_text, file_name="fraud-alert.txt", use_container_width=True)


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
    st.markdown(f"""
    <div class="footer">
        {tr("footer")}
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
        "ui_lang": "en",
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
                # Auto-detect non-English and translate silently
                try:
                    from googletrans import Translator
                    _t = Translator()
                    detected = _t.detect(raw)
                    if detected and detected.lang and detected.lang != "en":
                        with st.spinner(tr("translating")):
                            result = _t.translate(raw, dest="en")
                            translated = result.text
                except Exception:
                    pass  # Silently fall back to original text
                with st.spinner(tr("analyzing")):
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
