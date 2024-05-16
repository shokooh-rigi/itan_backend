import psycopg
import MySQLdb
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, filename='migration_errors.log', filemode='w')


mysql_conn = MySQLdb.connect(
    host="64.251.19.223",
    user="dtabtech_testusr",
    password="L[SP+hbSl!J{",
    database="dtabtech_testdb"
)

# Connect to PostgreSQL
pg_conn = psycopg.connect(
    dbname='test',
    user='debug',
    password='debug',
    host='postgres'
)

# Get MySQL cursor
mysql_cursor = mysql_conn.cursor()
# Get PostgreSQL cursor
pg_cursor = pg_conn.cursor()

# Get list of tables from MySQL
mysql_cursor.execute("SHOW TABLES")
tables = [table[0] for table in mysql_cursor.fetchall()]
tables_to_exclude = ['django_migrations']


# Function to find the primary key column name
def get_primary_key_column(pg_cursor, table):
    primary_key_query = f"""
    SELECT a.attname
    FROM pg_index i
    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
    WHERE i.indrelid = '{table}'::regclass AND i.indisprimary;
    """
    pg_cursor.execute(primary_key_query)
    primary_key_column = pg_cursor.fetchone()
    return primary_key_column[0] if primary_key_column else None

# Function to reset PostgreSQL sequences
def reset_postgres_sequence(pg_cursor, table):
    primary_key_column = get_primary_key_column(pg_cursor, table)
    if primary_key_column:
        seq_query = f"SELECT pg_get_serial_sequence('{table}', '{primary_key_column}')"
        pg_cursor.execute(seq_query)
        sequence_name = pg_cursor.fetchone()[0]

        if sequence_name:
            setval_query = f"SELECT setval('{sequence_name}', COALESCE((SELECT MAX({primary_key_column}) FROM {table}), 1))"
            pg_cursor.execute(setval_query)

def log_and_skip(table, error_message):
    """Log errors for a specific table and skip its processing."""
    logging.error(f"Error processing table {table}: {error_message}")
    print(f"Skipped table {table} due to errors. Check migration_errors.log for details.")


