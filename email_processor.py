import imaplib
import email
from email.header import decode_header
from email import utils
import pandas as pd
import os
import time
import jdatetime
import requests
import logging
import logging.handlers
from dotenv import load_dotenv
from config_loader import load_config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.handlers.RotatingFileHandler('bot_logs.log', maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load configuration
config = load_config()
ACCOUNTS = config['ACCOUNTS']
API_SETTINGS = config['API_SETTINGS']
OUTPUT_FILE = 'all_emails_shamsi_date.xlsx'

def send_whatsapp_message(message_body):
    """یک پیام متنی به گروه واتساپ ارسال میکند."""
    headers = {'Authorization': f'Bearer {API_SETTINGS["TOKEN"]}'}
    params = {
        "groupId": API_SETTINGS["GROUP_ID"],
        "message": message_body
    }
    try:
        logger.info("Sending message to WhatsApp group")
        response = requests.get(API_SETTINGS["GROUP_ENDPOINT"], headers=headers, params=params, timeout=15)
        response.raise_for_status()
        logger.info("Message sent successfully")
        return True
    except requests.RequestException as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        return False

def send_email_notification(email_data):
    """نوتیفیکیشن یک ایمیل خاص را به گروه واتساپ ارسال میکند."""
    body_text = email_data.get('Body', 'متنی یافت نشد.')
    if len(body_text) > 300:
        body_text = body_text[:300] + "..."

    message_body = (
        f"📬 *ایمیل جدید برای [{email_data['AccountName']}]* 📬\n\n"
        f"👤 *از طرف:* {email_data['From']}\n"
        f"📝 *موضوع:* {email_data['Subject']}\n"
        f"------------------------------------\n"
        f"📄 *متن ایمیل:*\n{body_text}"
    )
    return send_whatsapp_message(message_body)

def get_email_body(msg):
    """محتوای اصلی ایمیل را استخراج میکند."""
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

def process_single_account(account):
    """Process emails for a single account."""
    emails_data = []
    mail = None
    try:
        logger.info(f"Connecting to account: {account['name']} ({account['user']})")
        mail = imaplib.IMAP4_SSL(account['host'])
        mail.login(account['user'], account['pass'])
        mail.select('inbox', readonly=True)
        
        status, messages = mail.search(None, 'ALL')
        if status != 'OK':
            return emails_data

        for num in messages[0].split():
            try:
                status, data = mail.fetch(num, '(RFC822 FLAGS)')
                if status != 'OK':
                    continue
                    
                flags_part = data[0][0]
                if b'FLAGS' in flags_part:
                    flags = flags_part.decode().split('FLAGS (')[1].split(')')[0]
                else:
                    flags = ""
                
                msg_part = data[0][1]
                msg = email.message_from_bytes(msg_part)
                
                message_id = msg.get('Message-ID')
                if not message_id:
                    continue

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
                
                emails_data.append({
                    'AccountName': account['name'],
                    'AccountUser': account['user'],
                    'Message-ID': message_id,
                    'Date': shamsi_date_str,
                    'From': from_,
                    'Subject': subject,
                    'Status': status_text,
                    'Body': body
                })
            except Exception as e:
                logger.warning(f"Error processing individual email: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error processing account {account['name']}: {e}")
    finally:
        if mail:
            try:
                mail.logout()
            except:
                pass
            
    return emails_data

def fetch_and_process_emails():
    """تمام حسابهای تعریف شده را بررسی میکند."""
    all_emails_data = []
    
    for account in ACCOUNTS:
        account_emails = process_single_account(account)
        all_emails_data.extend(account_emails)
    
    return all_emails_data

def generate_status_report(all_emails_list):
    """Generate comprehensive status report."""
    report_parts = ["📊 *گزارش دورهای جامع وضعیت ایمیلها*\n"]
    
    total_all_accounts = 0
    read_all_accounts = 0
    
    # Group emails by account for better performance
    emails_by_account = {}
    for email_item in all_emails_list:
        user = email_item['AccountUser']
        if user not in emails_by_account:
            emails_by_account[user] = []
        emails_by_account[user].append(email_item)
    
    for account in ACCOUNTS:
        account_emails = emails_by_account.get(account['user'], [])
        if not account_emails:
            continue

        total_emails = len(account_emails)
        read_count = sum(1 for email in account_emails if email['Status'] == 'خوانده شده')
        unread_count = total_emails - read_count
        
        report_parts.append(
            f"\n------------------------------------\n"
            f"📬 *حساب: {account['name']}*\n"
            f"▫️ کل ایمیلها: *{total_emails}*\n"
            f"✅ خوانده شده: *{read_count}*\n"
            f"📩 خوانده نشده: *{unread_count}*"
        )
        
        total_all_accounts += total_emails
        read_all_accounts += read_count

    unread_all_accounts = total_all_accounts - read_all_accounts
    report_parts.append(
        f"\n====================\n"
        f"📈 *مجموع کل (تمام حسابها):*\n"
        f"▫️ کل ایمیلها: *{total_all_accounts}*\n"
        f"✅ خوانده شده: *{read_all_accounts}*\n"
        f"📩 خوانده نشده: *{unread_all_accounts}*"
    )
    
    return ''.join(report_parts)

def save_to_excel(all_emails_list):
    """Save email data to Excel file."""
    try:
        df = pd.DataFrame(all_emails_list)
        df.drop_duplicates(subset=['Message-ID'], keep='last', inplace=True)
        df.to_excel(OUTPUT_FILE, index=False, engine='openpyxl')
        logger.info(f"Saved {len(df)} unique emails to {OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"Error saving to Excel: {e}")

if __name__ == "__main__":
    notified_ids = set()
    if os.path.exists(OUTPUT_FILE):
        try:
            df = pd.read_excel(OUTPUT_FILE)
            notified_ids.update(df['Message-ID'].dropna().tolist())
            logger.info(f"Loaded {len(notified_ids)} previously processed email IDs")
        except Exception as e:
            logger.error(f"Could not read existing Excel file: {e}")

    try:
        while True:
            logger.info("Fetching and processing all emails from all accounts")
            all_emails_list = fetch_and_process_emails()

            if all_emails_list:
                logger.info("Generating and sending comprehensive status report")
                report_message = generate_status_report(all_emails_list)
                send_whatsapp_message(report_message)
                time.sleep(2)

                logger.info("Checking for new unread emails to notify")
                new_emails_to_notify = [
                    email_item for email_item in all_emails_list
                    if email_item['Status'] == 'خوانده نشده' and email_item['Message-ID'] not in notified_ids
                ]

                if new_emails_to_notify:
                    logger.info(f"Found {len(new_emails_to_notify)} new unread emails")
                    
                    summary_message = f"🔔 *اطلاعیه ایمیل جدید* 🔔\n\nشما *{len(new_emails_to_notify)}* ایمیل جدید در کل حسابها دریافت کردهاید:"
                    send_whatsapp_message(summary_message)
                    time.sleep(2)

                    for email_item in new_emails_to_notify:
                        logger.info(f"Sending notification for: '{email_item['Subject']}' from account '{email_item['AccountName']}'")
                        if send_email_notification(email_item):
                            notified_ids.add(email_item['Message-ID'])
                            time.sleep(3)
                else:
                    logger.info("No new unread emails found")

                logger.info("Saving all data to Excel")
                save_to_excel(all_emails_list)

            logger.info("Waiting for 10 minutes...")
            time.sleep(600)

    except KeyboardInterrupt:
        logger.info("Script stopped by user")