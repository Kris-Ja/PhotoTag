resource "azurerm_function_app_flex_consumption" "images_service" {
  name                = "images-service"
  resource_group_name = azurerm_resource_group.phototag.name
  location            = azurerm_resource_group.phototag.location
  service_plan_id     = azurerm_service_plan.service_plan.id

  storage_container_type      = "blobContainer"
  storage_container_endpoint  = "${azurerm_storage_account.images.primary_blob_endpoint}${azurerm_storage_container.images.name}"
  storage_authentication_type = "StorageAccountConnectionString"
  storage_access_key          = azurerm_storage_account.images.primary_access_key
  runtime_name                = "python"
  runtime_version             = "3.13"
  maximum_instance_count      = 5
  instance_memory_in_mb       = 512

  site_config {
  }

  app_settings = {
    ENV_PHOTOS_CONNSTR        = azurerm_storage_account.images.primary_connection_string
    ENV_PHOTOS_CONTAINER_NAME = azurerm_storage_container.images.name
  }
}
