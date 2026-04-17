# -*- coding: utf-8 -*-
"""
استخراج ميزات من نص الرسالة لتحسين دقة نموذج ML:
روابط، روابط مختصرة، كلمات مفتاحية، لغة استعجالية، إلخ.
"""
import re
import numpy as np

# كلمات مفتاحية مشبوهة (للميزات الرقمية)
SUSPICIOUS_KEYWORDS = [
    'urgent', 'verify', 'password', 'account', 'suspended', 'click', 'winner', 'prize',
    'bank', 'transfer', 'confirm', 'security', 'login', 'reset', 'unusual', 'paypal',
    'visa', 'mastercard', 'card', 'cvv', 'otp', 'link', 'update', 'activate', 'expire',
    'عاجل', 'تحقق', 'كلمة المرور', 'حسابك', 'موقوف', 'اضغط', 'فائز', 'جائزة',
    'بنك', 'تحويل', 'تأكيد', 'تسجيل دخول', 'إعادة تعيين', 'غير عادي'
]

SHORT_DOMAINS = ['bit.ly', 'tinyurl', 't.co', 'goo.gl', 'ow.ly', 'is.gd']
URGENCY_WORDS = ['urgent', 'immediately', 'asap', 'عاجل', 'فوري', 'الآن', 'فوراً', 'مطلوب فوراً']


def extract_features(text):
    """
    يستخرج من النص ميزات رقمية تُضاف لنموذج ML.
    يُرجع مصفوفة واحدة (array) بنفس الترتيب دائماً.
    """
    if not text or not isinstance(text, str):
        text = ''
    text_lower = text.lower().strip()

    # عدد الروابط
    links = re.findall(r'https?://[^\s<>"\']+', text_lower)
    link_count = min(len(links), 10)  # حد أقصى 10

    # وجود روابط مختصرة
    short_url_count = sum(1 for d in SHORT_DOMAINS if d in text_lower)
    has_short_url = 1 if short_url_count > 0 else 0

    # عدد الكلمات المفتاحية المشبوهة
    kw_count = sum(1 for kw in SUSPICIOUS_KEYWORDS if kw in text_lower)
    kw_count = min(kw_count, 15)

    # لغة استعجالية
    urgency_count = sum(1 for u in URGENCY_WORDS if u in text_lower)
    has_urgency = 1 if urgency_count > 0 else 0

    # طول النص (طبيعي)
    text_len = len(text)
    text_len_norm = min(text_len / 500.0, 5.0)  # حد أقصى 5

    # وجود كلمات مثل "click here", "claim", "reset password"
    high_risk_phrases = ['click here', 'claim your', 'reset your password', 'verify your', 'update your', 'account has been compromised', 'unusual activity']
    high_risk_count = sum(1 for p in high_risk_phrases if p in text_lower)
    high_risk_count = min(high_risk_count, 5)

    return np.array([
        link_count,
        has_short_url,
        kw_count,
        has_urgency,
        text_len_norm,
        high_risk_count
    ], dtype=np.float64)


def get_feature_names():
    """أسماء الميزات بالترتيب (للتفسير أو التصدير)."""
    return [
        'link_count',
        'has_short_url',
        'suspicious_keyword_count',
        'has_urgency',
        'text_length_norm',
        'high_risk_phrase_count'
    ]
