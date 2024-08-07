from flask import Flask, request, render_template, jsonify, send_file, session, redirect, url_for
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from azure.storage.blob import BlobServiceClient
from azure.identity import ClientSecretCredential 
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import *
from datetime import datetime, timedelta
from datetime import date
import time
import os
import pytz
import pyodbc
import requests
from together import Together
import pandas as pd
from io import BytesIO
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_url_path='', static_folder='static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Azure Storage Account settings
CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

# Azure subscription ID
subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')

# Define the connection parameters
server = os.getenv('DB_SERVER')
database = os.getenv('DB_NAME')
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')

# Azure credentials and subscription
tenant_id = os.environ.get("AZURE_TENANT_ID")
client_id = os.environ.get("AZURE_CLIENT_ID")
client_secret = os.environ.get("AZURE_CLIENT_SECRET")
subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")

# Data Factory details
resource_group = os.environ.get("AZURE_RESOURCE_GROUP")
factory_name = os.environ.get("AZURE_DATA_FACTORY_NAME")
pipeline_name = os.environ.get("AZURE_PIPELINE_NAME")

# Construct the connection string
DB_CONNECTION_STRING = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

CONTAINER_NAME = 'salesrepblob'

blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)

API_KEY = os.getenv('TOGETHER_API_KEY')
client = Together(api_key=API_KEY)

credential = ClientSecretCredential(tenant_id, client_id, client_secret)
adf_client = DataFactoryManagementClient(credential, subscription_id)

pipelines_of_interest = [
    'IngestProducts',
    'IngestPayments',
    'IngestCustomers',
    'IngestEmployees',
    'IngestTransactions',
    'CalculateMonthlyCustomerMetrics',
    'CalculateMonthlyProductMetrics',
    'CalculateMonthlyPaymentMetrics',
    'CalculateMonthlyEmployeeMetrics'
    ]


def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0]
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    else:
        ip = request.remote_addr
    
    # Remove the port if it's present
    ip = ip.split(':')[0]
    return ip

def get_or_create_ip_record(cursor, ip_address):
    today = date.today()
        
    # Try to get the existing record
    cursor.execute("""
        SELECT query_count, last_query_date
        FROM IPQueryTracking
        WHERE ip_address = ?
    """, ip_address)
    
    record = cursor.fetchone()
    
    if record:
        query_count, last_query_date = record
        if last_query_date != today:
            cursor.execute("""
                UPDATE IPQueryTracking
                SET query_count = 0, last_query_date = ?
                WHERE ip_address = ?
            """, today, ip_address)
            return 0
        return query_count
    else:
        cursor.execute("""
            INSERT INTO IPQueryTracking (ip_address, query_count, last_query_date)
            VALUES (?, 0, ?)
        """, ip_address, today)
        return 0

def check_query_limit():
    ip_address = get_client_ip()
    
    conn = pyodbc.connect(DB_CONNECTION_STRING)
    cursor = conn.cursor()
    
    try:
        query_count = get_or_create_ip_record(cursor, ip_address)
                
        if query_count >= 10:
            return False
        
        # Increment the query count
        cursor.execute("""
            UPDATE IPQueryTracking
            SET query_count = query_count + 1
            WHERE ip_address = ?
        """, ip_address)
        
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        cursor.close()
        conn.close()


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
    if not check_query_limit():
        return jsonify(error="Daily query limit reached. Please try again tomorrow."), 429

    query = request.json.get('query')
    
    # Add the Azure SQL compatibility instruction to the user query
    azure_sql_query = f"{query} (Make sure the SQL query generated is compatible with Azure SQL)"

    # Get the SQL query from the Together API
    response = client.chat.completions.create(
        model="meta-llama/Llama-3-70b-chat-hf",
        messages=[
            {"role": "system", "content": "You are a Natural Language to SQL Query Converter. The queries should be compatible with Azure SQL. Give the SQL query directly without anything else before or after. The schemas of tables are as follows - a) Transactions - transaction_id, timestamp, customer_id, product_id, employee_id, payment_id, quantity, total_amount b) Products - product_id, product_name, product_category, unit_price c) Payments - payment_id, payment_type d) Employees - employee_id, employee_name, employee_ssn, employee_phone, employee_state, employee_city, employee_postal e) Customers - customer_id, customer_first_name, customer_last_name, customer_city, customer_state, customer_postal, customer_email, customer_phone"},
            {"role": "user", "content": azure_sql_query},
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

@app.route('/get-remaining-queries')
def get_remaining_queries():
    ip_address = get_client_ip()
    
    conn = pyodbc.connect(DB_CONNECTION_STRING)
    cursor = conn.cursor()
    
    try:
        query_count = get_or_create_ip_record(cursor, ip_address)
        remaining = max(0, 10 - query_count)
        return jsonify(remaining=remaining)
    except Exception as e:
        return jsonify(error="An error occurred"), 500
    finally:
        cursor.close()
        conn.close()

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

def suggest_chart_type(data):
    if len(data) == 0:
        return None
    
    columns = list(data[0].keys())
    
    if len(columns) == 2:
        if isinstance(data[0][columns[1]], (int, float)):
            return 'bar'
        else:
            return 'pie'
    elif len(columns) > 2:
        numeric_columns = sum(isinstance(data[0][col], (int, float)) for col in columns)
        if numeric_columns >= 2:
            return 'line'
        else:
            return 'bar'
    
    return None

@app.route('/suggest-chart', methods=['POST'])
def suggest_chart():
    data = request.json.get('data', [])
    chart_type = suggest_chart_type(data)
    return jsonify({'chartType': chart_type})

# Add this new route for the landing page
@app.route('/files')
def landing():
    return render_template('files.html')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # In a real application, you would check these credentials against a database
        # For this example, we'll use hardcoded credentials
        if username == 'admin' and check_password_hash(generate_password_hash('password123'), password):
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html')

@app.route('/run-edited-sql', methods=['POST'])
def run_edited_sql():

    sql_query = request.json.get('sql')
    
    try:
        # Execute the SQL query
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify(results=results)
    except Exception as e:
        print(str(e))
        return jsonify(error=str(e))

@app.route('/data_flow')
def data_flow():
    return render_template('data_flow.html')

@app.route('/pipeline-status')
def pipeline_status():
    pipeline_runs = adf_client.pipeline_runs.query_by_factory(
        resource_group,
        factory_name,
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

if __name__ == '__main__':
    app.run(debug=True)