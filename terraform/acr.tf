resource "random_id" "acr" {
  byte_length = 14
}

resource "azurerm_container_registry" "acr" {
  name                = lower("phototagacr${random_id.acr.hex}")
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "Standard"
  admin_enabled       = false
}

resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.aks.kubelet_identity[0].object_id

  depends_on = [azurerm_container_registry.acr]
}

output "acr_login_server" {
  value = azurerm_container_registry.acr.login_server
}
