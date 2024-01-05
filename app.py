from flask import Flask, request, render_template
from azure.storage.blob import BlobServiceClient
import os

app = Flask(__name__)

# Azure Storage Account settings
CONNECTION_STRING = 'DefaultEndpointsProtocol=https;AccountName=dbprojectstorage;AccountKey=AkeELxf+2c4xT/jqAUDGI+fOD4wuU0iwb6H6ndJy+E2b56U4YMKC0540qwhTPp+oBUt1AyEP/TKo+AStNS1tNA==;EndpointSuffix=core.windows.net'
CONTAINER_NAME = 'webappstorage'

blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files_to_blob():
    uploaded_files = [
        request.files.get('products'),
        request.files.get('employees'),
        request.files.get('customers'),
        request.files.get('payments'),
        request.files.get('transactions')
    ]
    
    messages = []
    for file in uploaded_files:
        if file:
            blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=file.filename)
            blob_client.upload_blob(file)
            messages.append(f'Successfully uploaded {file.filename}!')
        else:
            messages.append('A required file was missing.')
    
    return '<br>'.join(messages)

if __name__ == '__main__':
    app.run(debug=True)
