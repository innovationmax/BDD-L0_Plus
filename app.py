from flask import Flask, render_template, request
from flask_socketio import SocketIO
import os
from runner import run_tests

app = Flask(__name__)
# Set async_mode and ping options here
socketio = SocketIO(
    app,
    async_mode='eventlet',
    cors_allowed_origins="*",
    ping_interval=10,  # send ping every 10s
    ping_timeout=30    # timeout after 30s
)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('start')
def handle_start():
    sid = request.sid
    socketio.emit('status', {'msg': 'Tests started'}, to=sid)
    socketio.start_background_task(run_tests, socketio, sid)

if __name__ == '__main__':
    os.makedirs('tests/reports', exist_ok=True)
    host = '127.0.0.1'
    port = 8000
    print(f" * Running on http://localhost:{port}/ (Press CTRL+C to quit)")
    socketio.run(
        app,
        host=host,
        port=port,
        debug=True
    )