tables = [
    'django_content_type',
    # 'django_migrations',
    'django_session',
    'auth_group',                 
    'auth_permission',
    'auth_group_permissions',   
    'custom_user_user',  
    'custom_user_user_groups',
    'custom_user_user_user_permissions',
    'django_admin_log',
    'core_profile',                     
    'core_businesscheckingaccount',
    'core_companysubmittalform',
    'core_companysubmittalform_related_services',
    'core_companytype', 
    'core_contactinfo',        
    'core_creditcard',    
    'core_emailbodytemplate',         
    'core_licensefiles',
    'core_licenseinfo',
    'core_modulestoemailtemplaterelation',
    'core_person',                        
    'core_project',                 
    'core_service',                        
    'core_setting', 
    'core_techlabelmodel',  
    'submittal_companysubmittal',
    'submittal_submittalforms',
    'ibfm_ibidfile',
    'bidfilemgm_bidfile',
    'bidfilemgm_equipmentsubmittal',
    'estimator_estimate',
    'estimator_estimate_service',
    'estimator_estimatedetails',
    'estimator_estimateequipment',
    'estimator_estimatehistory',
    'estimator_proposal',
    'estimator_quote',
    'order_changeorder',
    'order_changeorderservice',
    'order_controlsystem',
    'order_controlsystemmanufacturer',
    'order_order',
    'order_techlabel',
    'order_techlabelextrafields',
    'gi_accountsummary',
    'gi_invoice',
    'gi_invoicehistory',
    'gi_invoicetransaction',
    'report_report',
    'coi_coi',          
    'coi_insurancecompany',
    'administrative_document',   
    'administrative_typesofdocument',
    'scheduler_maintenance',
    'scheduler_schedule',
    'scheduler_scheduletech',
    'settlement_settledmaintenances',
    'settlement_settledschedule',
    'settlement_settlement',
    'dbmanagement_actualdatacustomoperation',
    'dbmanagement_airterminalcode',
    'dbmanagement_equipment',
    'dbmanagement_equipmentcustomfield',
    'dbmanagement_equipmentdb',
    'dbmanagement_equipmentdbdesigndata',
    'dbmanagement_equipmentmanufacturer',
    'dbmanagement_equipmenttypecustomfield',
    'dbmanagement_equipmenttypecustomoperation',
    'dbmanagement_testsheet',
    'dbmanagement_testsheetcolumn',
    'dbmanagement_testsheetfield',
    'dbmanagement_testsheetoperation',
    'sheetcreator_airterminalequipment',
    'sheetcreator_airterminalsheetdata',
    'sheetcreator_datasheet',
    'sheetcreator_datasheetequipment',
    'sheetcreator_sheet',
    'sheetcreator_sheetactualdatacustomfield',
    'sheetcreator_sheetequipment',
    'sheetcreator_sheetequipmentactualdata',
    'sheetcreator_sheetequipmentcommondata',
    'sheetcreator_sheetequipmentcustomdata',
    'sheetcreator_testsheetdata',
    'sheetcreator_testsheetgeneraldata',
    'generatereport_reportsheet',
    'pdf_analyzer_addressextractiondebug',
    'pdf_analyzer_addressextractionrun',
    'projectprocess_projectprocess',
    'projectprocess_projectprocesspredemo',
    'testsheetairmoving_airmovingequipmentequipment',
    'testsheetairmoving_airmovingequipmentsheetdata',
    'testsheetchiller_chillerequipment',
    'testsheetchiller_chillersheetdata',
    'testsheetdalt_daltequipment',
    'testsheetdalt_daltsheetdata',
    'testsheetflow_flowequipment',
    'testsheetflow_flowsheetdata',
    'testsheethotwaterboiler_hotwaterboilerequipment',
    'testsheethotwaterboiler_hotwaterboilersheetdata',
    'testsheetinductionunit_inductionunitequipment',
    'testsheetinductionunit_inductionunitsheetdata',
    'testsheetpitottraverse_pitottraverseequipment',
    'testsheetpitottraverse_pitottraversesheetdata',
    'testsheetphe2_phe2equipment',
    'testsheetphe2_phe2sheetdata',
    'testsheetphe_pheequipment',
    'testsheetphe_phesheetdata',
    'testsheetpump_pumpequipment',
    'testsheetpump_pumpsheetdata',
    'testsheetvavboxfanheatschedule_vbfhsequipment',
    'testsheetvavboxfanheatschedule_vbfhssheetdata',
    'testsheetvavboxschedule_vbsequipment',
    'testsheetvavboxschedule_vbssheetdata',
    'testsheetvavboxtemperatureschedule_vbtsequipment',
    'testsheetvavboxtemperatureschedule_vbtssheetdata',
    'testsheetvelocity_velocityequipment',
    'testsheetvelocity_velocitysheetdata',
    'testsheetvelocity_velocitysheettabledata'
]

cols2conv = [
    "flag", "is_active", "archive", "hidden_for_customer", "settlement",
    "required_in_design", "required_in_actual", "is_staff", "is_superuser",
    "email_confirmed", "default_card", "saved_flag", "confirmed",
    "general_notes_and_comments_finalize", "partial_job_done", "colored_drawing_finalize", 
    "fully_settled", "detailed_drawing", "schedule_drawing", "mechanical_drawing", 
    "tech_test_sheets", "mark_as_paid", "settled_type", "is_custom",
    "sheet_generator", "required", "show_in_actual", "show_in_design", "apply_on_design",
    "apply_on_actual", "rogue_design_data_entry_completed", "rogue_actual_data_entry_completed",
    "main_data_entry_completed", "design_data_entry_completed", "actual_data_entry_completed",
    "terminal_actual_data_entry_completed", "terminal_design_data_entry_completed", "velocity_data",
    "tech_package", "tech_scheduled", "job_completed", "report_out", "invoiced",
    "completed", 
]


