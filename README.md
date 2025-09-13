# Flask BDD Runner (Behave) with SocketIO Live Dashboard

## What this is
A small Flask app that runs Behave (Gherkin) tests and streams live updates
(feature → scenario → steps) to the browser using Flask-SocketIO and eventlet.

## Install
1. Create a virtualenv (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. Run the app
   ```bash
   python app.py
   ```

3. Open `http://localhost:5000` in your browser and click **Run Tests**.

## Notes
- Behave must be installed (it's in requirements.txt).
- The example feature is under `tests/features/example.feature`.
- When Behave runs it writes JSON to `tests/reports/results.json`.
