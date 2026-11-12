# Placement Application Tracker

A Streamlit app for recording job applications and reviewing application
status summaries. You can search and filter records, change their status,
manage interview dates, delete records with confirmation, and export the
displayed results as CSV.

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

On startup, the app adds an `interview_date` column to an existing database if
it is missing; existing application records are preserved. Add an interview
date when creating an application or update it later under **Manage
Applications**. Upcoming interviews are shown for applications with the
**Interview Scheduled** status and an interview date of today or later.

The CSV download follows the current company search and status filter.
Application records are stored in the local `placements.db` file. That file is
ignored by Git and is not included in this repository.

## Tests

Run the database tests with:

```powershell
python -m unittest test_placement_tracker_db.py
```