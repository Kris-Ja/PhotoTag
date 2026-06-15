import azure.functions as func
import logging
import os

from io import BytesIO
from PIL import Image
from azure.storage.blob import BlobServiceClient, ContentSettings

app = func.FunctionApp()


@app.service_bus_topic_trigger(
    arg_name="msg",
    connection="ENV_SERVICE_BUS_CONNSTR", 
    topic_name="%ENV_SERVICE_BUS_TOPIC_NAME%",
    subscription_name="thumbnail_subscriber" 
)
def generate_thumbnail(msg: func.ServiceBusMessage):
    image_id = msg.get_body().decode('utf-8')
    logging.info(f"Receive a message to create a thumbnail: {image_id}")

    try:
        connection_string = os.environ['ENV_PHOTOS_CONNSTR']
        container_name = os.environ['ENV_PHOTOS_CONTAINER_NAME']

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)

        original_filename = f"{image_id}.jpg"
        blob_client = container_client.get_blob_client(original_filename)
        
        logging.info(f"Dowloading file {original_filename} from container...")
        download_stream = blob_client.download_blob()
        image_data = download_stream.readall()

        img = Image.open(BytesIO(image_data))
        
        max_size = (200, 200) 
        img.thumbnail(max_size)
        
        thumbnail_data = BytesIO()
        img.save(thumbnail_data, format='JPEG')
        thumbnail_data.seek(0) 
        thumbnail_filename = f"{image_id}_thumbnail.jpg"
        thumbnail_blob_client = container_client.get_blob_client(thumbnail_filename)
        
        content_settings = ContentSettings(content_type='image/jpeg')
        thumbnail_blob_client.upload_blob(
            thumbnail_data, 
            overwrite=True, 
            content_settings=content_settings
        )

        logging.info(f"Success! Saved thumbnail as {thumbnail_filename}.")

    except Exception as e:
        logging.error(f"Error while changing image {image_id}: {e}")
        raise e