# Setup Instructions

## 1. Install Dependencies
```bash
pip install -r requirements.txt
```

## 2. Configure Environment Variables
Copy the example file and edit with your credentials:
```bash
copy .env.example .env
```

Edit `.env` file with your actual credentials:
- Replace `your_password_here` with actual email passwords
- Replace `your_api_key_here` with WhatsApp API key
- Replace `your_token_here` with WhatsApp token
- Replace `your_group_id_here` with WhatsApp group ID
- Update phone numbers in AUTHORIZED_USERS

## 3. Security Notes
- The old `config.json` file is now ignored for security
- Never commit `.env` file to version control
- All sensitive data is now in environment variables

## 4. Run the Applications
Start the email processor:
```bash
python email_processor.py
```

Start the WhatsApp bot (in another terminal):
```bash
python bot.py
```

## 5. Test
Send "1" via WhatsApp to get email summary report.