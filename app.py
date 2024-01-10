from flask import Flask, request, render_template, jsonify
from azure.storage.blob import BlobServiceClient
import os

app = Flask(__name__)

# Azure Storage Account settings
CONNECTION_STRING = 'DefaultEndpointsProtocol=https;AccountName=salesrepstorageacc;AccountKey=7VFqRFCzw+o5Dg4iTmFcClNkhDndSTNGKE1YcdFlVhxbrWP/q0JWOS4VDZvgVezQLcw8WK4KEj7I+ASts2Kh/A==;EndpointSuffix=core.windows.net'
CONTAINER_NAME = 'salesrepcontainerlocal'

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
            blob_client.upload_blob(file)
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


if __name__ == '__main__':
    app.run(debug=True)
