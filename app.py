from flask import Flask, render_template, request
from flask_socketio import SocketIO
import os
from runner import run_tests

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('start')
def handle_start():
    sid = request.sid
    socketio.emit('status', {'msg': 'Tests started'}, to=sid)
    # Use socketio.start_background_task to run without blocking
    socketio.start_background_task(run_tests, socketio, sid)

if __name__ == '__main__':
    # ensure reports directory exists
    os.makedirs('tests/reports', exist_ok=True)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
