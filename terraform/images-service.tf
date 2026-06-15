resource "azurerm_storage_container" "images_service" {
  name                  = "images-service"
  storage_account_id    = azurerm_storage_account.images.id
  container_access_type = "private"
}

resource "azurerm_function_app_flex_consumption" "images_service" {
  name                = lower("images-service${random_id.random.hex}")
  resource_group_name = azurerm_resource_group.phototag.name
  location            = azurerm_resource_group.phototag.location
  service_plan_id     = azurerm_service_plan.service_plan.id

  storage_container_type      = "blobContainer"
  storage_container_endpoint  = "${azurerm_storage_account.images.primary_blob_endpoint}${azurerm_storage_container.images_service.name}"
  storage_authentication_type = "StorageAccountConnectionString"
  storage_access_key          = azurerm_storage_account.images.primary_access_key
  runtime_name                = "python"
  runtime_version             = "3.13"
  maximum_instance_count      = 5
  instance_memory_in_mb       = 512

  site_config {
  }

  app_settings = {
    ENV_PHOTOS_CONNSTR            = azurerm_storage_account.images.primary_connection_string
    ENV_PHOTOS_CONTAINER_NAME     = azurerm_storage_container.images.name
    ENV_SERVICE_BUS_CONNSTR       = azurerm_servicebus_namespace.servicebus.default_primary_connection_string
    ENV_NEW_IMAGE_BLOB_TOPIC_NAME = azurerm_servicebus_topic.new_image_blob.name
  }
}

data "azurerm_function_app_host_keys" "images_service" {
  name                = azurerm_function_app_flex_consumption.images_service.name
  resource_group_name = azurerm_function_app_flex_consumption.images_service.resource_group_name
}

output "images_service_name" {
  value = azurerm_function_app_flex_consumption.images_service.name
}
