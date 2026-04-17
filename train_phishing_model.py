# -*- coding: utf-8 -*-
"""
سكربت تدريب نموذج كشف التصيد على ملف CSV.
الاستخدام:
  python train_phishing_model.py
  python train_phishing_model.py path/to/Phishing_validation_emails.csv
"""
import os
import sys

# جذر المشروع
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DEFAULT_CSV = os.path.join(BASE_DIR, 'Phishing_validation_emails.csv')


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    if not os.path.isfile(csv_path):
        print(f'File not found: {csv_path}')
        print('Usage: python train_phishing_model.py [path/to/Phishing_validation_emails.csv]')
        sys.exit(1)

    from ai_engine.ml_pipeline import train_and_evaluate

    print('Training on:', csv_path)
    print('...')
    report = train_and_evaluate(csv_path)
    print()
    print('=' * 50)
    print('RESULTS')
    print('=' * 50)
    print('Train size:', report['n_train'])
    print('Test size:', report['n_test'])
    print()
    print('Accuracy:          {:.2%}'.format(report['accuracy']))
    print('F1 (Phishing):     {:.2%}'.format(report['f1_phishing']))
    print('Precision (Phish): {:.2%}'.format(report['precision_phishing']))
    print('Recall (Phish):    {:.2%}'.format(report['recall_phishing']))
    print()
    print('Confusion Matrix (Test):')
    print('  Predicted: Safe  Phishing')
    cm = report['confusion_matrix']
    print('  Actual Safe:   ', cm[0][0], cm[0][1])
    print('  Actual Phish:  ', cm[1][0], cm[1][1])
    print()
    print('Classification Report:')
    print(report['classification_report'])
    print()
    print('Model saved to: ai_engine/saved_models/')
    print('The detector will use this model automatically on next run.')


if __name__ == '__main__':
    main()