try:
    pg_conn.rollback()
    # Get list of tables from PostgreSQL
    pg_cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    pg_tables = [table[0] for table in pg_cursor.fetchall()]
    missing_tables = [table for table in tables if table not in pg_tables and table not in tables_to_exclude]
    
    if missing_tables:
        logging.warning("Tables missing in PostgreSQL:")
        for table in missing_tables:
            logging.warning(table)
    else:
        logging.info("All tables from MySQL are available in PostgreSQL.")

    # Disable FK constraints temporarily
    pg_cursor.execute("SET session_replication_role = 'replica';")
    
    for table in tables:
        if table in tables_to_exclude:
            continue
        
        try:
            # Disable triggers for the current table
            pg_cursor.execute(f"ALTER TABLE {table} DISABLE TRIGGER ALL;")
            pg_cursor.execute(f"TRUNCATE TABLE {table} CASCADE")
            pg_cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'")
            psql_columns = [row[0] for row in pg_cursor.fetchall()]

            mysql_cursor.execute(f"SELECT * FROM {table}")
            data = mysql_cursor.fetchall()
            mysql_columns = [i[0] for i in mysql_cursor.description]

            data_dicts = [{mysql_columns[i]: value for i, value in enumerate(row)} for row in data]
            for data_dict in data_dicts:
                for col in cols2conv:
                    if col in data_dict:
                        data_dict[col] = bool(data_dict[col])
                    # Exceptions
                    if table == 'scheduler_schedule':
                        data_dict['pre_demo'] = bool(data_dict['pre_demo'])

                for col in psql_columns:
                    data_dict.setdefault(col, None)

                if 'number_of_exhaust_air_terminal' not in data_dict or data_dict['number_of_exhaust_air_terminal'] is None:
                    data_dict['number_of_exhaust_air_terminal'] = 0
            
            columns_string = ", ".join([f'"{col}"' for col in psql_columns])
            placeholders = ", ".join(f"%({col})s" for col in psql_columns)

            insert_query = f"""
            INSERT INTO {table} ({columns_string}) VALUES ({placeholders})
            ON CONFLICT DO NOTHING;
            """
            pg_cursor.executemany(insert_query, data_dicts)
            reset_postgres_sequence(pg_cursor, table)
            # Re-enable triggers for the current table
            pg_cursor.execute(f"ALTER TABLE {table} ENABLE TRIGGER ALL;")
        except Exception as table_error:
            logging.error(f"Error inserting data for table {table}: {table_error}")
            logging.error(columns_string)
            logging.error(placeholders)
            logging.error("===" * 10)
            log_and_skip(table, str(table_error))

    pg_cursor.execute("SET session_replication_role = 'origin';")
    pg_conn.commit()
    logging.info("Data transfer completed successfully.")
except Exception as e:
    logging.critical(f"Global error: {e}")
    pg_conn.rollback()
    pg_cursor.execute("SET session_replication_role = 'origin';")


def test_data_integrity(table_name):
    mysql_cursor.execute(f"SELECT * FROM {table_name}")
    mysql_data = mysql_cursor.fetchall()

    pg_cursor.execute(f"SELECT * FROM {table_name}")
    pg_data = pg_cursor.fetchall()

    assert mysql_data == pg_data, f"Data mismatch for table {table_name}"

for table in tables:
    if table in tables_to_exclude:
        continue

    try:
        mysql_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        mysql_count = mysql_cursor.fetchone()[0]

        pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        pg_count = pg_cursor.fetchone()[0]

        if mysql_count != pg_count:
            logging.warning(f"Table {table} - MySQL count: {mysql_count}, PostgreSQL count: {pg_count}")
        else:
            logging.info(f"Table {table} has matching counts in both databases.")

    except Exception as count_error:
        logging.error(f"Error comparing counts for table {table}: {count_error}")


mysql_cursor.close()
pg_cursor.close()
mysql_conn.close()
pg_conn.close()
