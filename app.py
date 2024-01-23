from flask import Flask, request, render_template, jsonify
from azure.storage.blob import BlobServiceClient
from azure.identity import ClientSecretCredential 
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import *
from datetime import datetime, timedelta
import time
import os

app = Flask(__name__, static_url_path='', static_folder='static')

# Azure Storage Account settings
CONNECTION_STRING = 'DefaultEndpointsProtocol=https;AccountName=salesrepstacc;AccountKey=w1YCSmzZ5nQrkkGXWSNljI2tOH1VIvKHp8HPO5MgJGNInMvf24swHZ+WELNuMq6XyZmL4T97hAL8+AStGT8bXA==;EndpointSuffix=core.windows.net'

# Determine the environment and set the container name
ENVIRONMENT = os.getenv('FLASK_ENV', 'development')

# Azure subscription ID
subscription_id = '53587102-7bd3-492c-a651-734213d61ed9'

# This program creates this resource group. If it's an existing resource group, comment out the code that creates the resource group
rg_name = 'salesreporting'

# The data factory name. It must be globally unique.
df_name = 'salesrepdf'

# Specify your Active Directory client ID, client secret, and tenant ID
credentials = ClientSecretCredential(client_id='9b23a631-3019-4890-bd89-3fda2f168f4e', client_secret='7ab8Q~cmC66jJHZmtLIg14I.2McNS-eNeFj29dlt', tenant_id='06f752f0-4e41-4efb-ba12-9f1c8bcd3025') 

resource_client = ResourceManagementClient(credentials, subscription_id)
adf_client = DataFactoryManagementClient(credentials, subscription_id)

if ENVIRONMENT == 'development':
    CONTAINER_NAME = 'salesrepblobdev'
    DB_CONNECTION_STRING = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:salesrepdbserver.database.windows.net,1433;Database=salesrepdbdev;Uid=berlin;Pwd=Youtube@123;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
    pipeline_name = 'Ingestion - Dev'
else:
    CONTAINER_NAME = 'salesrepblob'
    DB_CONNECTION_STRING = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:salesrepdbserver.database.windows.net,1433;Database=salesrepdb;Uid=berlin;Pwd=Youtube@123;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
    pipeline_name = 'Ingestion - Prod'

blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files_to_blob():
    uploaded_files = request.files.getlist('files[]')
    
    messages = []
    for file in uploaded_files:
        if file:
            blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=file.filename)
            blob_client.upload_blob(file, overwrite=True)
            messages.append(f'Successfully uploaded {file.filename}!')
        else:
            messages.append('A required file was missing.')
    
    return '<br>'.join(messages)

@app.route('/list-blobs')
def list_blobs():
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)
    blobs_list = container_client.list_blobs()
    blobs = [blob.name for blob in blobs_list]
    return jsonify(blobs=blobs)

@app.route('/delete-blobs', methods=['POST'])
def delete_blobs():
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)
    blob_list = [b.name for b in list(container_client.list_blobs())]
    for blob in blob_list:
        container_client.delete_blob(blob)
    return jsonify({'status': 'success', 'message': 'All blobs have been deleted.'})

@app.route('/tables')
def tables():
    return render_template('tables.html')

@app.route('/list-tables')
def list_tables():
    import pyodbc
    conn = pyodbc.connect(DB_CONNECTION_STRING)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sys.tables")
    tables = [table[0] for table in cursor.fetchall()]
    return jsonify(tables=tables)

@app.route('/delete-tables', methods=['POST'])
def delete_tables():
    import pyodbc
    # Establish the database connection
    conn = pyodbc.connect(DB_CONNECTION_STRING)
    cursor = conn.cursor()
    # Step 1: Identify and drop foreign key constraints
    cursor.execute("""
        SELECT 
            fk.name AS FK_name, 
            tp.name AS parent_table,
            ref.name AS referenced_table 
        FROM 
            sys.foreign_keys AS fk
        INNER JOIN 
            sys.tables AS tp ON fk.parent_object_id = tp.object_id
        INNER JOIN 
            sys.tables AS ref ON fk.referenced_object_id = ref.object_id
    """)
    fks = cursor.fetchall()
    for fk in fks:
        alter_query = f"ALTER TABLE {fk.parent_table} DROP CONSTRAINT {fk.FK_name}"
        cursor.execute(alter_query)
    # Step 2: Drop tables
    cursor.execute("SELECT name FROM sys.tables")
    tables = [table[0] for table in cursor.fetchall()]
    for table in tables:
        drop_query = f"DROP TABLE {table}"
        cursor.execute(drop_query)
    # Commit the transaction and close the connection
    conn.commit()
    return jsonify({'status': 'success', 'message': 'All tables and foreign key constraints have been deleted.'})

@app.route('/create-tables', methods=['POST'])
def create_tables():
    import pyodbc
    import os
    conn = pyodbc.connect(DB_CONNECTION_STRING)
    cursor = conn.cursor()
    # Retrieve all .sql files from the specified directory
    sql_files = [file for file in os.listdir('scripts/DDL') if file.endswith('.sql')]
    # Sort the files: 'dim' files first, then others, then 'fact' files last
    dim_files = [file for file in sql_files if 'dim' in file]
    fact_files = [file for file in sql_files if 'fact' in file]
    sorted_files = dim_files + fact_files
    # Execute each SQL file in the sorted order
    for file in sorted_files:
        with open(os.path.join('scripts/DDL', file), 'r') as f:
            sql = f.read()
            cursor.execute(sql)
    conn.commit()
    return jsonify({'status': 'success', 'message': 'All tables have been created.'})

@app.route('/data_flow')
def data_flow():
    return render_template('data_flow.html')

# Write decorator and function for /trigger-ingestion which triggers the Azure Data Factore pipeline using adf_client.pipelines.create_run(rg_name, df_name, pipeline_name)
@app.route('/trigger-ingestion', methods=['POST'])
def trigger_ingestion():
    run_response = adf_client.pipelines.create_run(rg_name, df_name, pipeline_name)
    return jsonify({'status': 'success', 'message': 'The ingestion pipeline has been triggered.'})

if __name__ == '__main__':
    app.run(debug=True)
