# -*- coding: utf-8 -*-
"""
خط أنابيب ML لاكتشاف التصيد:
- TF-IDF على النص
- ميزات ذكية (روابط، كلمات مفتاحية، استعجال، إلخ)
- Random Forest مصنّف
"""
import os
import joblib
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, classification_report, confusion_matrix
from scipy import sparse

from ai_engine.feature_extractor import extract_features, get_feature_names

# مجلد حفظ النماذج (داخل ai_engine)
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'saved_models')
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'tfidf.joblib')
MODEL_PATH = os.path.join(MODEL_DIR, 'classifier.joblib')


def _ensure_model_dir():
    os.makedirs(MODEL_DIR, exist_ok=True)


def _clean_text(text):
    if not text or not isinstance(text, str):
        return ''
    text = text.strip()
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    # تطبيع عربي بسيط لتحسين التعميم
    text = re.sub(r'[\u064B-\u0652]', '', text)  # حذف التشكيل
    text = re.sub(r'[إأآا]', 'ا', text)
    text = text.replace('ى', 'ي').replace('ة', 'ه')
    text = re.sub(r'\s+', ' ', text)
    return text


def build_features(X_text, vectorizer=None, fit=False):
    """
    X_text: قائمة نصوص
    يُرجع: مصفوفة مدمجة [TF-IDF | ميزات يدوية]
    """
    if vectorizer is None:
        vectorizer = TfidfVectorizer(
            max_features=15000,
            ngram_range=(1, 3),
            min_df=1,
            max_df=0.97,
            strip_accents='unicode',
            lowercase=True,
            sublinear_tf=True
        )
    if fit:
        X_tfidf = vectorizer.fit_transform(X_text)
    else:
        X_tfidf = vectorizer.transform(X_text)
    # ميزات يدوية
    X_hand = np.row_stack([extract_features(t) for t in X_text])
    return sparse.hstack([X_tfidf, X_hand]), vectorizer


def train_and_evaluate(csv_path, test_size=0.2, random_state=42):
    """
    تدريب على ملف CSV بصيغة: Email Text, Email Type
    Email Type: Safe Email | Phishing Email
    """
    import pandas as pd
    _ensure_model_dir()
    df = pd.read_csv(csv_path, encoding='utf-8')
    if 'Email Text' not in df.columns or 'Email Type' not in df.columns:
        raise ValueError('CSV must have columns: Email Text, Email Type')
    df = df.dropna(subset=['Email Text', 'Email Type'])
    texts = df['Email Text'].astype(str).map(_clean_text).tolist()
    labels = (df['Email Type'].str.strip().str.lower() == 'phishing email').astype(int).values
    # 0 = Safe/Legitimate, 1 = Phishing

    X_text_train, X_text_test, y_train, y_test = train_test_split(
        texts, labels, test_size=test_size, random_state=random_state, stratify=labels
    )

    vectorizer = TfidfVectorizer(
        max_features=15000,
        ngram_range=(1, 3),
        min_df=1,
        max_df=0.97,
        strip_accents='unicode',
        lowercase=True,
        sublinear_tf=True
    )
    X_train, _ = build_features(X_text_train, vectorizer=vectorizer, fit=True)
    X_test, _ = build_features(X_text_test, vectorizer=vectorizer, fit=False)

    # Logistic Regression غالباً أفضل مع TF-IDF للنصوص
    clf = LogisticRegression(
        solver='liblinear',
        C=2.0,
        max_iter=4000,
        class_weight='balanced',
        random_state=random_state,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, pos_label=1)
    prec = precision_score(y_test, y_pred, pos_label=1)
    rec = recall_score(y_test, y_pred, pos_label=1)

    joblib.dump(vectorizer, VECTORIZER_PATH)
    joblib.dump(clf, MODEL_PATH)

    report = {
        'accuracy': acc,
        'f1_phishing': f1,
        'precision_phishing': prec,
        'recall_phishing': rec,
        'classification_report': classification_report(y_test, y_pred, target_names=['Safe', 'Phishing']),
        'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
        'n_train': len(y_train),
        'n_test': len(y_test)
    }
    return report


def load_model():
    """تحميل المُتجه والمصنّف إن وُجدا."""
    if not os.path.isfile(VECTORIZER_PATH) or not os.path.isfile(MODEL_PATH):
        return None, None
    try:
        vectorizer = joblib.load(VECTORIZER_PATH)
        clf = joblib.load(MODEL_PATH)
        return vectorizer, clf
    except Exception:
        return None, None


def predict_one(text, vectorizer, clf):
    """
    تصنيف رسالة واحدة.
    text: النص الكامل (موضوع + جسم)
    يُرجع: (class_int, proba_phishing)
    class_int: 0 = legitimate, 1 = phishing
    """
    text = _clean_text(text)
    X_tfidf = vectorizer.transform([text])
    X_hand = extract_features(text).reshape(1, -1)
    X = sparse.hstack([X_tfidf, X_hand])
    proba = clf.predict_proba(X)[0]
    # index 0 = Safe, 1 = Phishing
    if clf.classes_[0] == 1:
        proba_phishing = proba[0]
    else:
        proba_phishing = proba[1]
    pred = 1 if proba_phishing >= 0.5 else 0
    return pred, float(proba_phishing)


def is_ml_loaded():
    v, c = load_model()
    return v is not None and c is not None
