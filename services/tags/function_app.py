import azure.functions as func
import logging
import os
import json

from io import BytesIO
from azure.storage.blob import BlobServiceClient
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from azure.servicebus import ServiceBusClient, ServiceBusMessage

app = func.FunctionApp()


@app.service_bus_topic_trigger(
    arg_name="msg",
    connection="ENV_SERVICE_BUS_CONNSTR",
    topic_name="%ENV_SERVICE_BUS_NEW_IMAGE_TOPIC_NAME%",
    subscription_name="tags-subscription",
)
def generate_tags(msg: func.ServiceBusMessage):
    idx = msg.get_body().decode("utf-8")
    logging.info(f"Receive a message generate tags: {idx}")

    try:
        connection_string = os.environ["ENV_PHOTOS_CONNSTR"]
        container_name = os.environ["ENV_PHOTOS_CONTAINER_NAME"]
        congnitive_endpoint = os.environ["ENV_COGNITIVE_ENDPOINT"]
        cognitive_key = os.environ["ENV_COGNITIVE_KEY"]
        sb_connection_string = os.environ["ENV_SERVICE_BUS_CONNSTR"]
        sb_new_tags_topic_name = os.environ["ENV_SERVICE_BUS_NEW_TAGS_TOPIC_NAME"]

        try:
            blob_service_client = BlobServiceClient.from_connection_string(
                connection_string
            )
            container_client = blob_service_client.get_container_client(container_name)

            credentials = CognitiveServicesCredentials(cognitive_key)
            cv_service_client = ComputerVisionClient(congnitive_endpoint, credentials)
        except Exception as e:
            logging.error(f"Error: {e}")
            raise e

        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )
        container_client = blob_service_client.get_container_client(container_name)

        original_filename = f"images/{idx}.jpg"
        blob_client = container_client.get_blob_client(original_filename)

        logging.info(f"Dowloading file {original_filename} from container...")
        download_stream = blob_client.download_blob()
        image_data = download_stream.readall()

        try:
            tags = []
            analysis = cv_service_client.analyze_image_in_stream(
                BytesIO(image_data), [VisualFeatureTypes.tags]
            )
            for tag in analysis.tags:
                if tag.confidence > 0.9:
                    tags.append(tag.name)
        except Exception as e:
            logging.error(f"Error: {e}")
            raise e

        try:
            with ServiceBusClient.from_connection_string(
                sb_connection_string
            ) as sb_client:
                with sb_client.get_topic_sender(
                    topic_name=sb_new_tags_topic_name
                ) as sender:
                    message_payload = {"id": idx, "tags": tags}

                    message = ServiceBusMessage(json.dumps(message_payload))

                    sender.send_messages(message)
                    logging.info(
                        f"Successfully sent UUID {idx} and tags {tags} to Service Bus topic."
                    )
        except Exception as e:
            logging.error(f"Error while sending message to Service Bus Topic: {e}")
            raise e

    except Exception as e:
        logging.error(f"Error while processing image {idx}: {e}")
        raise e
