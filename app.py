from flask import Flask, request, render_template, jsonify, send_file, session
from flask_session import Session
from azure.storage.blob import BlobServiceClient
from azure.identity import ClientSecretCredential 
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import *
from datetime import datetime, timedelta
import time
import os
import pytz
import pyodbc
import requests
from together import Together
import pandas as pd
from io import BytesIO

app = Flask(__name__, static_url_path='', static_folder='static')
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Azure Storage Account settings
CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=salesreportingstacc;AccountKey=97+RZ/EBfDX+99pjcSX7i8j/bf50mzl+MyiGUyymQTO3jt2fVMh2Zg8XtQQxbOfcIuf5fsptr/Ei+AStYPe3WQ==;EndpointSuffix=core.windows.net"

# Azure subscription ID
subscription_id = '8c10f661-e991-47d6-85c8-50e6fe1af3e6'

# rg_name
rg_name = 'salesreportingapplication_group'

# The data factory name. It must be globally unique.
df_name = 'salesreportingappadf'

# Specify your Active Directory client ID, client secret, and tenant ID
credentials = ClientSecretCredential(client_id='259fe23b-6bf9-41d8-82bb-2d5cdb209949', client_secret='YourSecurePasswordHere', tenant_id='60956884-10ad-40fa-863d-4f32c1e3a37a') 

resource_client = ResourceManagementClient(credentials, subscription_id)
adf_client = DataFactoryManagementClient(credentials, subscription_id)

# Define the connection parameters
server = 'salesreportingappdbserver.database.windows.net'
database = 'salesreportingappdb'
username = 'berlin'
password = 'Youtube@123'

# Construct the connection string
DB_CONNECTION_STRING = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

CONTAINER_NAME = 'salesrepblob'
pipeline_postfix = 'Prod'
pipelines_of_interest = ['Ingest Products Prod', 'Ingest Payments Prod', 'Ingest Customers Prod', 'Ingest Employees Prod', 'Ingest Transactions Prod']

blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)

API_KEY = '8e8e05d2ba164b2a477e7b6874f2bbf7c49d1f93450b1fb352625b0587e479ca'
client = Together(api_key=API_KEY)

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
    conn = pyodbc.connect(DB_CONNECTION_STRING)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sys.tables")
    tables = [table[0] for table in cursor.fetchall()]
    return jsonify(tables=tables)

@app.route('/delete-tables', methods=['POST'])
def delete_tables():
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
    conn = pyodbc.connect(DB_CONNECTION_STRING)
    cursor = conn.cursor()
    # Retrieve all .sql files from the specified directory
    sql_files = [file for file in os.listdir('scripts/DDL') if file.endswith('.sql')]
    # Sort the files: 'dim' files first, then 'metrics' files, then others, then 'fact' files last
    dim_files = [file for file in sql_files if 'dim' in file]
    metrics_files = [file for file in sql_files if 'metrics' in file]
    fact_files = [file for file in sql_files if 'fact' in file]
    other_files = [file for file in sql_files if file not in dim_files and file not in metrics_files and file not in fact_files]
    sorted_files = dim_files + metrics_files + other_files + fact_files
    # Execute each SQL file in the sorted order
    for file in sorted_files:
        with open(os.path.join('scripts/DDL', file), 'r') as f:
            sql = f.read()
            # Split the SQL script at each 'GO' command
            sql_commands = sql.split('GO')
            for command in sql_commands:
                if command.strip():  # Skip empty commands
                    cursor.execute(command)
    conn.commit()
    return jsonify({'status': 'success', 'message': 'All tables have been created.'})

@app.route('/table_data')
def table_data():
    return render_template('table_data.html')

@app.route('/pipeline-status')
def pipeline_status():
    pipeline_runs = adf_client.pipeline_runs.query_by_factory(
        rg_name,
        df_name,
        {"lastUpdatedAfter": datetime.now() - timedelta(days=1), 
         "lastUpdatedBefore": datetime.now() + timedelta(days=1)}
    )

    # Collect runs for each pipeline
    runs_by_pipeline = {pipeline: [] for pipeline in pipelines_of_interest}
    for run in pipeline_runs.value:
        if run.pipeline_name in pipelines_of_interest:
            runs_by_pipeline[run.pipeline_name].append(run)

    user_timezone = request.args.get('timezone', 'UTC')
    local_zone = pytz.timezone(user_timezone)

    # Sort runs by last updated time and pick the latest
    latest_runs = {}
    for pipeline, runs in runs_by_pipeline.items():
        if runs:
            latest_run = sorted(runs, key=lambda x: x.last_updated, reverse=True)[0]
            local_time = latest_run.last_updated.astimezone(local_zone)
            latest_runs[pipeline] = {
                'Status': latest_run.status,
                'Last Updated': local_time.strftime("%Y-%m-%d %H:%M:%S")
            }

    return jsonify(latest_runs)

