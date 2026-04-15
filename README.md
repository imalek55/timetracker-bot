# TimeTracker Bot — دليل التشغيل

## المتطلبات
- حساب Slack مع App مُعد مسبقاً
- Google Sheets مُعد مسبقاً
- حساب على Railway.app (مجاني)

---

## خطوات الرفع على Railway

1. روح على https://railway.app وسجل دخول بحساب GitHub
2. اضغط "New Project" ← "Deploy from GitHub repo"
3. ارفع هذه الملفات على GitHub repo جديد
4. في Railway، اضغط على المشروع ← "Variables" وأضف:

| المتغير | القيمة |
|---|---|
| SLACK_BOT_TOKEN | xoxb-... (من Slack App) |
| SLACK_SIGNING_SECRET | من Slack App ← Basic Information |
| GOOGLE_CREDENTIALS | محتوى ملف الـ JSON كاملاً |
| SHEET_NAME | TimeTracker |

5. بعد الـ Deploy، انسخ الـ URL مثل: `https://timetracker-xxx.railway.app`
6. ارجع لـ Slack App ← Slash Commands وعدّل الـ Request URL لكل أمر:
   - `/start` ← `https://timetracker-xxx.railway.app/slack/events`
   - `/stop`  ← `https://timetracker-xxx.railway.app/slack/events`
   - `/report` ← `https://timetracker-xxx.railway.app/slack/events`

---

## استخدام البوت

| الأمر | الوظيفة |
|---|---|
| `/start اسم-المشروع` | بدء تسجيل الوقت |
| `/stop` | إنهاء المهمة الحالية |
| `/report` | تقرير هذا الأسبوع |
| `/report month` | تقرير هذا الشهر |

---

## ملاحظات
- كل موظف يشوف تقريره الخاص فقط
- البيانات تُحفظ في Google Sheets تحت شيت "Logs"
- الأوامر مرئية للموظف نفسه فقط (ephemeral)
