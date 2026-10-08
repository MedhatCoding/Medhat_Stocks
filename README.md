# Medhat Stocks AI

تطبيق Streamlit شخصي لتحليل أسهم البورصة المصرية من القائمة الشرعية المرجعية (96 رمزًا).

## التشغيل محليًا
```bash
pip install -r requirements.txt
streamlit run app.py
```

## مفاتيح الخدمة
أضف مفاتيح الخدمات من إعدادات Secrets في Streamlit Cloud، ولا تضعها داخل الكود أو ترفعها إلى GitHub:
- `EODHD_API_KEY` لبيانات الأسعار والتاريخ.
- `OANOR_API_KEY` للأسعار والأخبار البديلة.
- `GEMINI_API_KEY` لشرح التحليل بالذكاء الاصطناعي (اختياري).
- إعدادات Supabase اختيارية لحفظ المحفظة.

## تقرير Telegram
يعمل `.github/workflows/telegram-daily.yml` الساعة 9 صباحًا بتوقيت القاهرة من الأحد إلى الخميس. أضف مفاتيح Telegram ومفاتيح مزودي البيانات إلى GitHub Actions Secrets، ثم اختبر الإرسال من تبويب Actions.

## الاختبارات
يحتوي `.github/workflows/validate.yml` على فحوصات Python الأساسية واختبار تشغيل Streamlit.

الأسعار قد تتأخر أو لا تتوفر من مزود البيانات. عند نقص البيانات، لا ينبغي اعتبار النتيجة توصية مؤكدة أو ضمانًا للأداء المستقبلي.
