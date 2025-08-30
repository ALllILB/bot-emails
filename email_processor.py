import imaplib
import email
from email.header import decode_header
from email import utils
import pandas as pd
import os
import time
import jdatetime
import requests
import json

# --- (مهم) تنظیمات حساب‌های ایمیل ---
# شما می‌توانید هر تعداد حساب ایمیل که می‌خواهید به این لیست اضافه کنید
ACCOUNTS = [
    {
        "name": "info@mahanholding.co",  # یک نام دلخواه برای این ایمیل
        "host": "mail.mahanholding.co",
        "user": "info@mahanholding.co",
        "pass": "s2FBx3SxLv9svsbrMwY8"
    },
     {
        "name": "admin@mahanholding.co", 
        "host": "mail.mahanholding.co",
        "user": "admin@mahanholding.co",
        "pass": "4DVhw4rDJjrY25kagsTk"
    },
]

# --- تنظیمات فایل خروجی ---
OUTPUT_FILE = 'all_emails_shamsi_date.xlsx'

# --- تنظیمات API واتس‌اپ ---
API_ENDPOINT_URL = 'https://api.whatsiplus.com/sendGroup/iq2d8x7-ai8ihoa-q0jnekb-zhb017u-aq0kiar'
API_KEY = 'iq2d8x7-ai8ihoa-q0jnekb-zhb017u-aq0kiar'
TOKEN = 'vSqHMvaHLnaxrVWo6WFoaKyf'
GROUP_ID = '120363400960768660'


def send_whatsapp_message(message_body):
    """یک پیام متنی به گروه واتس‌اپ با متد GET ارسال می‌کند."""
    headers = {
        'Authorization': f'Bearer {TOKEN}',
    }
    params = {
        "groupId": GROUP_ID,
        "message": message_body
    }
    try:
        print("--- Sending GET request to API (Group Send Method) ---")
        response = requests.get(API_ENDPOINT_URL, headers=headers, params=params, timeout=15)
        print(f"Server Response Status Code: {response.status_code}")
        print(f"Server Response Body: {response.text}")
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ خطا در ارسال پیام: {e}")
        return False

def send_email_notification(email_data):
    """نوتیفیکیشن یک ایمیل خاص را به گروه واتس‌اپ ارسال می‌کند."""
    
    body_text = email_data.get('Body', 'متنی یافت نشد.')
    if len(body_text) > 300:
        body_text = body_text[:300] + "..."

    # *** تغییر: اضافه شدن نام حساب به نوتیفیکیشن ***
    message_body = (
        f"📬 *ایمیل جدید برای [{email_data['AccountName']}]* 📬\n\n"
        f"👤 *از طرف:* {email_data['From']}\n"
        f"📝 *موضوع:* {email_data['Subject']}\n"
        f"------------------------------------\n"
        f"📄 *متن ایمیل:*\n{body_text}"
    )
    return send_whatsapp_message(message_body)


def get_email_body(msg):
    """محتوای اصلی ایمیل را استخراج می‌کند."""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                charset = part.get_content_charset() or 'utf-8'
                return part.get_payload(decode=True).decode(charset, errors='ignore')
    else:
        charset = msg.get_content_charset() or 'utf-8'
        return msg.get_payload(decode=True).decode(charset, errors='ignore')
    return ""

def fetch_and_process_emails():
    """
    *** تغییر: این تابع اکنون تمام حساب‌های تعریف شده در لیست ACCOUNTS را بررسی می‌کند ***
    """
    all_emails_data = []
    
    for account in ACCOUNTS:
        mail = None
        try:
            print(f"\nConnecting to account: {account['name']} ({account['user']})")
            mail = imaplib.IMAP4_SSL(account['host'])
            mail.login(account['user'], account['pass'])
            mail.select('inbox', readonly=True)
            
            status, messages = mail.search(None, 'ALL')
            if status != 'OK':
                continue

            for num in messages[0].split():
                status, data = mail.fetch(num, '(RFC822 FLAGS)')
                if status == 'OK':
                    flags_part = data[0][0] 
                    flags = flags_part.decode().split('FLAGS (')[1].split(')')[0]
                    
                    msg_part = data[0][1]
                    msg = email.message_from_bytes(msg_part)
                    
                    message_id = msg.get('Message-ID')
                    if not message_id: continue

                    status_text = 'خوانده شده' if '\\Seen' in flags else 'خوانده نشده'
                    
                    subject, encoding = decode_header(msg["Subject"])[0]
                    subject = subject.decode(encoding if encoding else "utf-8") if isinstance(subject, bytes) else subject
                    
                    from_, encoding = decode_header(msg.get("From"))[0]
                    from_ = from_.decode(encoding if encoding else "utf-8") if isinstance(from_, bytes) else from_
                    
                    date_str = msg.get("Date")
                    shamsi_date_str = "تاریخ نامعتبر"
                    if date_str:
                        try:
                            gregorian_dt = utils.parsedate_to_datetime(date_str)
                            jalali_dt = jdatetime.datetime.fromgregorian(datetime=gregorian_dt)
                            shamsi_date_str = jalali_dt.strftime('%Y/%m/%d %H:%M:%S')
                        except Exception:
                            shamsi_date_str = date_str
                    
                    body = get_email_body(msg)
                    
                    # *** تغییر: اضافه کردن نام و ایمیل حساب به داده‌ها ***
                    all_emails_data.append({
                        'AccountName': account['name'],
                        'AccountUser': account['user'],
                        'Message-ID': message_id, 'Date': shamsi_date_str, 'From': from_,
                        'Subject': subject, 'Status': status_text, 'Body': body
                    })
        except Exception as e:
            print(f"Error processing account {account['name']}: {e}")
        finally:
            if mail:
                mail.logout()
            
    return all_emails_data


