import azure.functions as func
import logging
import os
import json

from azure.data.tables import TableServiceClient
from datetime import datetime
from azure.servicebus import ServiceBusClient, ServiceBusMessage

app = func.FunctionApp()

@app.service_bus_topic_trigger(
    arg_name="msg",
    connection="ENV_SERVICE_BUS_CONNSTR",
    topic_name="%ENV_NEW_THUMBNAIL_TOPIC_NAME%",
    subscription_name="metadata-thumbnail-sub",
)
def new_thumbnail_message(msg: func.ServiceBusMessage):
    message_body = msg.get_body().decode("utf-8")
    payload = json.loads(message_body)
    
    image_id = payload["id"]
    blob_url = payload["blob_url"]
    
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
            entity['ThumbnailUrl'] = blob_url

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
    subscription_name="metadata-tags-sub",
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
    

@app.service_bus_topic_trigger(
    arg_name="msg",
    connection="ENV_SERVICE_BUS_CONNSTR",
    topic_name="%ENV_NEW_IMAGE_BLOB_TOPIC_NAME%",
    subscription_name="meta-image-blob-sub",
)
def new_image_message(msg: func.ServiceBusMessage):
    message_body = msg.get_body().decode("utf-8")
    payload = json.loads(message_body)
    idx = payload["idx"]
    original_url = payload["original_url"]

    logging.info(f"New image uploaded: {idx}")

    try:
        try:
            connection_string = os.environ['ENV_PHOTOS_CONNSTR']
            metadata_storage_name = os.environ['ENV_METADATA_STORAGE_NAME']
            sb_topic_name = os.environ["ENV_NEW_IMAGE_TOPIC_NAME"]
            sb_connection_string = os.environ["ENV_SERVICE_BUS_CONNSTR"]

            table_service_client = TableServiceClient.from_connection_string(connection_string)
            table_client = table_service_client.get_table_client(metadata_storage_name)
        except Exception as e:
            logging.error(f"Error: {e}")
            return func.HttpResponse(
                "Error: Unable to connect to Azure Storage", status_code=500
            )
        
        entity = {
            "PartitionKey": idx,
            "RowKey": idx,
            "Timestamp": datetime.now().isoformat(),
            "OriginalUrl": original_url,
            "ThumbnailUrl": "",
            "Tags": ""
        }
        
        try:
            logging.info("Upserting entity")
            table_client.upsert_entity(entity=entity)
        except Exception as e:
            logging.error(f"Error while upserting entity: {e}")
            raise e   
        
        try:
            with ServiceBusClient.from_connection_string(
                sb_connection_string
            ) as sb_client:
                with sb_client.get_topic_sender(topic_name=sb_topic_name) as sender:
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
        return None
    except Exception as e:
        logging.error(f"Error while saving metadata {idx}: {e}")
        raise e
