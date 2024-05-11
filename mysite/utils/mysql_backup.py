import MySQLdb
import os
import csv


mysql_conn_src = MySQLdb.connect(
    host="64.251.19.223",
    user="dtabtech_dev",
    password="qxjf@sXK)Fy0",
    database="dtabtech_maindb2"
)


# Function to export data of each table to a CSV file
def export_to_csv(cursor, table_name, directory):
    file_path = os.path.join(directory, f"{table_name}.csv")
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description]

    with open(file_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(column_names)  # Write column headers
        writer.writerows(rows)  # Write data rows

    print(f"Table '{table_name}' exported to '{file_path}'")

# Create a directory to store the CSV files
backup_directory = 'mysql_backup'
if not os.path.exists(backup_directory):
    os.makedirs(backup_directory)

# Get a cursor to execute queries
cursor = mysql_conn_src.cursor()

# Retrieve the list of tables
cursor.execute("SHOW TABLES")
tables = cursor.fetchall()

# Export each table to its own CSV file
for (table_name,) in tables:
    export_to_csv(cursor, table_name, backup_directory)

# Close the cursor and connection
cursor.close()
mysql_conn_src.close()

print("Backup completed!")
