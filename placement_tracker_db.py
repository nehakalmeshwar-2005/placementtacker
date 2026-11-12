import csv
import io
import sqlite3
from datetime import date


DATABASE_NAME = "placements.db"
APPLICATION_COLUMNS = [
    "application_id",
    "company_name",
    "job_role",
    "application_date",
    "status",
    "interview_date",
]


def get_connection(database_name=DATABASE_NAME):
    """Open a connection to the SQLite database."""
    return sqlite3.connect(database_name)


def initialize_database(database_name=DATABASE_NAME):
    """Create the applications table and migrate older databases."""
    connection = get_connection(database_name)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                job_role TEXT NOT NULL,
                application_date TEXT,
                status TEXT
            )
            """
        )
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(applications)"
            ).fetchall()
        }
        if "interview_date" not in columns:
            connection.execute(
                "ALTER TABLE applications ADD COLUMN interview_date TEXT"
            )
        connection.commit()
    finally:
        connection.close()


def add_application(
    company_name,
    job_role,
    application_date,
    status,
    interview_date=None,
    database_name=DATABASE_NAME,
):
    """Save one application in the database."""
    connection = get_connection(database_name)
    try:
        connection.execute(
            """
            INSERT INTO applications
                (company_name, job_role, application_date, status, interview_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                company_name,
                job_role,
                application_date,
                status,
                interview_date,
            ),
        )
        connection.commit()
    finally:
        connection.close()


def get_applications(company_query="", status=None, database_name=DATABASE_NAME):
    """Retrieve applications matching the optional company and status filters."""
    conditions = []
    parameters = []
    if company_query:
        conditions.append("company_name LIKE ? COLLATE NOCASE")
        parameters.append(f"%{company_query}%")
    if status:
        conditions.append("status = ?")
        parameters.append(status)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    connection = get_connection(database_name)
    try:
        return connection.execute(
            f"""
            SELECT application_id, company_name, job_role,
                   application_date, status, interview_date
            FROM applications
            {where_clause}
            ORDER BY application_id
            """,
            parameters,
        ).fetchall()
    finally:
        connection.close()


def applications_to_csv(applications):
    """Encode application records in the same column order as the UI table."""
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(APPLICATION_COLUMNS)
    writer.writerows(applications)
    return output.getvalue().encode("utf-8")


def get_total_applications(database_name=DATABASE_NAME):
    """Return the number of saved applications."""
    connection = get_connection(database_name)
    try:
        return connection.execute(
            "SELECT COUNT(*) FROM applications"
        ).fetchone()[0]
    finally:
        connection.close()


def get_most_applied_role(database_name=DATABASE_NAME):
    """Return the most frequently used job role, breaking ties alphabetically."""
    connection = get_connection(database_name)
    try:
        result = connection.execute(
            """
            SELECT job_role, COUNT(*) AS application_count
            FROM applications
            GROUP BY job_role
            ORDER BY application_count DESC, job_role ASC
            LIMIT 1
            """
        ).fetchone()
        return result[0] if result else None
    finally:
        connection.close()


def get_status_summary(statuses, database_name=DATABASE_NAME):
    """Return application counts for each supplied status."""
    connection = get_connection(database_name)
    try:
        rows = connection.execute(
            """
            SELECT status, COUNT(*) AS application_count
            FROM applications
            GROUP BY status
            """
        ).fetchall()
    finally:
        connection.close()

    counts = {status: 0 for status in statuses}
    for status, count in rows:
        if status in counts:
            counts[status] = count
    return counts


def update_application_status(
    application_id, status, database_name=DATABASE_NAME
):
    """Update an application's status."""
    connection = get_connection(database_name)
    try:
        cursor = connection.execute(
            "UPDATE applications SET status = ? WHERE application_id = ?",
            (status, application_id),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def update_interview_date(
    application_id, interview_date, database_name=DATABASE_NAME
):
    """Set or clear an application's interview date."""
    connection = get_connection(database_name)
    try:
        cursor = connection.execute(
            "UPDATE applications SET interview_date = ? WHERE application_id = ?",
            (interview_date, application_id),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def delete_application(application_id, database_name=DATABASE_NAME):
    """Delete an application by its ID."""
    connection = get_connection(database_name)
    try:
        cursor = connection.execute(
            "DELETE FROM applications WHERE application_id = ?",
            (application_id,),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def get_upcoming_interviews(today=None, database_name=DATABASE_NAME):
    """Return scheduled interviews occurring today or later."""
    today = today or date.today().isoformat()
    connection = get_connection(database_name)
    try:
        return connection.execute(
            """
            SELECT application_id, company_name, job_role, interview_date
            FROM applications
            WHERE status = 'Interview Scheduled'
              AND interview_date IS NOT NULL
              AND interview_date >= ?
            ORDER BY interview_date, application_id
            """,
            (today,),
        ).fetchall()
    finally:
        connection.close()
