from flask import Flask, render_template, request, jsonify
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

def get_scenarios():
    """Parse feature files and return a list of scenarios with summaries."""
    scenarios = []
    features_dir = os.path.join(os.path.dirname(__file__), 'features')
    for fname in os.listdir(features_dir):
        if not fname.endswith('.feature'):
            continue
        path = os.path.join(features_dir, fname)
        with open(path, encoding='utf-8') as f:
            feature_name = None
            feature_desc = ''
            scenario_name = None
            scenario_steps = []
            scenario_desc = ''
            in_scenario = False
            for line in f:
                line = line.rstrip('\n')
                stripped = line.strip()
                if stripped.lower().startswith('feature:'):
                    feature_name = stripped[8:].strip()
                    feature_desc = ''
                    in_scenario = False
                elif feature_name and not in_scenario and stripped and not stripped.lower().startswith('scenario:'):
                    feature_desc += stripped + ' '
                elif stripped.lower().startswith('scenario:'):
                    if scenario_name:
                        scenarios.append({
                            'feature': feature_name or fname,
                            'feature_desc': feature_desc.strip(),
                            'scenario': scenario_name,
                            'scenario_desc': scenario_desc.strip(),
                            'steps': scenario_steps
                        })
                    scenario_name = stripped[9:].strip()
                    scenario_steps = []
                    scenario_desc = ''
                    in_scenario = True
                elif in_scenario:
                    if stripped.startswith('Given') or stripped.startswith('When') or stripped.startswith('Then') or stripped.startswith('And') or stripped.startswith('But'):
                        scenario_steps.append(stripped)
                    elif stripped:
                        scenario_desc += stripped + ' '
            # Add last scenario in file
            if scenario_name:
                scenarios.append({
                    'feature': feature_name or fname,
                    'feature_desc': feature_desc.strip(),
                    'scenario': scenario_name,
                    'scenario_desc': scenario_desc.strip(),
                    'steps': scenario_steps
                })
    return scenarios

@app.route('/scenarios')
def scenarios():
    return jsonify(get_scenarios())
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