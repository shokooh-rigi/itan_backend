import MySQLdb

def test_mysql_connection():
    try:
        # Replace these variables with your database credentials
        db = MySQLdb.connect(
            host="64.251.19.223",
            user="dtabtech_testusr",
            password="L[SP+hbSl!J{",
            database="dtabtech_testdb"
        )

        # Create a cursor object using the cursor() method
        cursor = db.cursor()

        # Execute a simple SQL query to test the connection
        cursor.execute("SELECT VERSION()")

        # Fetch the result of the query
        data = cursor.fetchone()

        # Print the result
        print("Database version:", data)

        # Close the cursor and the connection
        cursor.close()
        db.close()

    except MySQLdb.Error as e:
        print(f"Error: Unable to connect to the database\n{e}")

# Test the function
test_mysql_connection()
