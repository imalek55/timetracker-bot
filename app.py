import os
import json
from datetime import datetime
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
import gspread
from google.oauth2.service_account import Credentials

# ─── إعداد التطبيق ───────────────────────────────────────────
app = App(token=os.environ["SLACK_BOT_TOKEN"],
          signing_secret=os.environ["SLACK_SIGNING_SECRET"])
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

# ─── إعداد Google Sheets ──────────────────────────────────────
def get_sheet():
    creds_json = json.loads(os.environ["GOOGLE_CREDENTIALS"])
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]    creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open(os.environ["SHEET_NAME"])
    return spreadsheet

# ─── /start ───────────────────────────────────────────────────
@app.command("/start")
def handle_start(ack, respond, command, client):
    ack("⏳ جاري التسجيل...")
    project = command["text"].strip()
    if not project:
        respond("❌ لازم تكتب اسم المشروع. مثال: `/start تطوير-الموقع`")
        return

    user_id = command["user_id"]
    user_info = client.users_info(user=user_id)
    user_name = user_info["user"]["real_name"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sheet = get_sheet()
    logs = sheet.worksheet("Logs")

    # تحقق إذا الموظف عنده مهمة مفتوحة
    all_rows = logs.get_all_records()
    for i, row in enumerate(all_rows):
        if row["employee_id"] == user_id and row["end_time"] == "":
            respond(f"⚠️ عندك مهمة مفتوحة على *{row['project']}*، استخدم `/stop` أولاً.")
            return

    logs.append_row([user_id, user_name, project, now, ""])
    respond(f"✅ سجّلت بدايتك الساعة *{now[-8:-3]}* على *{project}*")

# ─── /stop ────────────────────────────────────────────────────
@app.command("/stop")
def handle_stop(ack, respond, command):
    ack()
    user_id = command["user_id"]
    now = datetime.now()

    sheet = get_sheet()
    logs = sheet.worksheet("Logs")
    all_rows = logs.get_all_records()

    for i, row in enumerate(all_rows):
        if row["employee_id"] == user_id and row["end_time"] == "":
            row_number = i + 2  # +2 لأن الصف الأول عناوين
            start = datetime.strptime(row["start_time"], "%Y-%m-%d %H:%M:%S")
            duration = now - start
            hours = duration.total_seconds() / 3600

            logs.update_cell(row_number, 5, now.strftime("%Y-%m-%d %H:%M:%S"))

            h = int(hours)
            m = int((hours - h) * 60)
            respond(f"✅ أنهيت! اشتغلت *{h}س {m}د* على *{row['project']}*")
            return

    respond("❌ ما عندك مهمة مفتوحة. استخدم `/start اسم-المشروع` لتبدأ.")

# ─── /report ──────────────────────────────────────────────────
@app.command("/report")
def handle_report(ack, respond, command):
    ack()
    user_id = command["user_id"]
    period = command["text"].strip().lower()  # "week" أو "month" أو فراغ

    sheet = get_sheet()
    logs = sheet.worksheet("Logs")
    all_rows = logs.get_all_records()

    now = datetime.now()
    totals = {}

    for row in all_rows:
        if row["employee_id"] != user_id:
            continue
        if not row["end_time"]:
            continue

        start = datetime.strptime(row["start_time"], "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(row["end_time"], "%Y-%m-%d %H:%M:%S")

        # فلتر حسب الفترة
        if period == "month":
            if start.month != now.month or start.year != now.year:
                continue
        else:  # افتراضي: هذا الأسبوع
            week_start = now - __import__('datetime').timedelta(days=now.weekday())
            if start < week_start.replace(hour=0, minute=0, second=0):
                continue

        hours = (end - start).total_seconds() / 3600
        project = row["project"]
        totals[project] = totals.get(project, 0) + hours

    if not totals:
        period_label = "هذا الشهر" if period == "month" else "هذا الأسبوع"
        respond(f"📭 ما في سجلات {period_label}.")
        return

    period_label = "هذا الشهر" if period == "month" else "هذا الأسبوع"
    lines = [f"📊 *تقريرك {period_label}:*\n"]
    total_all = 0
    for project, hours in sorted(totals.items(), key=lambda x: -x[1]):
        h = int(hours)
        m = int((hours - h) * 60)
        lines.append(f"• *{project}*: {h}س {m}د")
        total_all += hours

    h = int(total_all)
    m = int((total_all - h) * 60)
    lines.append(f"\n⏱ *المجموع: {h}س {m}د*")
    respond("\n".join(lines))

# ─── Flask endpoint ───────────────────────────────────────────
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

@flask_app.route("/", methods=["GET"])
def health():
    return "TimeTracker Bot is running! ✅"

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
