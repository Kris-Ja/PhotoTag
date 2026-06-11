import azure.functions as func
import logging
import os
import uuid

from io import BytesIO
from PIL import Image
from azure.storage.blob import BlobServiceClient, ContentSettings

app = func.FunctionApp()

@app.function_name(name="upload")
@app.route(route="upload", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def upload_image(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    image_file = req.files.get('image')

    if image_file:
        try:
            connection_string = os.environ['ENV_PHOTOS_CONNSTR']
            container_name = os.environ['ENV_PHOTOS_CONTAINER_NAME']

            try:
                blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            except Exception as e:
                logging.error(f"Error: {e}")
                return func.HttpResponse(
                    "Error: Unable to connect to Azure Storage", status_code=500
                )
            
            img = Image.open(BytesIO(image_file.read()))
      
            container_client = blob_service_client.get_container_client(container_name)

            idx = str(uuid.uuid4())
            safe_filename = f"{idx}.jpg"

            blob_client = container_client.get_blob_client(safe_filename)
            
            img_data = BytesIO()
            img.save(img_data, format='JPEG')
            img_data.seek(0)
            
            content_settings = ContentSettings(content_type='image/jpeg')
            
            blob_client.upload_blob(img_data, overwrite=True, content_settings=content_settings)

            return func.HttpResponse(
                f"Image '{safe_filename}' loaded successfully.", 
                status_code=200
            )
            
        except Exception as e:
            logging.error(f"Error while processing an image {e}")
            return func.HttpResponse(f"Server error: {e}", status_code=500)
    else:
        return func.HttpResponse(
            "Provide an image.",
            status_code=400
        )