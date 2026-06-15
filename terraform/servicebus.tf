resource "azurerm_servicebus_namespace" "image_namespace" {
  name                = "phototag-servicebus${random_id.servicebus.hex}"
  location            = azurerm_resource_group.phototag.location
  resource_group_name = azurerm_resource_group.phototag.name
  sku                 = "Standard"
}

resource "azurerm_servicebus_topic" "image_topic" {
  name         = "image-uploaded-topic"
  namespace_id = azurerm_servicebus_namespace.image_namespace.id
}

resource "azurerm_servicebus_subscription" "thumbnail_subscriber" {
  name               = "thumbnail_subscriber"
  topic_id           = azurerm_servicebus_topic.image_topic.id
  max_delivery_count = 5
}

output "servicebus_connection_string" {
  value     = azurerm_servicebus_namespace.image_namespace.default_primary_connection_string
  sensitive = true
}

output "servicebus_topic_name" {
  value       = azurerm_servicebus_topic.image_topic.name
  description = "Name of topic where python send messages"
}