import imaplib
import email
from email.header import decode_header
import jdatetime
import requests
from flask import Flask, request, jsonify
import json # <--- کتابخانه json اضافه شد

# --- مرحله ۱: خواندن تنظیمات از فایل config.json ---
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    ACCOUNTS = config['ACCOUNTS']
    API_SETTINGS = config['API_SETTINGS']
    AUTHORIZED_USERS = config['AUTHORIZED_USERS']
    
    API_KEY = API_SETTINGS['API_KEY']
    TOKEN = API_SETTINGS['TOKEN']
    SEND_MESSAGE_ENDPOINT = API_SETTINGS['SEND_MESSAGE_ENDPOINT'].format(API_KEY=API_KEY)

    print("Configuration loaded successfully from config.json")
except FileNotFoundError:
    print("FATAL ERROR: config.json file not found. Please create it.")
    exit()
except KeyError as e:
    print(f"FATAL ERROR: A required key is missing from config.json: {e}")
    exit()

app = Flask(__name__)

# --- مرحله ۲: بقیه کد بدون تغییر باقی می‌ماند ---

def send_whatsapp_reply(recipient_number, message_body):
    """پاسخ را به شخص ارسال می‌کند."""
    headers = {'Authorization': f'Bearer {TOKEN}'}
    params = {"phonenumber": recipient_number, "message": message_body}
    try:
        requests.get(SEND_MESSAGE_ENDPOINT, headers=headers, params=params, timeout=15)
        print(f"Reply sent successfully to {recipient_number}.")
        return True
    except Exception as e:
        print(f"Error sending reply: {e}")
        return False

def get_email_summary_report():
    """ایمیل‌ها را از تمام حساب‌ها واکشی کرده و یک گزارش متنی جامع ایجاد می‌کند."""
    all_emails_data = []
    error_in_accounts = False
    error_message = ""
    for account in ACCOUNTS:
        mail = None
        try:
            mail = imaplib.IMAP4_SSL(account['host'])
            mail.login(account['user'], account['pass'])
            mail.select('inbox', readonly=True)
            status, messages = mail.search(None, 'ALL')
            if status != 'OK' or not messages[0]: continue
            status, data = mail.fetch('1:*', '(FLAGS)')
            if status == 'OK':
                for item in data:
                    if isinstance(item, tuple):
                        flags = item[1].decode()
                        status_text = 'خوانده شده' if '\\Seen' in flags else 'خوانده نشده'
                        all_emails_data.append({'AccountUser': account['user'], 'Status': status_text})
        except Exception as e:
            print(f"Could not process account {account['name']}: {e}")
            error_message = f"❌ خطا در اتصال به حساب ایمیل: *{account['name']}*\nلطفا اطلاعات ورود را در فایل config.json بررسی کنید."
            error_in_accounts = True
            break
        finally:
            if mail: mail.logout()
    if error_in_accounts: return error_message
    if not all_emails_data: return "هیچ ایمیلی در هیچ‌کدام از حساب‌ها یافت نشد."
    report_message = "📊 *گزارش جامع وضعیت ایمیل‌ها*\n"
    total_all, read_all = 0, 0
    for account in ACCOUNTS:
        account_emails = [e for e in all_emails_data if e['AccountUser'] == account['user']]
        total_emails = len(account_emails)
        if total_emails == 0: continue
        read_count = sum(1 for email in account_emails if email['Status'] == 'خوانده شده')
        unread_count = total_emails - read_count
        report_message += (f"\n------------------------------------\n"
                           f"📬 *حساب: {account['name']}*\n"
                           f"▫️ کل: *{total_emails}* | ✅ خوانده شده: *{read_count}* | 📩 خوانده نشده: *{unread_count}*")
        total_all += total_emails
        read_all += read_count
    unread_all = total_all - read_all
    report_message += (f"\n====================\n"
                       f"📈 *مجموع کل:*\n"
                       f"▫️ کل: *{total_all}* | ✅ خوانده شده: *{read_all}* | 📩 خوانده نشده: *{unread_all}*")
    return report_message

@app.route('/whatsapp-webhook', methods=['POST'])
def handle_webhook():
    try:
        data = request.get_json(force=True)
        print("Webhook Received:", data)
        if 'Chat' in data and 'From' in data:
            message_text = data['Chat'].strip()
            sender_id = data['From'].split('@')[0]

            if sender_id in AUTHORIZED_USERS:
                if message_text == '1':
                    print(f"Command '1' received from authorized user {sender_id}. Generating email summary...")
                    summary = get_email_summary_report()
                    send_whatsapp_reply(sender_id, summary)
            else:
                print(f"Message from unauthorized user {sender_id} ignored.")
                
    except Exception as e:
        print(f"An error occurred in webhook handler: {e}")
    return jsonify(success=True), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)