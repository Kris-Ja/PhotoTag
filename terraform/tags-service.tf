resource "azurerm_storage_container" "tags_service" {
  name                  = "tags-service"
  storage_account_id    = azurerm_storage_account.images.id
  container_access_type = "private"
}

resource "azurerm_service_plan" "cognitive_service_plan" {
  name                = "cognitive-service-plan"
  location            = azurerm_resource_group.phototag.location
  resource_group_name = azurerm_resource_group.phototag.name
  os_type             = "Linux"
  sku_name            = "FC1"
}

resource "azurerm_cognitive_account" "cognitive_acc" {
  name                = "cognitive-acc"
  location            = azurerm_resource_group.phototag_cognitive.location
  resource_group_name = azurerm_resource_group.phototag_cognitive.name
  sku_name            = "S0"
  kind                = "CognitiveServices"
}

resource "azurerm_function_app_flex_consumption" "tags_service" {
  name                = lower("tags-service${random_id.random.hex}")
  resource_group_name = azurerm_resource_group.phototag.name
  location            = azurerm_resource_group.phototag.location
  service_plan_id     = azurerm_service_plan.cognitive_service_plan.id

  storage_container_type        = "blobContainer"
  storage_container_endpoint    = "${azurerm_storage_account.images.primary_blob_endpoint}${azurerm_storage_container.tags_service.name}"
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
    ENV_PHOTOS_CONNSTR                   = azurerm_storage_account.images.primary_connection_string
    ENV_PHOTOS_CONTAINER_NAME            = azurerm_storage_container.images.name
    ENV_SERVICE_BUS_CONNSTR              = azurerm_servicebus_namespace.servicebus.default_primary_connection_string
    ENV_SERVICE_BUS_NEW_IMAGE_TOPIC_NAME = azurerm_servicebus_topic.new_image.name
    ENV_SERVICE_BUS_NEW_TAGS_TOPIC_NAME  = azurerm_servicebus_topic.new_tags.name
    ENV_COGNITIVE_KEY                    = azurerm_cognitive_account.cognitive_acc.primary_access_key
    ENV_COGNITIVE_ENDPOINT               = azurerm_cognitive_account.cognitive_acc.endpoint
  }
}

resource "azurerm_servicebus_subscription" "tags_sub" {
  name               = "tags-sub"
  topic_id           = azurerm_servicebus_topic.new_image.id
  max_delivery_count = 5
}

output "tags_service_name" {
  value = azurerm_function_app_flex_consumption.tags_service.name
}
