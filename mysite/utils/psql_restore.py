import psycopg
import os
import csv

# Connect to PostgreSQL
pg_conn = psycopg.connect(
    dbname='test',
    user='debug',
    password='debug',
    host='postgres'
)

# Function to create a table dynamically in PostgreSQL with unique constraint support
def create_table_from_csv_headers(cursor, table_name, headers, primary_key=None, unique_fields=None):
    # Quote each column name to avoid reserved keyword errors
    columns_definition = ', '.join([f'"{column}" TEXT' for column in headers])
    create_query = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_definition}'
    
    # If a primary key is specified, add it
    if primary_key and primary_key in headers:
        create_query += f', PRIMARY KEY ("{primary_key}")'
    
    # If unique fields are provided, add a unique constraint
    if unique_fields:
        unique_fields_list = ', '.join([f'"{field}"' for field in unique_fields])
        create_query += f', UNIQUE ({unique_fields_list})'
    
    create_query += ')'
    
    cursor.execute(create_query)
    print(f"Table '{table_name}' created (if not already existing).")

# Function to clean existing table data
def clear_existing_data(cursor, table_name):
    cursor.execute(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY')
    print(f"Existing data in table '{table_name}' has been cleared.")

# Function to load CSV data into a PostgreSQL table
def load_csv_to_pg(cursor, table_name, csv_file_path, primary_key=None, unique_fields=None):
    with open(csv_file_path, mode='r', newline='', encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file)
        headers = next(reader)  # First row is the header
        columns = ', '.join([f'"{header}"' for header in headers])
        placeholders = ', '.join(['%s'] * len(headers))
        
        # Create the table if it doesn't exist, with primary key and unique constraints if applicable
        create_table_from_csv_headers(cursor, table_name, headers, primary_key, unique_fields)

        # Clear existing data before inserting new data
        clear_existing_data(cursor, table_name)

        insert_query = f'INSERT INTO "{table_name}" ({columns}) VALUES ({placeholders})'
        
        for row in reader:
            cursor.execute(insert_query, row)

    print(f"Data from '{csv_file_path}' loaded into '{table_name}'.")

# Get a cursor for executing PostgreSQL queries
pg_cursor = pg_conn.cursor()

# Directory containing the backup CSV files
backup_directory = 'mysql_backup'

# Ensure backup directory exists
if os.path.exists(backup_directory) and os.path.isdir(backup_directory):
    # List all CSV files in the backup directory
    csv_files = [f for f in os.listdir(backup_directory) if f.endswith('.csv')]

    # Specify primary keys and unique constraints for known tables
    table_constraints = {
        'administrative_typesofdocument': {
            'primary_key': 'id',
            'unique_fields': ['id']  # Adjust as per actual unique fields
        },
        # Add other tables with known primary keys and unique constraints if needed
    }

    # Load each CSV into the corresponding PostgreSQL table
    for csv_file in csv_files:
        table_name = csv_file.replace('.csv', '')
        csv_file_path = os.path.join(backup_directory, csv_file)

        # Look up the primary key and unique constraints for each table
        constraints = table_constraints.get(table_name, {})
        primary_key = constraints.get('primary_key', None)
        unique_fields = constraints.get('unique_fields', None)

        load_csv_to_pg(pg_cursor, table_name, csv_file_path, primary_key, unique_fields)

    pg_conn.commit()  # Commit all changes
    print("Data import completed!")
else:
    print(f"Backup directory '{backup_directory}' not found!")

# Close the PostgreSQL cursor and connection
pg_cursor.close()
pg_conn.close()
