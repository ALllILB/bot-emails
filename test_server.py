from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return "سرور تست من کار میکند!"

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(
        host='0.0.0.0',
        port=8223,
        debug=debug_mode
    )