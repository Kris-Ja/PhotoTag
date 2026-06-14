# PhotoTag - Projektowanie Systemów Rozproszonych

## How to initialize remote backend (actually we could have done it better)

Login to Azure using Azure CLI:
```bash
az login
```

Create resource group:
```bash
az group create -n phototag-rg -l polandcentral
```

Create storage account:
```bash
az storage account create -n phototagstg001 -g phototag-rg -l polandcentral --sku Standard_LRS --kind StorageV2 --https-only true
```

Export access key:
```bash
export ARM_ACCESS_KEY=$(az storage account keys list -g phototag-rg -n phototagstg001 --query [0].value -o tsv)
```

Create storage container for terraform state:
```bash
az storage container create -n tfstate --account-name phototagstg001
```

Initialize terraform:
```bash
terraform init
```

Import resource group into terraform state:
```bash
terraform import azurerm_resource_group.phototag /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/phototag-rg
```
