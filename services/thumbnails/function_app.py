import azure.functions as func
import logging
import os
import json

from io import BytesIO
from PIL import Image
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.servicebus import ServiceBusClient, ServiceBusMessage

app = func.FunctionApp()


@app.service_bus_topic_trigger(
    arg_name="msg",
    connection="ENV_SERVICE_BUS_CONNSTR", 
    topic_name="%ENV_SERVICE_BUS_NEW_IMAGE_TOPIC_NAME%",
    subscription_name="thumbnails-subscription" 
)
def generate_thumbnail(msg: func.ServiceBusMessage):
    idx = msg.get_body().decode("utf-8")
    logging.info(f"Receive a message to create a thumbnail: {idx}")

    try:
        connection_string = os.environ['ENV_PHOTOS_CONNSTR']
        container_name = os.environ['ENV_PHOTOS_CONTAINER_NAME']
        sb_connection_string = os.environ['ENV_SERVICE_BUS_CONNSTR']
        sb_new_thumbnail_topic_name = os.environ['ENV_SERVICE_BUS_NEW_THUMBNAIL_TOPIC_NAME']

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)

        original_filename = f"images/{idx}.jpg"
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

        thumbnail_filename = f"thumbnails/{idx}_thumbnail.jpg"
        thumbnail_blob_client = container_client.get_blob_client(thumbnail_filename)
        
        content_settings = ContentSettings(content_type='image/jpeg')
        thumbnail_blob_client.upload_blob(
            thumbnail_data, 
            overwrite=True, 
            content_settings=content_settings
        )

        logging.info(f"Success! Saved thumbnail as {thumbnail_filename}.")

        try:
            with ServiceBusClient.from_connection_string(sb_connection_string) as sb_client:
                with sb_client.get_topic_sender(topic_name=sb_new_thumbnail_topic_name) as sender:

                    message_payload = {
                        "id": idx,
                        "blob_url": thumbnail_blob_client.url
                    }

                    message = ServiceBusMessage(json.dumps(message_payload))

                    sender.send_messages(message)
                    logging.info(f"Successfully sent UUID {idx} and blob url to Service Bus topic.")
                    
        except Exception as e:
            logging.error(f"Error while sending message to Service Bus Topic: {e}")
            return func.HttpResponse("Unable to queue the image for processing", status_code=500)

    except Exception as e:
        logging.error(f"Error while changing image {idx}: {e}")
        raise e
