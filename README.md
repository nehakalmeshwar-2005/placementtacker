# Placement Application Tracker

A Streamlit app for recording job applications and reviewing application
status summaries.

## Setup

1. Install Python 3.
2. Install the dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Create the local SQLite database:

   ```powershell
   python init_db.py
   ```

4. Start the app:

   ```powershell
   streamlit run app.py
   ```

Application records are stored in the local `placements.db` file. That file is
ignored by Git and is not included in this repository.