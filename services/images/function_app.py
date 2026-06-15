import azure.functions as func
import logging
import os
import uuid
import json


from io import BytesIO
from PIL import Image
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.servicebus import ServiceBusClient, ServiceBusMessage

app = func.FunctionApp()


@app.function_name(name="upload")
@app.route(route="upload", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def upload_image(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    image_file = req.files.get("image")

    if image_file:
        try:
            connection_string = os.environ["ENV_PHOTOS_CONNSTR"]
            container_name = os.environ["ENV_PHOTOS_CONTAINER_NAME"]
            sb_connection_string = os.environ["ENV_SERVICE_BUS_CONNSTR"]
            meta_topic_name = os.environ["ENV_METADATA_NEW_IMAGE_TOPIC_NAME"]

            try:
                blob_service_client = BlobServiceClient.from_connection_string(
                    connection_string
                )
                container_client = blob_service_client.get_container_client(
                    container_name
                )
            except Exception as e:
                logging.error(f"Connection Error: {e}")
                return func.HttpResponse(
                    "Error: Unable to connect to Azure Services", status_code=500
                )

            idx = str(uuid.uuid4())
            safe_filename = f"images/{idx}.jpg"

            img = Image.open(BytesIO(image_file.read()))

            try:
                blob_client = container_client.get_blob_client(safe_filename)

                img_data = BytesIO()
                img.save(img_data, format="JPEG")
                img_data.seek(0)

                content_settings = ContentSettings(content_type="image/jpeg")

                blob_client.upload_blob(
                    img_data, overwrite=True, content_settings=content_settings
                )
            except Exception as e:
                logging.error(f"Error: {e}")
                return func.HttpResponse(
                    "Unable to upload image to Azure Storage", status_code=500
                )

            try:
                with ServiceBusClient.from_connection_string(
                    sb_connection_string
                ) as sb_client:
                    with sb_client.get_topic_sender(topic_name=meta_topic_name) as sender:
                        message_payload = {"idx": idx, "original_url": blob_client.url}
                        message = ServiceBusMessage(json.dumps(message_payload))

                        sender.send_messages(message)
                        logging.info(
                            f"Successfully sent UUID {idx} and original url to Service Bus metadata topic."
                        )
            except Exception as e:
                logging.error(f"Error while sending message to Service Bus Topic: {e}")
                return func.HttpResponse(
                    "Unable to queue the image for processing", status_code=500
                )

            return func.HttpResponse(
                f"Image '{safe_filename}' loaded successfully.", status_code=200
            )

        except Exception as e:
            logging.error(f"Error while processing an image {e}")
            return func.HttpResponse(f"{e}", status_code=500)
    else:
        return func.HttpResponse("Provide an image.", status_code=400)
