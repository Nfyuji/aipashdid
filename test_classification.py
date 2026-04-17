# -*- coding: utf-8 -*-
"""
اختبار التصنيف: تشغيل من سطر الأوامر لمشاهدة هل النظام يصنّف الرسائل بشكل صحيح.
الاستخدام: python test_classification.py
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ai_engine.detector import analyze_email
from ai_engine.ml_pipeline import is_ml_loaded

def main():
    print("=" * 60)
    print("اختبار تصنيف الرسائل (PhishDetector)")
    print("=" * 60)
    if is_ml_loaded():
        print("النموذج المستخدم: ML (Random Forest + TF-IDF)")
    else:
        print("النموذج المستخدم: قواعد التحليل (لم يُحمّل نموذج ML)")
    print()

    # رسائل اختبار: واحدة آمنة وواحدة تصيد
    tests = [
        ("Safe", "noreply@company.com", "Meeting reminder", 
         "Hi John, our meeting is scheduled for tomorrow at 10 AM. Please be prepared with your updates."),
        ("Phishing", "security@bank-fake.com", "Urgent: Verify your account",
         "Alert: Unusual login attempt detected. Verify your account by clicking here. Your account has been compromised."),
        ("Phishing", "winner@prize.com", "You won!",
         "Congratulations! You've won a $3000 gift card. Click here to claim your prize."),
        ("Safe", "hr@company.com", "Project update",
         "Hello Alex, here is your weekly update on the project's progress. Please review and provide feedback."),
    ]

    for label, sender, subject, body in tests:
        result = analyze_email(sender, subject, body)
        print(f"[{label}]")
        print(f"  المرسل: {sender}")
        print(f"  الموضوع: {subject[:50]}...")
        print(f"  التصنيف: {result['classification']} | الخطورة: {result['risk_level']} | النقاط: {result['risk_score']}")
        print(f"  التفسير: {result['reasons'][:70]}...")
        print(f"  النموذج: {result.get('model_used', 'rules')}")
        print()

    print("=" * 60)
    print("انتهى الاختبار. إذا التصنيف منطقي (Safe -> legitimate، Phishing -> phishing) فالنظام يعمل.")
    print("=" * 60)

if __name__ == "__main__":
    main()
