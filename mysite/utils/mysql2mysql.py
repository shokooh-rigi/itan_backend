import MySQLdb
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, filename='migration_errors.log', filemode='w')


mysql_conn_src = MySQLdb.connect(
    host="64.251.19.223",
    user="dtabtech_dev",
    password="qxjf@sXK)Fy0",
    database="dtabtech_maindb2"
)
mysql_conn_dest = MySQLdb.connect(
    host="mysql",
    user="debug",
    password="debug",
    database="test"
)

mysql_src_cursor = mysql_conn_src.cursor()
mysql_dest_cursor = mysql_conn_dest.cursor()

# Get list of tables from MySQL
mysql_src_cursor.execute("SHOW TABLES")
tables = [table[0] for table in mysql_src_cursor.fetchall()]
tables_to_exclude = ['django_migrations']

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
    'testsheetairmovingequipment_airmovingequipmentequipment',
    'testsheetairmovingequipment_airmovingequipmentsheetdata',
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
    'testsheetpitottraversesummary_pitottraversesummaryequipment',
    'testsheetpitottraversesummary_pitottraversesummarysheetdata',
    'testsheetprimaryheatexchanger2_primaryheatexchanger2equipment',
    'testsheetprimaryheatexchanger2_primaryheatexchanger2sheetdata',
    'testsheetprimaryheatexchanger_primaryheatexchangerequipment',
    'testsheetprimaryheatexchanger_primaryheatexchangersheetdata',
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


for table in tables:
    if table in tables_to_exclude:
        continue

    try:
        # Get the schema of the table
        mysql_src_cursor.execute(f"SHOW CREATE TABLE {table}")
        create_table_sql = mysql_src_cursor.fetchone()[1]

        # Create the table in the destination database
        mysql_dest_cursor.execute(f"DROP TABLE IF EXISTS {table}")
        mysql_dest_cursor.execute(create_table_sql)

        # Copy data from the source table to the destination table
        mysql_src_cursor.execute(f"SELECT * FROM {table}")
        rows = mysql_src_cursor.fetchall()

        # Fetch column information to construct the query
        mysql_src_cursor.execute(f"DESCRIBE {table}")
        columns = [column[0] for column in mysql_src_cursor.fetchall()]
        column_names = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        insert_query = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"

        # Insert rows into the destination table
        mysql_dest_cursor.executemany(insert_query, rows)
        mysql_conn_dest.commit()

        logging.info(f"Table {table} copied successfully.")

    except Exception as e:
        logging.error(f"Error copying table {table}: {e}")

# Close cursors and connections
mysql_src_cursor.close()
mysql_dest_cursor.close()
mysql_conn_src.close()
mysql_conn_dest.close()
