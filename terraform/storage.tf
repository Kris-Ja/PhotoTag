resource "azurerm_storage_account" "images" {
  name                     = "images"
  resource_group_name      = azurerm_resource_group.phototag.name
  location                 = azurerm_resource_group.phototag.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "images" {
  name                  = "images-container"
  storage_account_id    = azurerm_storage_account.images.id
  container_access_type = "private"
}
