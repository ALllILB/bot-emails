# Email Monitoring Bot

A secure email monitoring system that sends WhatsApp notifications for new emails.

## Security Setup

1. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Configure your credentials in `.env`:**
   - Email account credentials
   - WhatsApp API keys
   - Authorized user phone numbers

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Start the WhatsApp Bot:
```bash
python bot.py
```

### Start the Email Monitor:
```bash
python email_processor.py
```

## Commands

Send "1" via WhatsApp to get email summary report.

## Security Features

- ✅ Environment-based configuration
- ✅ Proper logging with levels
- ✅ Input validation and error handling
- ✅ No hardcoded credentials
- ✅ Debug mode disabled by default
- ✅ Authorized users only

## Important Notes

- Never commit `.env` file to version control
- The old `config.json` is now ignored for security
- All credentials must be in environment variables