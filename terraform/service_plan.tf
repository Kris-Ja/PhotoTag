resource "azurerm_service_plan" "service_plan" {
  name                = "service-plan"
  location            = azurerm_resource_group.phototag.location
  resource_group_name = azurerm_resource_group.phototag.name
  os_type             = "Linux"
  sku_name            = "FC1"
}

resource "azurerm_service_plan" "congnitive_service_plan" {
  name                = "cognitive-service-plan"
  location            = azurerm_resource_group.phototag.location
  resource_group_name = azurerm_resource_group.phototag.name
  os_type             = "Linux"
  sku_name            = "FC1"
}

resource "azurerm_service_plan" "thumbnails_service_plan" {
  name                = "thumbnails-service-plan"
  location            = azurerm_resource_group.phototag.location
  resource_group_name = azurerm_resource_group.phototag.name
  os_type             = "Linux"
  sku_name            = "FC1"
}
