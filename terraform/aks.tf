resource "azurerm_kubernetes_cluster" "aks" {
  name                = "phototag-aks"
  location            = azurerm_resource_group.phototag.location
  resource_group_name = azurerm_resource_group.phototag.name
  dns_prefix          = "phototag-aks-dns"

  default_node_pool {
    name       = "default"
    node_count = 1
    vm_size    = "Standard_D2_v3"
  }

  identity {
    type = "SystemAssigned"
  }

  tags = {
    Environment = "Production"
  }
}

resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.aks.kubelet_identity[0].object_id

  depends_on = [azurerm_container_registry.acr]
}

output "kube_config" {
  value     = azurerm_kubernetes_cluster.aks.kube_config_raw
  sensitive = true
}

resource "kubernetes_namespace_v1" "argocd" {
  metadata {
    name = "argocd"
  }
}

resource "kubernetes_secret_v1" "subscription_key" {
  metadata {
    name      = "subscription-key"
    namespace = "default"
  }
  data = {
    subscription-key = azurerm_api_management_subscription.subscription.primary_key
  }
}

resource "kubernetes_secret_v1" "api_url" {
  metadata {
    name      = "api-url"
    namespace = "default"
  }
  data = {
    api-url = azurerm_api_management.apim.gateway_url
  }
}
