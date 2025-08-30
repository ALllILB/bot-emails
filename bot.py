import imaplib
import email
from email.header import decode_header
import jdatetime
import requests
from flask import Flask, request, jsonify
import logging
import logging.handlers
import os
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
AUTHORIZED_USERS = config['AUTHORIZED_USERS']
FLASK_CONFIG = config['FLASK_CONFIG']

API_KEY = API_SETTINGS['API_KEY']
TOKEN = API_SETTINGS['TOKEN']
SEND_MESSAGE_ENDPOINT = API_SETTINGS['SEND_MESSAGE_ENDPOINT']

logger.info("Configuration loaded successfully from environment variables")

app = Flask(__name__)

def send_whatsapp_reply(recipient_number, message_body):
    """پاسخ را به شخص ارسال میکند."""
    headers = {'Authorization': f'Bearer {TOKEN}'}
    params = {"phonenumber": recipient_number, "message": message_body}
    try:
        response = requests.get(SEND_MESSAGE_ENDPOINT, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        logger.info(f"Reply sent successfully to {recipient_number}")
        return True
    except requests.RequestException as e:
        logger.error(f"Error sending reply to {recipient_number}: {e}")
        return False

def get_email_summary_report():
    """ایمیلها را از تمام حسابها واکشی کرده و یک گزارش متنی جامع ایجاد میکند."""
    all_emails_data = []
    
    for account in ACCOUNTS:
        try:
            emails_data = _process_account_emails(account)
            all_emails_data.extend(emails_data)
        except Exception as e:
            logger.error(f"Could not process account {account['name']}: {e}")
            return f"❌ خطا در اتصال به حساب ایمیل: *{account['name']}*\nلطفا اطلاعات ورود را بررسی کنید."
    
    if not all_emails_data:
        return "هیچ ایمیلی در هیچکدام از حسابها یافت نشد."
    
    return _generate_summary_report(all_emails_data)

def _process_account_emails(account):
    """Process emails for a single account."""
    emails_data = []
    mail = None
    try:
        mail = imaplib.IMAP4_SSL(account['host'])
        mail.login(account['user'], account['pass'])
        mail.select('inbox', readonly=True)
        status, messages = mail.search(None, 'ALL')
        
        if status != 'OK' or not messages[0]:
            return emails_data
            
        status, data = mail.fetch('1:*', '(FLAGS)')
        if status == 'OK':
            for item in data:
                if isinstance(item, tuple) and len(item) > 1:
                    try:
                        flags = item[1].decode()
                        status_text = 'خوانده شده' if '\\Seen' in flags else 'خوانده نشده'
                        emails_data.append({'AccountUser': account['user'], 'Status': status_text})
                    except (IndexError, UnicodeDecodeError) as e:
                        logger.warning(f"Error processing email flags: {e}")
                        continue
    finally:
        if mail:
            try:
                mail.logout()
            except:
                pass
    
    return emails_data

def _generate_summary_report(all_emails_data):
    """Generate summary report from email data."""
    report_parts = ["📊 *گزارش جامع وضعیت ایمیلها*\n"]
    total_all, read_all = 0, 0
    
    # Group emails by account for better performance
    emails_by_account = {}
    for email_data in all_emails_data:
        user = email_data['AccountUser']
        if user not in emails_by_account:
            emails_by_account[user] = []
        emails_by_account[user].append(email_data)
    
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
            f"▫️ کل: *{total_emails}* | ✅ خوانده شده: *{read_count}* | 📩 خوانده نشده: *{unread_count}*"
        )
        
        total_all += total_emails
        read_all += read_count
    
    unread_all = total_all - read_all
    report_parts.append(
        f"\n====================\n"
        f"📈 *مجموع کل:*\n"
        f"▫️ کل: *{total_all}* | ✅ خوانده شده: *{read_all}* | 📩 خوانده نشده: *{unread_all}*"
    )
    
    return ''.join(report_parts)

@app.route('/whatsapp-webhook', methods=['POST'])
def handle_webhook():
    try:
        data = request.get_json(force=True)
        logger.info(f"Webhook received from {request.remote_addr}")
        
        if not data or 'Chat' not in data or 'From' not in data:
            logger.warning("Invalid webhook data received")
            return jsonify(error="Invalid data"), 400
            
        message_text = data['Chat'].strip()
        sender_id = data['From'].split('@')[0]

        if sender_id not in AUTHORIZED_USERS:
            logger.warning(f"Unauthorized access attempt from {sender_id}")
            return jsonify(success=True), 200
            
        if message_text == '1':
            logger.info(f"Email summary requested by authorized user {sender_id}")
            summary = get_email_summary_report()
            send_whatsapp_reply(sender_id, summary)
        else:
            logger.info(f"Unknown command '{message_text}' from user {sender_id}")
                
    except KeyError as e:
        logger.error(f"Missing required field in webhook data: {e}")
        return jsonify(error="Missing required field"), 400
    except Exception as e:
        logger.error(f"Unexpected error in webhook handler: {e}")
        return jsonify(error="Internal server error"), 500
        
    return jsonify(success=True), 200

if __name__ == '__main__':
    app.run(
        host=FLASK_CONFIG['HOST'],
        port=FLASK_CONFIG['PORT'],
        debug=FLASK_CONFIG['DEBUG']
    )