import azure.functions as func
import logging
import os
import uuid
import json

from datetime import datetime
from io import BytesIO
from PIL import Image
from azure.data.tables import TableServiceClient
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.servicebus import ServiceBusClient, ServiceBusMessage

app = func.FunctionApp()


@app.function_name(name="upload_image")
@app.route(route="images", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def upload_image(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    image_file = req.files.get("image")

    if image_file:
        try:
            connection_string = os.environ["ENV_PHOTOS_CONNSTR"]
            metadata_storage_name = os.environ['ENV_METADATA_STORAGE_NAME']
            photos_container_name = os.environ["ENV_PHOTOS_CONTAINER_NAME"]
            sb_connection_string = os.environ["ENV_SERVICE_BUS_CONNSTR"]
            topic_name = os.environ["ENV_NEW_IMAGE_TOPIC_NAME"]

            try:
                blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                container_client = blob_service_client.get_container_client(photos_container_name)
                table_service_client = TableServiceClient.from_connection_string(connection_string)
                table_client = table_service_client.get_table_client(metadata_storage_name)

            except Exception as e:
                logging.error(f"Connection Error: {e}")
                return func.HttpResponse(
                    "Error: Unable to connect to Azure Services", status_code=500
                )

            idx = str(uuid.uuid4())
            filename = f"images/{idx}.jpg"

            img = Image.open(BytesIO(image_file.read()))

            try:
                blob_client = container_client.get_blob_client(filename)

                img_data = BytesIO()
                img.save(img_data, format="JPEG")
                img_data.seek(0)

                content_settings = ContentSettings(content_type="image/jpeg")

                blob_client.upload_blob(img_data, content_settings=content_settings)
            except Exception as e:
                logging.error(f"Error: {e}")
                return func.HttpResponse(
                    "Unable to upload image to Azure Storage", status_code=500
                )

            entity = {
                "PartitionKey": idx,
                "RowKey": idx,
                "Timestamp": datetime.now().isoformat(),
                "ImagePath": filename,
                "ThumbnailPath": "",
                "Tags": ""
            }
            
            try:
                logging.info("Upserting entity")
                table_client.upsert_entity(entity=entity)
            except Exception as e:
                logging.error(f"Error while upserting entity: {e}")
                return func.HttpResponse(
                    "Unable to upload image to Azure Storage", status_code=500
                )

            try:
                with ServiceBusClient.from_connection_string(
                    sb_connection_string
                ) as sb_client:
                    with sb_client.get_topic_sender(topic_name=topic_name) as sender:
                        message = ServiceBusMessage(idx)

                        sender.send_messages(message)
                        logging.info(
                            f"Successfully sent UUID {idx} to Service Bus topic."
                        )
            except Exception as e:
                logging.error(f"Error while sending message to Service Bus Topic: {e}")
                return func.HttpResponse(
                    "Unable to queue the image for processing", status_code=500
                )

            return func.HttpResponse(
                f"Image '{filename}' loaded successfully.", status_code=200
            )

        except Exception as e:
            logging.error(f"Error while processing an image {e}")
            return func.HttpResponse(f"{e}", status_code=500)
    else:
        return func.HttpResponse("Provide an image.", status_code=400)

@app.service_bus_topic_trigger(
    arg_name="msg",
    connection="ENV_SERVICE_BUS_CONNSTR",
    topic_name="%ENV_NEW_THUMBNAIL_TOPIC_NAME%",
    subscription_name="new-thumbnail-sub",
)
def new_thumbnail_message(msg: func.ServiceBusMessage):
    message_body = msg.get_body().decode("utf-8")
    payload = json.loads(message_body)
    
    image_id = payload["id"]
    blob_name = payload["blob_name"]
    
    logging.info(f"Thumbnail was created message: {image_id}")

    try:
        try:
            connection_string = os.environ['ENV_PHOTOS_CONNSTR']
            metadata_storage_name = os.environ['ENV_METADATA_STORAGE_NAME']

            table_service_client = TableServiceClient.from_connection_string(connection_string)
            table_client = table_service_client.get_table_client(metadata_storage_name)
        except Exception as e:
            logging.error(f"Error: {e}")
            return func.HttpResponse(
                "Error: Unable to connect to Azure Storage", status_code=500
            )
        
        entity = None
        try:
            entity = table_client.get_entity(partition_key=image_id, row_key=image_id)
        except Exception as e:
            logging.error(f"Error while getting entity: {e}")
            raise e
        
        if entity is None:
            return
        else:
            entity['ThumbnailPath'] = blob_name

        try:
            logging.info("Upserting entity")
            table_client.upsert_entity(entity=entity)
        except Exception as e:
            logging.error(f"Error while upserting entity: {e}")
            raise e   
    except Exception as e:
        logging.error(f"Error while saving metadata {image_id}: {e}")
        raise e
    
    return None

@app.service_bus_topic_trigger(
    arg_name="msg",
    connection="ENV_SERVICE_BUS_CONNSTR",
    topic_name="%ENV_NEW_TAGS_TOPIC_NAME%",
    subscription_name="new-tags-sub",
)
def new_tags_message(msg: func.ServiceBusMessage):
    message_body = msg.get_body().decode("utf-8")
    payload = json.loads(message_body)

    image_id = payload["id"]
    tags = payload["tags"]
    
    logging.info(f"Tags was generated message: {image_id}")

    try:
        try:
            connection_string = os.environ['ENV_PHOTOS_CONNSTR']
            metadata_storage_name = os.environ['ENV_METADATA_STORAGE_NAME']

            table_service_client = TableServiceClient.from_connection_string(connection_string)
            table_client = table_service_client.get_table_client(metadata_storage_name)
        except Exception as e:
            logging.error(f"Error: {e}")
            return func.HttpResponse(
                "Error: Unable to connect to Azure Storage", status_code=500
            )
        
        entity = None
        try:
            entity = table_client.get_entity(partition_key=image_id, row_key=image_id)
        except Exception as e:
            logging.error(f"Error while getting entity: {e}")
            raise e
        
        if entity is None:
            return
        else:
            entity['Tags'] = ";".join(tags)

        try:
            logging.info("Upserting entity")
            table_client.upsert_entity(entity=entity)
        except Exception as e:
            logging.error(f"Error while upserting entity: {e}")
            raise e   
    except Exception as e:
        logging.error(f"Error while saving metadata {image_id}: {e}")
        raise e
    
    return None