@app.route('/load-table-data/<table_name>')
def load_specific_table_data(table_name):
    conn = pyodbc.connect(DB_CONNECTION_STRING)
    cursor = conn.cursor()

    # Validate table name to prevent SQL injection
    valid_tables = [
        'Products', 'Customers', 'Employees', 'Payments', 'Transactions',
        'MonthlyCustomerMetrics', 'MonthlyEmployeeMetrics', 'MonthlyPaymentMetrics', 'MonthlyProductMetrics'
    ]
    if table_name not in valid_tables:
        return jsonify({"error": "Invalid table name"}), 400

    # Fetch first five rows from the specific table
    cursor.execute(f"SELECT TOP 5 * FROM dbo.{table_name}")
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    table_data = [dict(zip(columns, row)) for row in rows]

    return jsonify(table_data)

@app.route('/stored_procedures')
def stored_procedures():
    return render_template('stored_procedures.html')

@app.route('/list-stored-procedures')
def list_stored_procedures():
    conn = pyodbc.connect(DB_CONNECTION_STRING)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name 
        FROM sys.procedures
    """)
    procedures = [procedure[0] for procedure in cursor.fetchall()]
    return jsonify(procedures=procedures)

@app.route('/delete-stored-procedures', methods=['POST'])
def delete_stored_procedures():
    conn = pyodbc.connect(DB_CONNECTION_STRING)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name 
        FROM sys.procedures
    """)
    procedures = [procedure[0] for procedure in cursor.fetchall()]
    for procedure in procedures:
        drop_query = f"DROP PROCEDURE {procedure}"
        cursor.execute(drop_query)
    conn.commit()
    return jsonify({'status': 'success', 'message': 'All stored procedures have been deleted.'})

@app.route('/create-stored-procedures', methods=['POST'])
def create_stored_procedures():
    conn = pyodbc.connect(DB_CONNECTION_STRING)
    cursor = conn.cursor()
    sql_files = [file for file in os.listdir('scripts/StoredProcedures') if file.endswith('.sql')]
    for file in sql_files:
        with open(os.path.join('scripts/StoredProcedures', file), 'r') as f:
            sql = f.read()
            # Split the SQL script at each 'GO' command
            sql_commands = sql.split('GO')
            for command in sql_commands:
                if command.strip():  # Skip empty commands
                    cursor.execute(command)
    conn.commit()
    return jsonify({'status': 'success', 'message': 'All stored procedures have been created.'})

@app.route('/visualizations')
def visualizations():
    return render_template('visualizations.html')

@app.route('/explore_data')
def explore_data():
    return render_template('explore_data.html')

@app.route('/submit-query', methods=['POST'])
def submit_query():
    query = request.json.get('query')
    
    # Get the SQL query from the Together API
    response = client.chat.completions.create(
        model="meta-llama/Llama-3-70b-chat-hf",
        messages=[
            {"role": "system", "content": "You are a Natural Language to SQL Query Converter. The queries should be compatible with Azure SQL. Give the SQL query directly without anything else before or after. The schemas of tables are as follows - a) Transactions - transaction_id, timestamp, customer_id, product_id, employee_id, payment_id, quantity, total_amount b) Products - product_id, product_name, product_category, unit_price c) Payments - payment_id, payment_type d) Employees - employee_id, employee_name, employee_ssn, employee_phone, employee_state, employee_city, employee_postal e) Customers - customer_id, customer_first_name, customer_last_name, customer_city, customer_state, customer_postal, customer_email, customer_phone"},
            {"role": "user", "content": query},
        ],
    )

    if response and response.choices and len(response.choices) > 0:
        sql_query = response.choices[0].message.content.strip()
    else:
        return jsonify(results=[], sql_query="Error generating SQL query from the model.")

    try:
        # Execute the SQL query
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results=results, sql_query=sql_query)
    except Exception as e:
        print(str(e))
        return jsonify(results=[], sql_query=sql_query, error=str(e))

@app.route('/export-query-results', methods=['POST'])
def export_query_results():
    data = request.json.get('data')
    export_format = request.json.get('format', 'csv')  # default to CSV
    
    df = pd.DataFrame(data)
    
    if export_format == 'csv':
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(output, mimetype='text/csv', as_attachment=True, download_name='query_results.csv')
    elif export_format == 'excel':
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='query_results.xlsx')
    else:
        return jsonify({'error': 'Unsupported format'}), 400

@app.route('/save-query-history', methods=['POST'])
def save_query_history():
    history = request.json.get('history', [])
    session['query_history'] = history
    return jsonify({'status': 'success'})

@app.route('/get-query-history')
def get_query_history():
    history = session.get('query_history', [])
    return jsonify({'history': history})

@app.route('/clear-query-history', methods=['POST'])
def clear_query_history():
    session['query_history'] = []
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)