import psycopg
import MySQLdb
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, filename='migration_errors.log', filemode='w')


mysql_conn = MySQLdb.connect(
    host="64.251.19.223",
    user="dtabtech_dev",
    password="qxjf@sXK)Fy0",
    database="dtabtech_maindb2"
)

# Connect to PostgreSQL
pg_conn = psycopg.connect(
    dbname='test',
    user='debug',
    password='debug',
    host='postgres'
)


# Retrieve information about constraints from MySQL
with mysql_conn.cursor() as mysql_cursor:
    mysql_cursor.execute("SHOW TABLES")
    tables = mysql_cursor.fetchall()

    for (table,) in tables:
        # Primary keys
        mysql_cursor.execute(f"SHOW KEYS FROM {table} WHERE Key_name = 'PRIMARY'")
        primary_keys = mysql_cursor.fetchall()

        # Foreign keys
        mysql_cursor.execute(f"SELECT * FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA = 'your_schema' AND TABLE_NAME = '{table}' AND REFERENCED_TABLE_NAME IS NOT NULL")
        foreign_keys = mysql_cursor.fetchall()

        # Unique indexes
        mysql_cursor.execute(f"SHOW INDEX FROM {table} WHERE Non_unique = 0 AND Key_name != 'PRIMARY'")
        unique_indexes = mysql_cursor.fetchall()

        # Initialize SQL commands
        pg_sql_statements = []

        # Primary Key Constraint Check
        for pk in primary_keys:
            primary_key_name = f"{table}_pkey"
            pg_pk_sql = f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{primary_key_name}') THEN ALTER TABLE {table} ADD CONSTRAINT {primary_key_name} PRIMARY KEY ({pk[4]}); END IF; END $$;"
            pg_sql_statements.append(pg_pk_sql)

        # Foreign Key Constraint Check
        for fk in foreign_keys:
            foreign_key_name = f"{fk[2]}_fk"
            pg_fk_sql = f"""
            DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{foreign_key_name}') THEN
            ALTER TABLE {fk[6]} ADD CONSTRAINT {foreign_key_name} FOREIGN KEY ({fk[7]}) REFERENCES {fk[10]}({fk[11]}) ON DELETE {fk[8]} ON UPDATE {fk[9]};
            END IF; END $$;
            """
            pg_sql_statements.append(pg_fk_sql)

        # Unique Index Check
        for index in unique_indexes:
            unique_index_name = index[2]
            pg_index_sql = f"CREATE UNIQUE INDEX IF NOT EXISTS {unique_index_name} ON {index[0]} ({index[4]});"
            pg_sql_statements.append(pg_index_sql)

        # Execute all SQL statements
        with pg_conn.cursor() as pg_cursor:
            for statement in pg_sql_statements:
                pg_cursor.execute(statement)


# Remember to close both connections
mysql_conn.close()
pg_conn.close()
