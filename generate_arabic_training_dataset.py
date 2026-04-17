#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
إنشاء مجموعة بيانات عربية للتصيد (Phishing) مقابل رسائل سليمة.
ينتج CSV بصيغة:
Email Text,Email Type
"""
import csv
import random
from pathlib import Path

OUT_PATH = Path(__file__).resolve().parent / "Phishing_validation_emails.csv"
TOTAL_PER_CLASS = 1400  # 2800 سجل إجمالي
SEED = 42


SAFE_SUBJECTS = [
    "تذكير باجتماع الفريق",
    "جدول محاضرات الاسبوع القادم",
    "تحديث على مشروع التخرج",
    "محضر اجتماع القسم",
    "دعوه لحضور ورشه عمل",
    "مراجعه التقرير الشهري",
    "متابعه طلب الاجازه",
    "جدوله مقابله داخليه",
    "اشعار باستلام المهمه",
    "تنبيه صيانة نظام البريد الداخلي",
]

SAFE_BODIES = [
    "نود تذكيركم بان الاجتماع سيكون غدا الساعه {time} في قاعه {room}. يرجى الاطلاع على جدول الاعمال المرفق.",
    "تم تحديث الخطة التنفيذية للمشروع، الرجاء مراجعة النسخة على بوابة الشركة الداخلية قبل نهاية الدوام.",
    "يرجى اعتماد التقرير بعد مراجعة الملاحظات. في حال وجود استفسار يمكن التواصل مع فريق الجودة.",
    "تمت الموافقه على الطلب رقم {id}. يمكنكم المتابعة عبر النظام الداخلي دون الحاجة لاي بيانات اضافية.",
    "نرفق لكم محضر الاجتماع السابق، ونأمل ارسال الملاحظات خلال يومي عمل.",
    "تمت اضافة مهام جديدة في لوحة المشروع. الرجاء تحديث حالة المهام المكلف بها.",
    "سيتم تنفيذ صيانة دورية يوم {day} من الساعه {time} ولمدة ساعتين. قد يتوقف النظام بشكل جزئي.",
]

PHISH_SUBJECTS = [
    "تحذير: سيتم ايقاف حسابك خلال 24 ساعه",
    "اشعار امني عاجل: تحقق من هويتك الان",
    "تم رصد نشاط غير معتاد على بريدك",
    "تنبيه فوري: تحديث بيانات الدفع مطلوب",
    "رساله من البنك: يرجى تاكيد بياناتك",
    "اشعار: استرجاع حسابك قبل الحظر النهائي",
    "عاجل جدا: لديك تحويل معلق",
]

PHISH_BODIES = [
    "عزيزي المستخدم، تم اكتشاف محاولة دخول غير مصرح بها. يرجى تسجيل الدخول فورا عبر الرابط {url} لتأكيد الحساب.",
    "سيتم تعليق بريدك الالكتروني اذا لم تقم بتحديث كلمة المرور الآن من خلال {url}.",
    "لديك شحنة معلقة، ادخل بياناتك الشخصية ورقم الهوية عبر الرابط {url} خلال ساعتين.",
    "تم ايقاف خدمة الحساب مؤقتا. لاعادة التفعيل، قم بتسجيل الدخول عبر {url} وادخل رمز التحقق المرسل.",
    "يرجى تأكيد بيانات البطاقة البنكية لتجنب الغرامة. استخدم الرابط التالي {url} بشكل عاجل.",
    "لقد ربحت مكافأة مالية بقيمة {amount} ريال. لاستلام الجائزة ادخل معلوماتك البنكية عبر {url}.",
    "هذه اخر محاولة قبل الاغلاق النهائي. قم بالتحقق الان عبر {url}.",
]

URLS = [
    "http://bit.ly/verify-secure",
    "http://tinyurl.com/bank-check",
    "http://secure-login-pay.com/confirm",
    "http://account-update-now.net/login",
    "http://verify-wallet-fast.org/identity",
]


def build_safe(i: int) -> str:
    subject = random.choice(SAFE_SUBJECTS)
    body = random.choice(SAFE_BODIES).format(
        time=random.choice(["08:00", "09:30", "10:00", "13:00", "15:30"]),
        room=random.choice(["A12", "B07", "C03", "قاعة التدريب", "القاعة الكبرى"]),
        id=f"REQ-{1000 + i}",
        day=random.choice(["الاحد", "الاثنين", "الثلاثاء", "الاربعاء", "الخميس"]),
    )
    return f"{subject}. {body}"


def build_phishing(i: int) -> str:
    subject = random.choice(PHISH_SUBJECTS)
    body = random.choice(PHISH_BODIES).format(
        url=random.choice(URLS),
        amount=random.choice(["500", "900", "1500", "3000", "5000"]),
    )
    urgency = random.choice(
        [
            "الرجاء التنفيذ فورا.",
            "لا تتجاهل هذا التنبيه.",
            "مهلة التحقق تنتهي اليوم.",
            "سيتم الحظر اذا لم تستجب الان.",
        ]
    )
    return f"{subject}. {body} {urgency}"


def main() -> None:
    random.seed(SEED)
    rows = []

    for i in range(TOTAL_PER_CLASS):
        rows.append((build_safe(i), "Safe Email"))
    for i in range(TOTAL_PER_CLASS):
        rows.append((build_phishing(i), "Phishing Email"))

    random.shuffle(rows)

    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Email Text", "Email Type"])
        writer.writerows(rows)

    print(f"Generated {len(rows)} rows at: {OUT_PATH}")


if __name__ == "__main__":
    main()

