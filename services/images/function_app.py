import azure.functions as func
import logging
import os
import uuid
import json

from datetime import datetime, timezone, timedelta
from io import BytesIO
from PIL import Image
from azure.data.tables import TableServiceClient
from azure.storage.blob import BlobServiceClient, ContentSettings, BlobSasPermissions, generate_blob_sas
from azure.servicebus import ServiceBusClient, ServiceBusMessage

app = func.FunctionApp()

def generate_sas_url(container_name, blob_name, account_name, account_key):
    sas_token = generate_blob_sas(
        account_name = account_name,
        container_name = container_name,
        blob_name = blob_name,
        account_key = account_key,
        permission = BlobSasPermissions(read=True),
        expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    )
    return f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
                

@app.function_name(name="get_images")
@app.route(route="images", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
def get_images(req: func.HttpRequest) -> func.HttpResponse:
    try:
        connection_string = os.environ["ENV_PHOTOS_CONNSTR"]
        metadata_storage_name = os.environ['ENV_METADATA_STORAGE_NAME']
        container_name = os.environ["ENV_PHOTOS_CONTAINER_NAME"]

        conn_dict = dict(kv.split("=", 1) for kv in connection_string.split(";") if kv)
        account_name = conn_dict.get("AccountName")
        account_key = conn_dict.get("AccountKey")

        table_service_client = TableServiceClient.from_connection_string(connection_string)
        table_client = table_service_client.get_table_client(metadata_storage_name)
        
        entities = table_client.list_entities()
        
        results = []

        for entity in entities:
            idx = entity.get("RowKey")
            url = None
            tags = []
            timestamp = None
            
            timestamp_val = entity.get("Timestamp")
            if timestamp_val:
                timestamp = timestamp_val
            
            thumbnail_path = entity.get("ThumbnailPath")
            if thumbnail_path:
                blob_name = thumbnail_path
                url = generate_sas_url(container_name, blob_name, account_name, account_key) 

            tags_string = entity.get("Tags")
            if tags_string:
                tags = [s.strip() for s in tags_string.split(",") if s.strip()]

            results.append({
                "id": idx, 
                "url": url,
                "tags": tags,
                "created_at": timestamp
            })

        return func.HttpResponse(
            body=json.dumps(results),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error while getting data: {e}")
        return func.HttpResponse("Error while getting data", status_code=500)

@app.function_name(name="get_image")
@app.route(route="images/{id}", auth_level=func.AuthLevel.FUNCTION, methods=["GET"])
def get_image(req: func.HttpRequest) -> func.HttpResponse:
    try:
        idx = req.route_params.get("id")
        if not idx:
            return func.HttpResponse(
                "No image id in route params",
                status_code=400
            )
        connection_string = os.environ["ENV_PHOTOS_CONNSTR"]
        metadata_storage_name = os.environ['ENV_METADATA_STORAGE_NAME']
        container_name = os.environ["ENV_PHOTOS_CONTAINER_NAME"]

        conn_dict = dict(kv.split("=", 1) for kv in connection_string.split(";") if kv)
        account_name = conn_dict.get("AccountName")
        account_key = conn_dict.get("AccountKey")

        table_service_client = TableServiceClient.from_connection_string(connection_string)
        table_client = table_service_client.get_table_client(metadata_storage_name)
        
        try:
            entity = table_client.get_entity(idx, idx)
            if not entity:
                return func.HttpResponse(
                    f"Image with id {idx} not found",
                    status_code=400
                )
        except Exception as e:
            return func.HttpResponse(
                f"Image with id {idx} not found",
                status_code=400
            )
        
        url = None
        tags = []
        timestamp = None
        
        timestamp_val = entity.get("Timestamp")
        if timestamp_val:
            timestamp = timestamp_val
        
        image_path = entity.get("ImagePath")
        if image_path:
            blob_name = image_path
            url = generate_sas_url(container_name, blob_name, account_name, account_key) 

        tags_string = entity.get("Tags")
        if tags_string:
            tags = [s.strip() for s in tags_string.split(",") if s.strip()]

        result = {
            "id": idx, 
            "url": url,
            "tags": tags,
            "created_at": timestamp
        }

        return func.HttpResponse(
            body=json.dumps(result),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error while getting data: {e}")
        return func.HttpResponse("Error while getting data", status_code=500)

@app.function_name(name="upload_image")
@app.route(route="images", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def upload_image(req: func.HttpRequest) -> func.HttpResponse:

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
