terraform {
  backend "azurerm" {
    resource_group_name  = "phototag-rg"
    storage_account_name = "phototagstg001"
    container_name       = "tfstate"
    key                  = "envs/prod/terraform.tfstate"
  }
}

