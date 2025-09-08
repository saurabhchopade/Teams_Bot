"""Utility functions for Teams meeting operations."""

import re
import logging
from typing import Optional, Dict, List
from urllib.parse import urlparse, parse_qs
import base64
import json

logger = logging.getLogger(__name__)


class MeetingUtils:
    """Utility functions for Microsoft Teams meeting operations."""
    
    @staticmethod
    def extract_meeting_info(meeting_url: str) -> Dict[str, str]:
        """
        Extract meeting information from various Teams meeting URL formats.
        
        Args:
            meeting_url: Teams meeting join URL
            
        Returns:
            Dictionary containing extracted meeting information
        """
        try:
            meeting_info = {
                "meeting_id": None,
                "thread_id": None,
                "organizer_id": None,
                "tenant_id": None,
                "conference_id": None,
                "url_type": "unknown"
            }
            
            # Parse URL
            parsed_url = urlparse(meeting_url)
            query_params = parse_qs(parsed_url.query)
            
            # Extract meeting ID from different URL patterns
            patterns = [
                # Standard meetup-join format
                (r'meetup-join/([^/\?]+)', 'meeting_id'),
                # Thread ID format
                (r'19:meeting_([^@]+)@thread\.v2', 'thread_id'),
                # Conference ID format
                (r'conf-id=([^&]+)', 'conference_id'),
                # Organizer ID format
                (r'organizer=([^&]+)', 'organizer_id'),
                # Tenant ID format
                (r'tenant=([^&]+)', 'tenant_id')
            ]
            
            for pattern, key in patterns:
                match = re.search(pattern, meeting_url)
                if match:
                    meeting_info[key] = match.group(1)
            
            # Determine URL type
            if 'teams.microsoft.com' in meeting_url:
                if 'meetup-join' in meeting_url:
                    meeting_info['url_type'] = 'meetup_join'
                elif 'l/meetup-join' in meeting_url:
                    meeting_info['url_type'] = 'deep_link'
                else:
                    meeting_info['url_type'] = 'teams_web'
            elif 'teams.live.com' in meeting_url:
                meeting_info['url_type'] = 'teams_live'
            
            # Extract from query parameters
            for param, value in query_params.items():
                if param == 'meetingID' and value:
                    meeting_info['meeting_id'] = value[0]
                elif param == 'threadId' and value:
                    meeting_info['thread_id'] = value[0]
                elif param == 'tenantId' and value:
                    meeting_info['tenant_id'] = value[0]
            
            logger.info(f"Extracted meeting info: {meeting_info}")
            return meeting_info
            
        except Exception as e:
            logger.error(f"Error extracting meeting info: {str(e)}")
            return meeting_info
    
    @staticmethod
    def validate_meeting_url(meeting_url: str) -> bool:
        """
        Validate if the provided URL is a valid Teams meeting URL.
        
        Args:
            meeting_url: URL to validate
            
        Returns:
            True if valid Teams meeting URL
        """
        try:
            if not meeting_url or not isinstance(meeting_url, str):
                return False
            
            # Check for Teams domains
            valid_domains = [
                'teams.microsoft.com',
                'teams.live.com',
                'meet.lync.com',
                'join.skype.com'
            ]
            
            domain_found = any(domain in meeting_url.lower() for domain in valid_domains)
            
            if not domain_found:
                return False
            
            # Check for meeting-specific patterns
            meeting_patterns = [
                r'meetup-join',
                r'meeting_id',
                r'conf-id',
                r'19:meeting_',
                r'/m/',
                r'join\.skype\.com'
            ]
            
            pattern_found = any(re.search(pattern, meeting_url, re.IGNORECASE) for pattern in meeting_patterns)
            
            return pattern_found
            
        except Exception as e:
            logger.error(f"Error validating meeting URL: {str(e)}")
            return False
    
    @staticmethod
    def generate_join_info(meeting_info: Dict[str, str]) -> Dict[str, str]:
        """
        Generate join information for Graph API calls.
        
        Args:
            meeting_info: Meeting information dictionary
            
        Returns:
            Join information formatted for API calls
        """
        try:
            join_info = {}
            
            if meeting_info.get('meeting_id'):
                join_info['meetingId'] = meeting_info['meeting_id']
            
            if meeting_info.get('thread_id'):
                join_info['threadId'] = meeting_info['thread_id']
            
            if meeting_info.get('organizer_id'):
                join_info['organizerId'] = meeting_info['organizer_id']
            
            if meeting_info.get('tenant_id'):
                join_info['tenantId'] = meeting_info['tenant_id']
            
            return join_info
            
        except Exception as e:
            logger.error(f"Error generating join info: {str(e)}")
            return {}
    
    @staticmethod
    def format_participant_info(participant_data: Dict) -> Dict[str, str]:
        """
        Format participant information from Graph API response.
        
        Args:
            participant_data: Raw participant data from API
            
        Returns:
            Formatted participant information
        """
        try:
            formatted_info = {
                'id': participant_data.get('id', ''),
                'display_name': '',
                'email': '',
                'role': 'attendee',
                'is_muted': False,
                'is_in_lobby': False,
                'join_time': '',
                'user_type': 'unknown'
            }
            
            # Extract identity information
            info = participant_data.get('info', {})
            identity = info.get('identity', {})
            
            # User information
            user = identity.get('user', {})
            if user:
                formatted_info['display_name'] = user.get('displayName', '')
                formatted_info['email'] = user.get('userPrincipalName', '')
                formatted_info['user_type'] = 'user'
            
            # Application information (for bots)
            application = identity.get('application', {})
            if application:
                formatted_info['display_name'] = application.get('displayName', '')
                formatted_info['user_type'] = 'application'
            
            # Guest information
            guest = identity.get('guest', {})
            if guest:
                formatted_info['display_name'] = guest.get('displayName', '')
                formatted_info['user_type'] = 'guest'
            
            # Media state
            media_state = participant_data.get('mediaState', {})
            if media_state:
                audio = media_state.get('audio', {})
                formatted_info['is_muted'] = audio.get('state') == 'muted'
            
            # Meeting state
            meeting_state = participant_data.get('meetingState', {})
            if meeting_state:
                formatted_info['role'] = meeting_state.get('role', 'attendee')
                formatted_info['is_in_lobby'] = meeting_state.get('state') == 'inLobby'
            
            return formatted_info
            
        except Exception as e:
            logger.error(f"Error formatting participant info: {str(e)}")
            return {}
    
    @staticmethod
    def create_meeting_context(meeting_info: Dict, participants: List[Dict]) -> Dict:
        """
        Create a comprehensive meeting context object.
        
        Args:
            meeting_info: Meeting information
            participants: List of participants
            
        Returns:
            Meeting context dictionary
        """
        try:
            context = {
                'meeting_info': meeting_info,
                'participant_count': len(participants),
                'participants': participants,
                'bot_participant': None,
                'candidate_participants': [],
                'other_participants': [],
                'meeting_state': 'active'
            }
            
            # Categorize participants
            for participant in participants:
                user_type = participant.get('user_type', 'unknown')
                display_name = participant.get('display_name', '').lower()
                
                if user_type == 'application' or 'bot' in display_name:
                    context['bot_participant'] = participant
                elif user_type in ['user', 'guest']:
                    # Assume non-bot users are candidates or interviewers
                    if 'interview' not in display_name:
                        context['candidate_participants'].append(participant)
                    else:
                        context['other_participants'].append(participant)
                else:
                    context['other_participants'].append(participant)
            
            # Determine meeting state
            if context['participant_count'] < 2:
                context['meeting_state'] = 'waiting_for_participants'
            elif any(p.get('is_in_lobby', False) for p in participants):
                context['meeting_state'] = 'participants_in_lobby'
            else:
                context['meeting_state'] = 'active'
            
            return context
            
        except Exception as e:
            logger.error(f"Error creating meeting context: {str(e)}")
            return {}
    
    @staticmethod
    def generate_meeting_summary(context: Dict, duration_minutes: int = 0) -> str:
        """
        Generate a human-readable meeting summary.
        
        Args:
            context: Meeting context dictionary
            duration_minutes: Meeting duration in minutes
            
        Returns:
            Meeting summary string
        """
        try:
            summary_parts = []
            
            # Basic meeting info
            meeting_info = context.get('meeting_info', {})
            meeting_id = meeting_info.get('meeting_id', 'Unknown')
            summary_parts.append(f"Meeting ID: {meeting_id}")
            
            # Participant summary
            participant_count = context.get('participant_count', 0)
            summary_parts.append(f"Total Participants: {participant_count}")
            
            # Candidate information
            candidates = context.get('candidate_participants', [])
            if candidates:
                candidate_names = [p.get('display_name', 'Unknown') for p in candidates]
                summary_parts.append(f"Candidates: {', '.join(candidate_names)}")
            
            # Bot information
            bot = context.get('bot_participant')
            if bot:
                bot_name = bot.get('display_name', 'Interview Bot')
                summary_parts.append(f"Bot: {bot_name}")
            
            # Duration
            if duration_minutes > 0:
                summary_parts.append(f"Duration: {duration_minutes} minutes")
            
            # Meeting state
            state = context.get('meeting_state', 'unknown')
            summary_parts.append(f"State: {state.replace('_', ' ').title()}")
            
            return " | ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error generating meeting summary: {str(e)}")
            return "Meeting summary unavailable"
    
    @staticmethod
    def decode_meeting_token(token: str) -> Optional[Dict]:
        """
        Decode a Teams meeting token to extract information.
        
        Args:
            token: Base64 encoded meeting token
            
        Returns:
            Decoded token information or None if decoding fails
        """
        try:
            # Remove any URL encoding
            token = token.replace('%3D', '=').replace('%2B', '+').replace('%2F', '/')
            
            # Add padding if necessary
            padding = 4 - (len(token) % 4)
            if padding != 4:
                token += '=' * padding
            
            # Decode base64
            decoded_bytes = base64.b64decode(token)
            decoded_str = decoded_bytes.decode('utf-8')
            
            # Try to parse as JSON
            try:
                token_data = json.loads(decoded_str)
                return token_data
            except json.JSONDecodeError:
                # If not JSON, return as string
                return {'raw_data': decoded_str}
                
        except Exception as e:
            logger.error(f"Error decoding meeting token: {str(e)}")
            return None