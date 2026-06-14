resource "azurerm_api_management" "apim" {
  name                = lower("apim${random_id.random.hex}")
  resource_group_name = azurerm_resource_group.phototag.name
  location            = azurerm_resource_group.phototag.location
  publisher_name      = "Kris-Ja"
  publisher_email     = "107918765+Kris-Ja@users.noreply.github.com"
  sku_name            = "Consumption_0"
}

resource "azurerm_api_management_subscription" "subscription" {
  api_management_name = azurerm_api_management.apim.name
  resource_group_name = azurerm_api_management.apim.resource_group_name
  display_name        = "App subscription"
  state               = "active"
  allow_tracing       = false
}

output "subscription_key" {
  value     = azurerm_api_management_subscription.subscription.primary_key
  sensitive = true
}

resource "azurerm_api_management_api" "api" {
  name                = "api"
  api_management_name = azurerm_api_management.apim.name
  resource_group_name = azurerm_api_management.apim.resource_group_name
  revision            = "1"
  display_name        = "API"
  protocols           = ["https"]
}

data "azurerm_client_config" "client_config" {}

resource "azurerm_api_management_named_value" "tenant_id" {
  name                = "tenant-id"
  resource_group_name = azurerm_api_management.apim.resource_group_name
  api_management_name = azurerm_api_management.apim.name
  display_name        = "tenant-id"
  value               = data.azurerm_client_config.client_config.tenant_id
  secret              = true
}

resource "azurerm_api_management_named_value" "client_application_id" {
  name                = "client-application-id"
  resource_group_name = azurerm_api_management.apim.resource_group_name
  api_management_name = azurerm_api_management.apim.name
  display_name        = "client-application-id"
  value               = azurerm_api_management.apim.id
  secret              = true
}

resource "azurerm_api_management_api_policy" "api_policy" {
  api_name            = azurerm_api_management_api.api.name
  api_management_name = azurerm_api_management_api.api.api_management_name
  resource_group_name = azurerm_api_management_api.api.resource_group_name
  xml_content         = <<XML
<policies>
  <inbound>
    <base />
    <rate-limit calls="10" renewal-period="30" />
  </inbound>
  <backend>
    <base />
  </backend>
  <outbound>
    <base />
  </outbound>
  <on-error>
    <base />
  </on-error>
</policies>
XML
}

resource "azurerm_api_management_named_value" "images_service_name" {
  name                = "images-service-name"
  resource_group_name = azurerm_api_management.apim.resource_group_name
  api_management_name = azurerm_api_management.apim.name
  display_name        = "images-service-name"
  value               = azurerm_function_app_flex_consumption.images_service.name
  secret              = true
}

resource "azurerm_api_management_named_value" "images_service_key" {
  name                = "images-service-key"
  resource_group_name = azurerm_api_management.apim.resource_group_name
  api_management_name = azurerm_api_management.apim.name
  display_name        = "images-service-key"
  value               = data.azurerm_function_app_host_keys.images_service.default_function_key
  secret              = true
}

resource "azurerm_api_management_api_operation" "upload_images" {
  api_management_name = azurerm_api_management.apim.name
  api_name            = azurerm_api_management_api.api.name
  resource_group_name = azurerm_api_management.apim.resource_group_name

  operation_id = "upload-images"
  display_name = "Upload image"
  method       = "POST"
  url_template = "/"
}

resource "azurerm_api_management_api_operation_policy" "upload_images" {
  api_management_name = azurerm_api_management.apim.name
  api_name            = azurerm_api_management_api.api.name
  operation_id        = azurerm_api_management_api_operation.upload_images.operation_id
  resource_group_name = azurerm_api_management.apim.resource_group_name

  xml_content = <<XML
<policies>
  <inbound>
    <base />
    <set-query-parameter name="code" exists-action="override">
      <value>{{images-service-key}}</value>
    </set-query-parameter>
    <set-backend-service base-url="https://{{images-service-name}}.azurewebsites.net/api/upload" />
  </inbound>
  <backend>
    <base />
  </backend>
  <outbound>
    <base />
  </outbound>
  <on-error>
    <base />
  </on-error>
</policies>
XML
  depends_on  = [azurerm_api_management_named_value.images_service_name, azurerm_api_management_named_value.images_service_key]
}

