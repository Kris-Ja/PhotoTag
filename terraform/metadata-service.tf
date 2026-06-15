resource "azurerm_storage_container" "metadata_service" {
  name                  = "metadata-service"
  storage_account_id    = azurerm_storage_account.images.id
  container_access_type = "private"
}

resource "azurerm_storage_table" "metadata" {
  name                 = "metadata"
  storage_account_name = azurerm_storage_account.images.name
}

resource "azurerm_function_app_flex_consumption" "metadata_service" {
  name                = lower("metadata-service${random_id.random.hex}")
  resource_group_name = azurerm_resource_group.phototag.name
  location            = azurerm_resource_group.phototag.location
  service_plan_id     = azurerm_service_plan.metadata_service_plan.id

  storage_container_type        = "blobContainer"
  storage_container_endpoint    = "${azurerm_storage_account.images.primary_blob_endpoint}${azurerm_storage_container.metadata_service.name}"
  storage_authentication_type   = "StorageAccountConnectionString"
  storage_access_key            = azurerm_storage_account.images.primary_access_key
  runtime_name                  = "python"
  runtime_version               = "3.13"
  maximum_instance_count        = 5
  instance_memory_in_mb         = 512
  public_network_access_enabled = true

  site_config {
  }

  app_settings = {
    ENV_PHOTOS_CONNSTR            = azurerm_storage_account.images.primary_connection_string
    ENV_SERVICE_BUS_CONNSTR       = azurerm_servicebus_namespace.servicebus.default_primary_connection_string
    ENV_NEW_IMAGE_TOPIC_NAME      = azurerm_servicebus_topic.new_image.name
    ENV_NEW_IMAGE_BLOB_TOPIC_NAME = azurerm_servicebus_topic.new_image_blob.name
    ENV_NEW_THUMBNAIL_TOPIC_NAME  = azurerm_servicebus_topic.new_thumbnail.name
    ENV_NEW_TAGS_TOPIC_NAME       = azurerm_servicebus_topic.new_tags.name
    ENV_METADATA_STORAGE_NAME     = azurerm_storage_table.metadata.name
  }
}

resource "azurerm_servicebus_subscription" "metadata_tags_sub" {
  name               = "metadata-tags-sub"
  topic_id           = azurerm_servicebus_topic.new_tags.id
  max_delivery_count = 5
}

resource "azurerm_servicebus_subscription" "metadata_image_blob_sub" {
  name               = "metadata-image-blob-sub"
  topic_id           = azurerm_servicebus_topic.new_image_blob.id
  max_delivery_count = 5
}

resource "azurerm_servicebus_subscription" "metadata_thumbnail_sub" {
  name               = "metadata-thumbnail-sub"
  topic_id           = azurerm_servicebus_topic.new_thumbnail.id
  max_delivery_count = 5
}
