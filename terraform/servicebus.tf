resource "azurerm_servicebus_namespace" "servicebus" {
  name                = "servicebus${random_id.servicebus.hex}"
  location            = azurerm_resource_group.phototag.location
  resource_group_name = azurerm_resource_group.phototag.name
  sku                 = "Standard"
}

resource "azurerm_servicebus_topic" "new_image" {
  name         = "new-image"
  namespace_id = azurerm_servicebus_namespace.servicebus.id
}

resource "azurerm_servicebus_topic" "new_thumbnail" {
  name         = "new-thumbnail"
  namespace_id = azurerm_servicebus_namespace.servicebus.id
}

resource "azurerm_servicebus_topic" "new_tags" {
  name         = "new-tags"
  namespace_id = azurerm_servicebus_namespace.servicebus.id
}

output "servicebus_connection_string" {
  value     = azurerm_servicebus_namespace.servicebus.default_primary_connection_string
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
