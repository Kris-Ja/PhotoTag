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

resource "azurerm_resource_group" "phototag_cognitive" {
  name     = "${var.resource_group_name}-cognitive"
  location = var.location_cognitive
}

provider "kubernetes" {
  host                   = azurerm_kubernetes_cluster.aks.kube_config[0].host
  client_certificate     = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].client_certificate)
  client_key             = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].cluster_ca_certificate)
}
