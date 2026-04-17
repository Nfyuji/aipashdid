# قواعد كشف التصيد الاحتيالي
import re

# كلمات مفتاحية مشبوهة (عربي + إنجليزي)
SUSPICIOUS_KEYWORDS = [
    'urgent', 'عاجل', 'فوري', 'فوراً', 'مطلوب', 'required', 'verify', 'تحقق', 'تأكيد',
    'password', 'كلمة المرور', 'account', 'حسابك', 'suspended', 'موقوف', 'click', 'اضغط',
    'winner', 'فائز', 'جائزة', 'prize', 'bank', 'بنك', 'transfer', 'تحويل', 'wire',
    'أرسل', 'send', 'الآن', 'now', 'limited', 'محدود', 'expire', 'ينتهي', 'confirm',
    'أمن', 'security', 'تسجيل دخول', 'login', 'reset', 'إعادة تعيين', 'unusual', 'غير عادي',
    'paypal', 'فيزا', 'visa', 'mastercard', 'بطاقة', 'card', 'cvv', 'otp', 'رمز',
    'رابط', 'link', 'فتح', 'open', 'تحديث', 'update', 'تفعيل', 'activate'
]

# أنماط روابط مشبوهة
LINK_PATTERNS = [
    r'https?://[^\s]+',  # أي رابط
    r'bit\.ly/\w+',
    r'tinyurl\.com/\w+',
    r'\[?رابط\]?.*https?://',
]

# نطاقات شائعة للتصيد (جزء من النطاق)
PHISH_DOMAINS_HINTS = ['paypal', 'apple', 'microsoft', 'amazon', 'bank', 'secure', 'login', 'account', 'verify']


def check_keywords(text):
    """عدد الكلمات المشبوهة في النص"""
    if not text:
        return 0
    text_lower = text.lower().strip()
    count = 0
    for kw in SUSPICIOUS_KEYWORDS:
        if kw.lower() in text_lower:
            count += 1
    return count


def check_links(text):
    """عدد الروابط في النص"""
    if not text:
        return 0
    return len(re.findall(r'https?://[^\s<>"\']+', text))


def check_urgency(text):
    """هل النص يحوي لغة استعجالية"""
    urgency = ['عاجل', 'فوري', 'الآن', 'urgent', 'immediately', 'asap', 'فوراً', 'مطلوب فوراً']
    text_lower = (text or '').lower()
    return sum(1 for u in urgency if u in text_lower)


def check_shortened_urls(text):
    """كشف روابط مختصرة (مشبوهة غالباً في التصيد)"""
    if not text:
        return 0
    text_lower = text.lower()
    count = 0
    for pattern in ['bit.ly', 'tinyurl', 't.co', 'goo.gl', 'ow.ly', 'is.gd']:
        if pattern in text_lower:
            count += len(re.findall(re.escape(pattern), text_lower))
    return min(count, 5)  # حد أقصى لتأثير النقاط


def check_phish_domain_in_links(text):
    """هل توجد روابط تحوي نطاقات تشبه جهات معروفة (PayPal, بنك، إلخ)"""
    if not text:
        return False
    urls = re.findall(r'https?://[^\s<>"\']+', text)
    text_lower = (text or '').lower()
    for hint in PHISH_DOMAINS_HINTS:
        for url in urls:
            if hint in url.lower() and ('paypal' in url.lower() or 'bank' in url.lower() or 'secure' in url.lower() or 'login' in url.lower() or 'account' in url.lower() or 'verify' in url.lower()):
                return True
    return False


def analyze_text(subject, body):
    """
    تحليل النص وإرجاع:
    - نقاط_الخطر 0-100
    - risk_level: low | medium | high
    - classification: legitimate | spam | phishing  (تصنيف موحّد للمخرجات)
    - reasons: تفسير مختصر (Explainable AI)
    """
    reasons = []
    score = 0
    full_text = f"{subject or ''} {body or ''}"

    kw_count = check_keywords(full_text)
    if kw_count > 0:
        score += min(kw_count * 8, 40)
        reasons.append(f"كلمات مفتاحية مشبوهة ({kw_count})")

    link_count = check_links(full_text)
    if link_count > 0:
        score += min(link_count * 15, 35)
        reasons.append(f"روابط في الرسالة ({link_count})")

    short_urls = check_shortened_urls(full_text)
    if short_urls > 0:
        score += min(short_urls * 5, 20)
        reasons.append(f"روابط مختصرة مشبوهة ({short_urls})")

    if check_phish_domain_in_links(full_text):
        score += 25
        reasons.append("رابط يشبه نطاقاً معروفاً (بنك/دفع/تحقق)")

    if check_urgency(full_text) > 0:
        score += 15
        reasons.append("لغة استعجالية")

    if len(full_text) > 500 and kw_count >= 2:
        score += 10
        reasons.append("نص طويل مع مؤشرات مشبوهة")

    score = min(100, score)

    if score >= 70:
        risk_level = 'high'
        classification = 'phishing'
    elif score >= 40:
        risk_level = 'medium'
        classification = 'spam'
    else:
        risk_level = 'low'
        classification = 'legitimate'

    reason_text = ' | '.join(reasons) if reasons else 'لا توجد مؤشرات خطيرة'
    return score, risk_level, classification, reason_text
