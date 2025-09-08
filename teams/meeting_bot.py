"""Microsoft Teams meeting bot for joining and managing meetings."""

import asyncio
import logging
import json
import re
from typing import Optional, Dict, List, Any
from urllib.parse import urlparse, parse_qs
import aiohttp
from auth.teams_auth import TeamsAuthenticator
from config.settings import settings

logger = logging.getLogger(__name__)


class TeamsMeetingBot:
    """Handles Microsoft Teams meeting operations and bot integration."""
    
    def __init__(self, auth_handler: TeamsAuthenticator):
        """
        Initialize the Teams meeting bot.
        
        Args:
            auth_handler: Authenticated Teams authenticator instance
        """
        self.auth = auth_handler
        self.session: Optional[aiohttp.ClientSession] = None
        self.meeting_id: Optional[str] = None
        self.call_id: Optional[str] = None
        self.participants: List[Dict] = []
        self.is_in_meeting: bool = False
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _extract_meeting_id(self, meeting_url: str) -> Optional[str]:
        """
        Extract meeting ID from Teams meeting URL.
        
        Args:
            meeting_url: Teams meeting join URL
            
        Returns:
            Meeting ID if found, None otherwise
        """
        try:
            # Parse different Teams URL formats
            patterns = [
                r'meetup-join/([^/\?]+)',
                r'meeting_id=([^&]+)',
                r'/m/([^/\?]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, meeting_url)
                if match:
                    meeting_id = match.group(1)
                    logger.info(f"Extracted meeting ID: {meeting_id}")
                    return meeting_id
            
            logger.warning(f"Could not extract meeting ID from URL: {meeting_url}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting meeting ID: {str(e)}")
            return None
    
    async def join_meeting(self, meeting_url: str) -> bool:
        """
        Join a Microsoft Teams meeting programmatically.
        
        Args:
            meeting_url: Teams meeting join URL
            
        Returns:
            True if successfully joined, False otherwise
        """
        try:
            # Extract meeting ID from URL
            self.meeting_id = self._extract_meeting_id(meeting_url)
            if not self.meeting_id:
                logger.error("Failed to extract meeting ID from URL")
                return False
            
            # Get authentication headers
            headers = self.auth.get_auth_headers()
            
            # Prepare call request payload
            call_payload = {
                "callbackUri": f"{settings.callback_url}/webhook/calls",
                "requestedModalities": ["audio"],
                "mediaConfig": {
                    "@odata.type": "#microsoft.graph.serviceHostedMediaConfig"
                },
                "meetingInfo": {
                    "@odata.type": "#microsoft.graph.organizerMeetingInfo",
                    "organizer": {
                        "identity": {
                            "user": {
                                "id": settings.bot_app_id
                            }
                        }
                    }
                },
                "source": {
                    "identity": {
                        "application": {
                            "id": settings.bot_app_id,
                            "displayName": "Interview Bot"
                        }
                    }
                }
            }
            
            # Make API call to join meeting
            join_url = f"{settings.graph_base_url}/communications/calls"
            
            async with self.session.post(
                join_url,
                headers=headers,
                json=call_payload
            ) as response:
                
                if response.status == 201:
                    call_data = await response.json()
                    self.call_id = call_data.get("id")
                    self.is_in_meeting = True
                    
                    logger.info(f"Successfully joined meeting. Call ID: {self.call_id}")
                    
                    # Setup audio streams
                    await self.setup_audio_streams()
                    
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to join meeting: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error joining meeting: {str(e)}")
            return False
    
    async def setup_audio_streams(self) -> bool:
        """
        Setup bidirectional audio streams for the meeting.
        
        Returns:
            True if audio streams setup successfully
        """
        try:
            if not self.call_id:
                logger.error("No active call to setup audio streams")
                return False
            
            headers = self.auth.get_auth_headers()
            
            # Configure audio settings
            audio_config = {
                "mediaConfig": {
                    "@odata.type": "#microsoft.graph.serviceHostedMediaConfig",
                    "preFetchMedia": [
                        {
                            "uri": f"{settings.callback_url}/audio/welcome.wav",
                            "resourceId": "welcome-message"
                        }
                    ]
                }
            }
            
            # Update call with audio configuration
            update_url = f"{settings.graph_base_url}/communications/calls/{self.call_id}"
            
            async with self.session.patch(
                update_url,
                headers=headers,
                json=audio_config
            ) as response:
                
                if response.status == 200:
                    logger.info("Audio streams setup successfully")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to setup audio streams: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error setting up audio streams: {str(e)}")
            return False
    
    async def leave_meeting(self) -> bool:
        """
        Leave the current Teams meeting gracefully.
        
        Returns:
            True if successfully left the meeting
        """
        try:
            if not self.call_id:
                logger.warning("No active call to leave")
                return True
            
            headers = self.auth.get_auth_headers()
            
            # Delete the call to leave meeting
            leave_url = f"{settings.graph_base_url}/communications/calls/{self.call_id}"
            
            async with self.session.delete(leave_url, headers=headers) as response:
                if response.status in [200, 204]:
                    logger.info("Successfully left the meeting")
                    self.is_in_meeting = False
                    self.call_id = None
                    self.meeting_id = None
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to leave meeting: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error leaving meeting: {str(e)}")
            return False
    
    async def get_meeting_participants(self) -> List[Dict]:
        """
        Get current meeting participants.
        
        Returns:
            List of participant information dictionaries
        """
        try:
            if not self.call_id:
                logger.warning("No active call to get participants")
                return []
            
            headers = self.auth.get_auth_headers()
            
            # Get call participants
            participants_url = f"{settings.graph_base_url}/communications/calls/{self.call_id}/participants"
            
            async with self.session.get(participants_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    self.participants = data.get("value", [])
                    logger.info(f"Retrieved {len(self.participants)} participants")
                    return self.participants
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to get participants: {response.status} - {error_text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting participants: {str(e)}")
            return []
    
    async def mute_participant(self, participant_id: str) -> bool:
        """
        Mute a specific participant in the meeting.
        
        Args:
            participant_id: ID of the participant to mute
            
        Returns:
            True if successfully muted
        """
        try:
            if not self.call_id:
                logger.error("No active call to mute participant")
                return False
            
            headers = self.auth.get_auth_headers()
            
            # Mute participant
            mute_url = f"{settings.graph_base_url}/communications/calls/{self.call_id}/participants/{participant_id}/mute"
            
            async with self.session.post(mute_url, headers=headers) as response:
                if response.status in [200, 202]:
                    logger.info(f"Successfully muted participant: {participant_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to mute participant: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error muting participant: {str(e)}")
            return False
    
    async def send_meeting_message(self, message: str) -> bool:
        """
        Send a text message to the meeting chat.
        
        Args:
            message: Message to send
            
        Returns:
            True if message sent successfully
        """
        try:
            # This would require additional Graph API calls to send chat messages
            # Implementation depends on specific meeting chat API endpoints
            logger.info(f"Sending message to meeting: {message}")
            
            # For now, we'll log the message
            # In a full implementation, this would use the Graph API to send chat messages
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending meeting message: {str(e)}")
            return False