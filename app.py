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
def upload_file_to_blob():
    file = request.files['file']
    if file:
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=file.filename)
        blob_client.upload_blob(file)
        return 'File successfully uploaded!'
    return 'No file selected for uploading'

if __name__ == '__main__':
    app.run(debug=True)