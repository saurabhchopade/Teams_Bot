#!/bin/bash

# Microsoft Teams Interview Bot - Azure Setup Script
# This script helps set up the required Azure resources

set -e

echo "🚀 Microsoft Teams Interview Bot - Azure Setup"
echo "=============================================="

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first:"
    echo "   https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if user is logged in
if ! az account show &> /dev/null; then
    echo "🔐 Please log in to Azure CLI:"
    az login
fi

# Get current subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "📋 Using subscription: $SUBSCRIPTION_ID"

# Configuration
RESOURCE_GROUP_NAME="teams-interview-bot-rg"
LOCATION="eastus"
APP_NAME="teams-interview-bot-$(date +%s)"
BOT_NAME="teams-interview-bot"
SPEECH_SERVICE_NAME="teams-interview-speech"

echo ""
echo "📝 Configuration:"
echo "   Resource Group: $RESOURCE_GROUP_NAME"
echo "   Location: $LOCATION"
echo "   App Name: $APP_NAME"
echo "   Bot Name: $BOT_NAME"
echo "   Speech Service: $SPEECH_SERVICE_NAME"
echo ""

read -p "Continue with setup? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled."
    exit 1
fi

echo "🏗️  Creating Azure resources..."

# Create resource group
echo "📦 Creating resource group..."
az group create \
    --name $RESOURCE_GROUP_NAME \
    --location $LOCATION

# Create Azure AD App Registration
echo "🔐 Creating Azure AD App Registration..."
APP_ID=$(az ad app create \
    --display-name $APP_NAME \
    --query appId -o tsv)

echo "   App ID: $APP_ID"

# Create service principal
echo "👤 Creating service principal..."
az ad sp create --id $APP_ID

# Create client secret
echo "🔑 Creating client secret..."
CLIENT_SECRET=$(az ad app credential reset \
    --id $APP_ID \
    --query password -o tsv)

# Get tenant ID
TENANT_ID=$(az account show --query tenantId -o tsv)

# Create Speech Services
echo "🎤 Creating Speech Services..."
az cognitiveservices account create \
    --name $SPEECH_SERVICE_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --kind SpeechServices \
    --sku S0 \
    --location $LOCATION

# Get Speech Service key
SPEECH_KEY=$(az cognitiveservices account keys list \
    --name $SPEECH_SERVICE_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --query key1 -o tsv)

# Create Bot Framework registration
echo "🤖 Creating Bot Framework registration..."
az bot create \
    --resource-group $RESOURCE_GROUP_NAME \
    --name $BOT_NAME \
    --kind registration \
    --version v4 \
    --lang python \
    --verbose \
    --appid $APP_ID

# Set required API permissions
echo "🔒 Setting API permissions..."

# Microsoft Graph permissions
GRAPH_API_ID="00000003-0000-0000-c000-000000000000"

# OnlineMeetings.ReadWrite.All
az ad app permission add \
    --id $APP_ID \
    --api $GRAPH_API_ID \
    --api-permissions "b8bb2037-6e08-44ac-a4ea-4b8f279dabd8=Role"

# Calls.AccessMedia.All
az ad app permission add \
    --id $APP_ID \
    --api $GRAPH_API_ID \
    --api-permissions "a7a681dc-756e-4909-b988-f160edc6655f=Role"

# Calls.JoinGroupCall.All
az ad app permission add \
    --id $APP_ID \
    --api $GRAPH_API_ID \
    --api-permissions "f6b49018-60ab-4f81-83bd-22caeabfed2d=Role"

# CallRecords.Read.All
az ad app permission add \
    --id $APP_ID \
    --api $GRAPH_API_ID \
    --api-permissions "45bbb07e-7321-4fd7-a8f6-3ff27e6a81c8=Role"

echo "⚠️  IMPORTANT: You need to grant admin consent for the API permissions."
echo "   Go to: https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/CallAnAPI/appId/$APP_ID"
echo "   Click 'Grant admin consent' for the permissions."
echo ""

# Create App Service (optional)
read -p "Create App Service for hosting? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🌐 Creating App Service..."
    
    APP_SERVICE_PLAN="$APP_NAME-plan"
    
    # Create App Service Plan
    az appservice plan create \
        --name $APP_SERVICE_PLAN \
        --resource-group $RESOURCE_GROUP_NAME \
        --sku B1 \
        --is-linux
    
    # Create Web App
    az webapp create \
        --resource-group $RESOURCE_GROUP_NAME \
        --plan $APP_SERVICE_PLAN \
        --name $APP_NAME \
        --runtime "PYTHON|3.9"
    
    # Get App Service URL
    APP_URL="https://$APP_NAME.azurewebsites.net"
    echo "   App Service URL: $APP_URL"
    
    # Configure app settings
    az webapp config appsettings set \
        --resource-group $RESOURCE_GROUP_NAME \
        --name $APP_NAME \
        --settings \
            AZURE_CLIENT_ID=$APP_ID \
            AZURE_TENANT_ID=$TENANT_ID \
            BOT_APP_ID=$APP_ID \
            AZURE_SPEECH_KEY=$SPEECH_KEY \
            AZURE_SPEECH_REGION=$LOCATION \
            BOT_ENDPOINT=$APP_URL
fi

echo ""
echo "✅ Azure setup completed!"
echo ""
echo "📋 Configuration Summary:"
echo "========================"
echo "AZURE_CLIENT_ID=$APP_ID"
echo "AZURE_CLIENT_SECRET=$CLIENT_SECRET"
echo "AZURE_TENANT_ID=$TENANT_ID"
echo "BOT_APP_ID=$APP_ID"
echo "BOT_APP_PASSWORD=$CLIENT_SECRET"
echo "AZURE_SPEECH_KEY=$SPEECH_KEY"
echo "AZURE_SPEECH_REGION=$LOCATION"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "BOT_ENDPOINT=$APP_URL"
fi
echo ""
echo "⚠️  IMPORTANT NEXT STEPS:"
echo "1. Grant admin consent for API permissions in Azure Portal"
echo "2. Copy the above configuration to your .env file"
echo "3. Set up your Google Gemini API key"
echo "4. Configure your webhook endpoint URL"
echo ""
echo "🔗 Useful Links:"
echo "   Azure Portal: https://portal.azure.com"
echo "   Bot Framework Portal: https://dev.botframework.com"
echo "   Graph Explorer: https://developer.microsoft.com/graph/graph-explorer"
echo ""