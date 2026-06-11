terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "4.76.0"
    }

    random = {
      source  = "hashicorp/random"
      version = "3.9.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "phototag-rg"
    storage_account_name = "phototagstg001"
    container_name       = "tfstate"
    key                  = "envs/prod/terraform.tfstate"
  }
}

