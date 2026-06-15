resource "azurerm_storage_account" "images" {
  name                     = lower("images${random_id.random.hex}")
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

resource "azurerm_storage_table" "metadata" {
  name                 = "metadata"
  storage_account_name = azurerm_storage_account.images.name
}

resource "azurerm_storage_container" "metadata_images" {
  name                  = "metadata-images"
  storage_account_id    = azurerm_storage_account.images.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "tags_images" {
  name                  = "tags-images"
  storage_account_id    = azurerm_storage_account.images.id
  container_access_type = "private"
}

resource "azurerm_storage_container" "thumbnail_images" {
  name                  = "thumbnail-images"
  storage_account_id    = azurerm_storage_account.images.id
  container_access_type = "private"
}
