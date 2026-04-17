# -*- coding: utf-8 -*-
"""
منسق الكشف: يستخدم نموذج ML المدرب إن وُجد، وإلا قواعد التحليل.
"""
from ai_engine.rules import analyze_text


def _predict_with_ml(sender_email, subject, body):
    """
    استدعاء نموذج ML إن كان محمّلاً.
    يُرجع dict أو None إذا لم يكن النموذج جاهزاً.
    """
    try:
        from ai_engine.ml_pipeline import load_model, predict_one
        vectorizer, clf = load_model()
        if vectorizer is None or clf is None:
            return None
        full_text = f"{subject or ''}\n{body or ''}"
        pred, proba_phishing = predict_one(full_text, vectorizer, clf)
        risk_score = int(round(proba_phishing * 100))
        if risk_score >= 70:
            risk_level = 'high'
            classification = 'phishing'
        elif risk_score >= 40:
            risk_level = 'medium'
            classification = 'spam'
        else:
            risk_level = 'low'
            classification = 'legitimate'
        if pred == 1:
            classification = 'phishing'
            risk_level = 'high' if risk_score >= 60 else 'medium'
        reasons = f"تصنيف بواسطة نموذج ML (Logistic Regression + TF-IDF). احتمال التصيد: {risk_score}%"
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'classification': classification,
            'reasons': reasons,
            'model_used': 'ml'
        }
    except Exception:
        return None


def analyze_email(sender_email, subject, body):
    """
    تحليل رسالة وإرجاع:
    - risk_score (0-100)
    - risk_level: low | medium | high
    - classification: legitimate | spam | phishing
    - reasons: تفسير مختصر (Explainable AI)
    """
    result = _predict_with_ml(sender_email, subject, body)
    if result is not None:
        return result
    score, risk_level, classification, reasons = analyze_text(subject, body)
    return {
        'risk_score': score,
        'risk_level': risk_level,
        'classification': classification,
        'reasons': reasons,
        'model_used': 'rules'
    }
