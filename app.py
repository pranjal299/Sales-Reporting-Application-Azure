from flask import Flask, request, render_template, jsonify
from azure.storage.blob import BlobServiceClient
import os

app = Flask(__name__, static_url_path='', static_folder='static')

# Azure Storage Account settings
CONNECTION_STRING = 'DefaultEndpointsProtocol=https;AccountName=salesrepstorageacc;AccountKey=7VFqRFCzw+o5Dg4iTmFcClNkhDndSTNGKE1YcdFlVhxbrWP/q0JWOS4VDZvgVezQLcw8WK4KEj7I+ASts2Kh/A==;EndpointSuffix=core.windows.net'

# Determine the environment and set the container name
ENVIRONMENT = os.getenv('FLASK_ENV', 'development')

if ENVIRONMENT == 'development':
    CONTAINER_NAME = 'salesrepcontainerlocal'
    DB_CONNECTION_STRING = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:sales-reporting-system.database.windows.net,1433;Database=salesrepdbdev;Uid=berlin;Pwd=Youtube123;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
else:
    CONTAINER_NAME = 'salesrepcontainer'
    DB_CONNECTION_STRING = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:sales-reporting-system.database.windows.net,1433;Database=salesrepdb;Uid=berlin;Pwd=Youtube123;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'

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
# Code for creating tables based on individual SQL scripts present in the static folder
def create_tables():
    import pyodbc
    conn = pyodbc.connect(DB_CONNECTION_STRING)
    cursor = conn.cursor()
    for file in os.listdir('scripts/DDL'):
        if file.endswith('.sql'):
            with open(os.path.join('scripts/DDL', file), 'r') as f:
                sql = f.read()
                cursor.execute(sql)
    conn.commit()
    return jsonify({'status': 'success', 'message': 'All tables have been created.'})

if __name__ == '__main__':
    app.run(debug=True)
