import sqlite3


# Connect to the SQLite database.
# SQLite creates the database file if it does not already exist.
connection = sqlite3.connect("placements.db")

# Create a cursor so we can execute SQL commands.
cursor = connection.cursor()

# Create the applications table if it does not already exist.
cursor.execute(
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

# Save the table creation changes.
connection.commit()

# Close the connection to the database.
connection.close()

# Let the user know that the setup completed successfully.
print("Database and applications table created successfully.")
