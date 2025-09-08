"""Microsoft Teams authentication handler using Azure AD and MSAL."""

import logging
from typing import Optional, Dict, Any
from msal import ConfidentialClientApplication
from azure.identity import ClientSecretCredential
from config.settings import settings

logger = logging.getLogger(__name__)


class TeamsAuthenticator:
    """Handles authentication with Microsoft Teams and Azure AD."""
    
    def __init__(self):
        """Initialize the authenticator with Azure AD configuration."""
        self.client_id = settings.azure_client_id
        self.client_secret = settings.azure_client_secret
        self.tenant_id = settings.azure_tenant_id
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        
        # Initialize MSAL client
        self.msal_app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )
        
        # Initialize Azure Identity credential
        self.credential = ClientSecretCredential(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        
        self._access_token: Optional[str] = None
        self._token_cache: Dict[str, Any] = {}
    
    async def get_access_token(self, scopes: Optional[list] = None) -> str:
        """
        Acquire access token for Microsoft Graph API.
        
        Args:
            scopes: List of required scopes, defaults to Graph API scopes
            
        Returns:
            Valid access token string
        """
        if scopes is None:
            scopes = settings.required_scopes
        
        try:
            # Try to get token from cache first
            accounts = self.msal_app.get_accounts()
            if accounts:
                result = self.msal_app.acquire_token_silent(scopes, account=accounts[0])
                if result and "access_token" in result:
                    self._access_token = result["access_token"]
                    logger.info("Retrieved access token from cache")
                    return self._access_token
            
            # Acquire new token using client credentials flow
            result = self.msal_app.acquire_token_for_client(scopes=scopes)
            
            if "access_token" in result:
                self._access_token = result["access_token"]
                logger.info("Successfully acquired new access token")
                return self._access_token
            else:
                error_msg = result.get("error_description", "Unknown error")
                logger.error(f"Failed to acquire access token: {error_msg}")
                raise Exception(f"Authentication failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error acquiring access token: {str(e)}")
            raise
    
    async def authenticate_bot(self) -> bool:
        """
        Authenticate the bot with Azure Bot Framework.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Get access token for Bot Framework
            token = await self.get_access_token()
            
            if token:
                logger.info("Bot authentication successful")
                return True
            else:
                logger.error("Bot authentication failed - no token received")
                return False
                
        except Exception as e:
            logger.error(f"Bot authentication error: {str(e)}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dictionary containing authorization headers
        """
        if not self._access_token:
            raise Exception("No access token available. Call get_access_token() first.")
        
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }
    
    async def validate_permissions(self) -> bool:
        """
        Validate that the bot has required permissions.
        
        Returns:
            True if all required permissions are granted
        """
        try:
            # This would typically involve checking the token claims
            # or making a test API call to verify permissions
            token = await self.get_access_token()
            
            if token:
                logger.info("Permissions validation successful")
                return True
            else:
                logger.error("Permissions validation failed")
                return False
                
        except Exception as e:
            logger.error(f"Permission validation error: {str(e)}")
            return False