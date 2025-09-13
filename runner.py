import subprocess
import json
import os
import shlex

def _emit(socketio, sid, event, payload):
    try:
        socketio.emit(event, payload, to=sid)
    except Exception:
        # best-effort emit; socket may have disconnected
        pass

def run_tests(socketio, sid: str):
    """Run Behave tests and stream step-level results + live summary.

    This implementation:
    - runs `behave` producing a JSON report at tests/reports/results.json
    - streams raw console lines (log)
    - after behave finishes, parses the JSON and emits scenario/step/summary events
    """
    out_path = 'tests/reports/results.json'
    # remove previous report if exists
    try:
        if os.path.exists(out_path):
            os.remove(out_path)
    except Exception:
        pass

    cmd = ['behave', '--format', 'progress', '--format', 'json', '--outfile', out_path]
    # Start behave process and stream stdout lines to client
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    except FileNotFoundError:
        _emit(socketio, sid, 'log', {'line': 'ERROR: behave not found. Is it installed in this environment?'})
        _emit(socketio, sid, 'done', {'msg': 'Failed: behave not found'})
        return

    # stream raw output
    if process.stdout:
        for line in process.stdout:
            _emit(socketio, sid, 'log', {'line': line.rstrip()})

    process.wait()

    # If report doesn't exist, notify and finish
    if not os.path.exists(out_path):
        _emit(socketio, sid, 'log', {'line': f'No JSON report found at {out_path}.'})
        _emit(socketio, sid, 'done', {'msg': 'Completed (no report).'})
        return

    # Parse JSON report
    try:
        with open(out_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
    except Exception as e:
        _emit(socketio, sid, 'log', {'line': f'Error reading JSON report: {e}'})
        _emit(socketio, sid, 'done', {'msg': 'Completed (parse error).'})
        return

    summary = {
        'features': {'total': 0, 'passed': 0, 'failed': 0},
        'scenarios': {'total': 0, 'passed': 0, 'failed': 0},
        'steps': {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0}
    }

    for feature in report:
        summary['features']['total'] += 1
        feature_name = feature.get('name', 'Unnamed Feature')
        feature_failed = False

        for element in feature.get('elements', []):
            if element.get('type') != 'scenario':
                continue

            summary['scenarios']['total'] += 1
            scenario_name = element.get('name', 'Unnamed Scenario')
            scenario_status = 'passed'

            # emit scenario started
            _emit(socketio, sid, 'scenario', {
                'feature': feature_name,
                'scenario': scenario_name,
                'status': 'running'
            })

            for step in element.get('steps', []):
                summary['steps']['total'] += 1
                step_name = f"{step.get('keyword','')} {step.get('name','')}".strip()
                result = step.get('result', {}) or {}
                status = result.get('status', 'unknown')
                duration = result.get('duration', 0) or 0

                if status == 'passed':
                    summary['steps']['passed'] += 1
                elif status == 'failed':
                    summary['steps']['failed'] += 1
                    scenario_status = 'failed'
                    feature_failed = True
                elif status == 'skipped':
                    summary['steps']['skipped'] += 1

                _emit(socketio, sid, 'step', {
                    'feature': feature_name,
                    'scenario': scenario_name,
                    'step': step_name,
                    'status': status,
                    'duration': f"{duration:.2f}s"
                })

                # emit updated summary after each step
                _emit(socketio, sid, 'summary', summary)

            # finalize scenario
            summary['scenarios'][scenario_status] += 1
            _emit(socketio, sid, 'scenario', {
                'feature': feature_name,
                'scenario': scenario_name,
                'status': scenario_status
            })

        if feature_failed:
            summary['features']['failed'] += 1
        else:
            summary['features']['passed'] += 1

        _emit(socketio, sid, 'summary', summary)

    _emit(socketio, sid, 'done', {'msg': 'All tests completed'})