if __name__ == "__main__":
    notified_ids = set()
    if os.path.exists(OUTPUT_FILE):
        try:
            df = pd.read_excel(OUTPUT_FILE)
            notified_ids.update(df['Message-ID'].dropna().tolist())
            print(f"Loaded {len(notified_ids)} previously processed email IDs.")
        except Exception as e:
            print(f"Could not read existing Excel file to load IDs: {e}")

    try:
        while True:
            print("\nStep 1: Fetching and processing all emails from all accounts...")
            all_emails_list = fetch_and_process_emails()

            if all_emails_list:
                # *** تغییر: منطق گزارش‌دهی کاملاً بازنویسی شده است ***
                print("\nStep 2: Generating and sending comprehensive status report...")
                
                report_message = "📊 *گزارش دوره‌ای جامع وضعیت ایمیل‌ها*\n"
                
                # آمار کلی
                total_all_accounts = 0
                read_all_accounts = 0
                
                # محاسبه آمار به تفکیک هر حساب
                for account in ACCOUNTS:
                    # فیلتر کردن ایمیل‌های مربوط به این حساب
                    account_emails = [e for e in all_emails_list if e['AccountUser'] == account['user']]
                    if not account_emails:
                        continue

                    total_emails = len(account_emails)
                    read_count = sum(1 for email in account_emails if email['Status'] == 'خوانده شده')
                    unread_count = total_emails - read_count
                    
                    # اضافه کردن آمار این حساب به گزارش
                    report_message += (
                        f"\n------------------------------------\n"
                        f"📬 *حساب: {account['name']}*\n"
                        f"▫️ کل ایمیل‌ها: *{total_emails}*\n"
                        f"✅ خوانده شده: *{read_count}*\n"
                        f"📩 خوانده نشده: *{unread_count}*"
                    )
                    
                    # اضافه کردن به آمار کلی
                    total_all_accounts += total_emails
                    read_all_accounts += read_count

                # اضافه کردن بخش "مجموع کل" به گزارش
                unread_all_accounts = total_all_accounts - read_all_accounts
                report_message += (
                    f"\n====================\n"
                    f"📈 *مجموع کل (تمام حساب‌ها):*\n"
                    f"▫️ کل ایمیل‌ها: *{total_all_accounts}*\n"
                    f"✅ خوانده شده: *{read_all_accounts}*\n"
                    f"📩 خوانده نشده: *{unread_all_accounts}*"
                )
                
                send_whatsapp_message(report_message)
                time.sleep(2)

                # --- ادامه منطق قبلی برای اطلاع‌رسانی ایمیل‌های جدید ---
                print("\nStep 3: Checking for new unread emails to notify...")
                new_emails_to_notify = []
                for email_item in all_emails_list:
                    if email_item['Status'] == 'خوانده نشده' and email_item['Message-ID'] not in notified_ids:
                        new_emails_to_notify.append(email_item)

                if new_emails_to_notify:
                    print(f"Found {len(new_emails_to_notify)} new unread emails. Sending notifications...")
                    
                    summary_message = f"🔔 *اطلاعیه ایمیل جدید* 🔔\n\nشما *{len(new_emails_to_notify)}* ایمیل جدید در کل حساب‌ها دریافت کرده‌اید:"
                    send_whatsapp_message(summary_message)
                    time.sleep(2)

                    for email_item in new_emails_to_notify:
                        print(f"Sending notification for: '{email_item['Subject']}' from account '{email_item['AccountName']}'")
                        if send_email_notification(email_item):
                            notified_ids.add(email_item['Message-ID'])
                            time.sleep(3)
                else:
                    print("No new unread emails found.")

                # --- ذخیره‌سازی در اکسل ---
                print("\nStep 4: Saving all data to Excel...")
                df = pd.DataFrame(all_emails_list)
                df.drop_duplicates(subset=['Message-ID'], keep='last', inplace=True)
                # اضافه کردن ستون‌های مربوط به حساب به فایل اکسل
                df.to_excel(OUTPUT_FILE, index=False, engine='openpyxl')
                print(f"Saved {len(df)} unique emails to {OUTPUT_FILE}.")

            print("\n--- Waiting for 10 minutes... (Press Ctrl+C to stop) ---\n")
            time.sleep(600)

    except KeyboardInterrupt:
        print("\nScript stopped by user.")