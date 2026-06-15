resource "azurerm_servicebus_namespace" "image_namespace" {
  name                = "phototag-servicebus${random_id.servicebus.hex}"
  location            = azurerm_resource_group.phototag.location
  resource_group_name = azurerm_resource_group.phototag.name
  sku                 = "Standard"
}

resource "azurerm_servicebus_topic" "new_image" {
  name         = "new-image"
  namespace_id = azurerm_servicebus_namespace.image_namespace.id
}

resource "azurerm_servicebus_subscription" "thumbnail_subscriber" {
  name               = "thumbnail-subscriber"
  topic_id           = azurerm_servicebus_topic.new_image.id
  max_delivery_count = 5
}

resource "azurerm_servicebus_subscription" "tags_subscriber" {
  name               = "tags-subscriber"
  topic_id           = azurerm_servicebus_topic.new_image.id
  max_delivery_count = 5
}

resource "azurerm_servicebus_topic" "new_thumbnail" {
  name         = "new-thumbnail"
  namespace_id = azurerm_servicebus_namespace.image_namespace.id
}

resource "azurerm_servicebus_topic" "new_tags" {
  name         = "new-tags"
  namespace_id = azurerm_servicebus_namespace.image_namespace.id
}

output "servicebus_connection_string" {
  value     = azurerm_servicebus_namespace.image_namespace.default_primary_connection_string
  sensitive = true
}

output "servicebus_new_image_topic" {
  value       = azurerm_servicebus_topic.new_image.name
  description = "Name of topic where python send messages"
}

output "servicebus_new_thumbnail_topic" {
  value       = azurerm_servicebus_topic.new_thumbnail.name
  description = "Name of topic where python send messages"
}

output "servicebus_new_tags_topic" {
  value       = azurerm_servicebus_topic.new_tags.name
  description = "Name of topic where python send messages"
}