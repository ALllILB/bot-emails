import os
import logging
from datetime import datetime
from flask import Flask, render_template_string
from logging.handlers import RotatingFileHandler

# Configure logging to file
log_file = 'bot_logs.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Email Bot Logs</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Courier New', monospace; margin: 20px; background: #1a1a1a; color: #00ff00; }
        .header { text-align: center; margin-bottom: 30px; }
        .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .running { background: #004400; border: 1px solid #00ff00; }
        .error { background: #440000; border: 1px solid #ff0000; color: #ff6666; }
        .info { background: #004444; border: 1px solid #00ffff; color: #66ffff; }
        .warning { background: #444400; border: 1px solid #ffff00; color: #ffff66; }
        .log-container { background: #000; padding: 20px; border-radius: 10px; border: 1px solid #333; }
        .log-line { margin: 2px 0; padding: 5px; border-radius: 3px; }
        .timestamp { color: #888; }
        .level-INFO { color: #00ff00; }
        .level-ERROR { color: #ff6666; }
        .level-WARNING { color: #ffff66; }
        .refresh-btn { background: #333; color: #00ff00; border: 1px solid #00ff00; padding: 10px 20px; cursor: pointer; }
        .refresh-btn:hover { background: #00ff00; color: #000; }
    </style>
    <script>
        function autoRefresh() {
            setTimeout(function(){ location.reload(); }, 30000);
        }
        window.onload = autoRefresh;
    </script>
</head>
<body>
    <div class="header">
        <h1>📧 Email Bot Monitor</h1>
        <p>Last Updated: {{ current_time }}</p>
        <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
    </div>
    
    <div class="status running">
        <strong>🟢 Bot Status:</strong> Active | 
        <strong>📊 Log Lines:</strong> {{ log_count }} | 
        <strong>📁 Log File:</strong> {{ log_file }}
    </div>
    
    <div class="log-container">
        <h3>📋 Recent Logs (Last 100 lines)</h3>
        {% for line in logs %}
        <div class="log-line {{ line.level_class }}">
            <span class="timestamp">{{ line.timestamp }}</span> - 
            <strong>{{ line.level }}</strong> - 
            {{ line.message }}
        </div>
        {% endfor %}
    </div>
</body>
</html>
'''

def parse_log_line(line):
    """Parse log line and extract components."""
    try:
        parts = line.strip().split(' - ', 3)
        if len(parts) >= 4:
            return {
                'timestamp': parts[0],
                'logger': parts[1],
                'level': parts[2],
                'message': parts[3],
                'level_class': f'level-{parts[2]}'
            }
    except:
        pass
    return {
        'timestamp': '',
        'logger': '',
        'level': 'INFO',
        'message': line.strip(),
        'level_class': 'level-INFO'
    }

@app.route('/')
def show_logs():
    """Display bot logs in a beautiful web interface."""
    logs = []
    log_count = 0
    
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                log_count = len(lines)
                # Get last 100 lines
                recent_lines = lines[-100:] if len(lines) > 100 else lines
                logs = [parse_log_line(line) for line in reversed(recent_lines)]
        except Exception as e:
            logs = [{'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                    'logger': 'log_viewer', 'level': 'ERROR', 
                    'message': f'Error reading log file: {e}', 'level_class': 'level-ERROR'}]
    
    return render_template_string(HTML_TEMPLATE, 
                                logs=logs, 
                                log_count=log_count,
                                log_file=log_file,
                                current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8223, debug=False)