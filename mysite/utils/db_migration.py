import mysql.connector
import psycopg2
import pandas as pd
from sqlalchemy import create_engine


mysql_user = 'dtabtech_testusr'
mysql_password = 'L[SP+hbSl!J{'
mysql_host = '64.251.19.223'
mysql_port = 3306
mysql_db = 'dtabtech_testdb'

psql_user = 'debug'
psql_password = 'debug'
psql_host = 'postgres'
psql_port = 5432
psql_db = 'test'


mysql_config = {
    'user': mysql_user,
    'password': mysql_password,
    'host': mysql_host,
    'database': mysql_db,
    'port': mysql_port
}

psql_config = {
    'user': psql_user,
    'password': psql_password,
    'host': psql_host,
    'dbname': psql_db,
    'port': psql_port
}

mysql_conn = mysql.connector.connect(**mysql_config)
mysql_cursor = mysql_conn.cursor()

psql_conn = psycopg2.connect(user=psql_config['user'], password=psql_config['password'], host=psql_config['host'], port=psql_config['port'], dbname='postgres')
psql_conn.autocommit = True
psql_cursor = psql_conn.cursor()

print(f"Dropping database {psql_config['dbname']} if exists.")
psql_cursor.execute(f"DROP DATABASE IF EXISTS {psql_config['dbname']};")
print(f"Creating database {psql_config['dbname']}.")
psql_cursor.execute(f"CREATE DATABASE {psql_config['dbname']};")
psql_conn.close()

psql_conn = psycopg2.connect(**psql_config)
psql_cursor = psql_conn.cursor()

mysql_engine = create_engine(f"mysql+mysqlconnector://{mysql_config['user']}:{mysql_config['password']}@{mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}")
psql_engine = create_engine(f"postgresql+psycopg2://{psql_config['user']}:{psql_config['password']}@{psql_config['host']}:{psql_config['port']}/{psql_config['dbname']}")

mysql_cursor.execute("SHOW TABLES;")
tables = [row[0] for row in mysql_cursor.fetchall()]
print(f"Tables found in MySQL database: {tables}")

for table in tables:
    print(f"Processing table: {table}")
    df = pd.read_sql(f"SELECT * FROM {table}", mysql_engine)
    print(f"Fetched {len(df)} records from table {table}.")

    df.to_sql(table, psql_engine, index=False, if_exists='replace', method='multi')
    print(f"Table {table} migrated successfully.")
    
    psql_cursor.execute(f"SELECT COUNT(*) FROM {table};")
    count = psql_cursor.fetchone()[0]
    print(f"Table {table} has {count} records in PostgreSQL.")

# Close connections
mysql_conn.close()
psql_conn.close()
print("Migration and verification completed.")
