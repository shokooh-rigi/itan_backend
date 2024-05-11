import MySQLdb


mysql_conn_src = MySQLdb.connect(
    host="64.251.19.223",
    user="dtabtech_testusr",
    password="L[SP+hbSl!J{",
    database="dtabtech_testdb"
)

# Create a cursor object using the cursor() method
cursor = mysql_conn_src.cursor()

# SQL statement to drop a table
try:
    # Assuming the table to drop is 'authtoken_token'
    cursor.execute("DROP TABLE IF EXISTS authtoken_token;")
    mysql_conn_src.commit()  # Commit the changes to the database
    print("Table dropped successfully")
except MySQLdb.Error as e:
    print(f"Error: {e}")
    mysql_conn_src.rollback()  # Rollback in case of any error
finally:
    # Close the cursor and connection to the server
    cursor.close()
    mysql_conn_src.close()
