import subprocess
import json
import os
import sys

def _emit(socketio, sid, event, payload):
    """Helper to safely emit events over SocketIO."""
    try:
        socketio.emit(event, payload, to=sid)
    except Exception:
        # best-effort emit; socket may have disconnected
        pass

def run_tests(socketio, sid: str):
    """Run Behave tests and stream results + summaries live to the dashboard."""

    out_path = os.path.join("tests", "reports", "results.json")

    # ensure reports dir exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # remove previous report
    try:
        if os.path.exists(out_path):
            os.remove(out_path)
    except Exception:
        pass

    features_path = "features"

    # Command: run behave with progress (stdout) and json (file only)
    cmd = [
        sys.executable, "-m", "behave",
        features_path,
        "--no-summary", "--no-snippets",
        "--format", "progress", "--outfile", "NUL",  # discard extra progress output file
        "--format", "json", "--outfile", out_path    # structured JSON report
    ]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=os.path.abspath(".")
        )
    except FileNotFoundError:
        _emit(socketio, sid, "log", {"line": "ERROR: behave not found. Is it installed in this environment?"})
        _emit(socketio, sid, "done", {"msg": "Failed: behave not found"})
        return

    # stream raw console output
    if process.stdout:
        for line in process.stdout:
            _emit(socketio, sid, "log", {"line": line.rstrip()})

    process.wait()

    # short delay to ensure file write completes
    import time
    time.sleep(0.1)

    if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        _emit(socketio, sid, "log", {"line": f"No JSON report found or file is empty at {out_path}."})
        _emit(socketio, sid, "done", {"msg": "Completed (no report)."})
        return

    # parse JSON report
    try:
        with open(out_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        _emit(socketio, sid, "log", {"line": f"Error reading JSON report: {e}"})
        _emit(socketio, sid, "done", {"msg": "Completed (parse error)."})
        return

    summary = {
        "features": {"total": 0, "passed": 0, "failed": 0},
        "scenarios": {"total": 0, "passed": 0, "failed": 0},
        "steps": {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
    }

    for feature in report:
        summary["features"]["total"] += 1
        feature_name = feature.get("name", "Unnamed Feature")
        feature_failed = False

        for element in feature.get("elements", []):
            if element.get("type") != "scenario":
                continue

            summary["scenarios"]["total"] += 1
            scenario_name = element.get("name", "Unnamed Scenario")
            scenario_status = "passed"

            _emit(socketio, sid, "scenario", {
                "feature": feature_name,
                "scenario": scenario_name,
                "status": "running"
            })

            for step in element.get("steps", []):
                summary["steps"]["total"] += 1
                step_name = f"{step.get('keyword','')} {step.get('name','')}".strip()
                result = step.get("result", {}) or {}
                status = result.get("status", "unknown")
                duration = result.get("duration", 0) or 0

                if status == "passed":
                    summary["steps"]["passed"] += 1
                elif status == "failed":
                    summary["steps"]["failed"] += 1
                    scenario_status = "failed"
                    feature_failed = True
                elif status == "skipped":
                    summary["steps"]["skipped"] += 1

                _emit(socketio, sid, "step", {
                    "feature": feature_name,
                    "scenario": scenario_name,
                    "step": step_name,
                    "status": status,
                    "duration": f"{duration:.2f}s"
                })

                _emit(socketio, sid, "summary", summary)

            summary["scenarios"][scenario_status] += 1
            _emit(socketio, sid, "scenario", {
                "feature": feature_name,
                "scenario": scenario_name,
                "status": scenario_status
            })

        if feature_failed:
            summary["features"]["failed"] += 1
        else:
            summary["features"]["passed"] += 1

        _emit(socketio, sid, "summary", summary)

    _emit(socketio, sid, "done", {"msg": "All tests completed"})