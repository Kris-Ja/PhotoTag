provider "azurerm" {
  features {
    api_management {
      purge_soft_delete_on_destroy = true
    }
  }
}

resource "azurerm_resource_group" "phototag" {
  name     = var.resource_group_name
  location = var.location
}

