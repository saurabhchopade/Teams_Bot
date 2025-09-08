"""Test suite for the Microsoft Teams Interview Bot."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import json

from auth.teams_auth import TeamsAuthenticator
from teams.meeting_bot import TeamsMeetingBot
from speech.speech_processor import SpeechProcessor
from ai.interview_brain import InterviewAI
from orchestrator.interview_orchestrator import InterviewBotOrchestrator
from utils.meeting_utils import MeetingUtils
from config.settings import settings


class TestTeamsAuthenticator:
    """Test cases for Teams authentication."""
    
    @pytest.fixture
    def auth_handler(self):
        """Create a test authentication handler."""
        return TeamsAuthenticator()
    
    @pytest.mark.asyncio
    async def test_get_access_token_success(self, auth_handler):
        """Test successful access token acquisition."""
        with patch.object(auth_handler.msal_app, 'acquire_token_for_client') as mock_acquire:
            mock_acquire.return_value = {"access_token": "test_token_123"}
            
            token = await auth_handler.get_access_token()
            
            assert token == "test_token_123"
            assert auth_handler._access_token == "test_token_123"
    
    @pytest.mark.asyncio
    async def test_get_access_token_failure(self, auth_handler):
        """Test access token acquisition failure."""
        with patch.object(auth_handler.msal_app, 'acquire_token_for_client') as mock_acquire:
            mock_acquire.return_value = {"error": "invalid_client"}
            
            with pytest.raises(Exception):
                await auth_handler.get_access_token()
    
    def test_get_auth_headers(self, auth_handler):
        """Test authentication headers generation."""
        auth_handler._access_token = "test_token_123"
        
        headers = auth_handler.get_auth_headers()
        
        assert headers["Authorization"] == "Bearer test_token_123"
        assert headers["Content-Type"] == "application/json"
    
    def test_get_auth_headers_no_token(self, auth_handler):
        """Test authentication headers without token."""
        with pytest.raises(Exception):
            auth_handler.get_auth_headers()


class TestMeetingBot:
    """Test cases for Teams meeting bot."""
    
    @pytest.fixture
    def mock_auth(self):
        """Create a mock authentication handler."""
        auth = Mock(spec=TeamsAuthenticator)
        auth.get_auth_headers.return_value = {
            "Authorization": "Bearer test_token",
            "Content-Type": "application/json"
        }
        return auth
    
    @pytest.fixture
    def meeting_bot(self, mock_auth):
        """Create a test meeting bot."""
        return TeamsMeetingBot(mock_auth)
    
    def test_extract_meeting_id_success(self, meeting_bot):
        """Test successful meeting ID extraction."""
        test_urls = [
            "https://teams.microsoft.com/l/meetup-join/19%3ameeting_test123%40thread.v2",
            "https://teams.microsoft.com/meetup-join/test_meeting_456",
            "https://teams.live.com/meet/test789"
        ]
        
        for url in test_urls:
            meeting_id = meeting_bot._extract_meeting_id(url)
            assert meeting_id is not None
            assert len(meeting_id) > 0
    
    def test_extract_meeting_id_failure(self, meeting_bot):
        """Test meeting ID extraction failure."""
        invalid_urls = [
            "https://example.com/not-a-teams-meeting",
            "invalid-url",
            ""
        ]
        
        for url in invalid_urls:
            meeting_id = meeting_bot._extract_meeting_id(url)
            assert meeting_id is None
    
    @pytest.mark.asyncio
    async def test_join_meeting_success(self, meeting_bot):
        """Test successful meeting join."""
        test_url = "https://teams.microsoft.com/l/meetup-join/test123"
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 201
            mock_response.json.return_value = {"id": "call_123"}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            meeting_bot.session = Mock()
            meeting_bot.session.post = mock_post
            
            result = await meeting_bot.join_meeting(test_url)
            
            assert result is True
            assert meeting_bot.call_id == "call_123"
            assert meeting_bot.is_in_meeting is True


class TestSpeechProcessor:
    """Test cases for speech processing."""
    
    @pytest.fixture
    def speech_processor(self):
        """Create a test speech processor."""
        return SpeechProcessor()
    
    def test_initialize_recognizer(self, speech_processor):
        """Test speech recognizer initialization."""
        with patch('azure.cognitiveservices.speech.SpeechRecognizer'):
            result = speech_processor.initialize_recognizer()
            assert result is True
            assert speech_processor.speech_recognizer is not None
    
    def test_initialize_synthesizer(self, speech_processor):
        """Test speech synthesizer initialization."""
        with patch('azure.cognitiveservices.speech.SpeechSynthesizer'):
            result = speech_processor.initialize_synthesizer()
            assert result is True
            assert speech_processor.speech_synthesizer is not None
    
    def test_get_voice_config(self, speech_processor):
        """Test voice configuration retrieval."""
        config = speech_processor._get_voice_config("professional")
        
        assert "voice_name" in config
        assert "rate" in config
        assert "pitch" in config
        assert config["voice_name"] == "en-US-AriaNeural"
    
    @pytest.mark.asyncio
    async def test_speak_in_meeting_success(self, speech_processor):
        """Test successful speech synthesis."""
        with patch.object(speech_processor, 'initialize_synthesizer', return_value=True):
            mock_synthesizer = Mock()
            mock_result = Mock()
            mock_result.reason = Mock()
            mock_result.reason = 3  # SynthesizingAudioCompleted
            mock_synthesizer.speak_ssml.return_value = mock_result
            
            speech_processor.speech_synthesizer = mock_synthesizer
            
            result = await speech_processor.speak_in_meeting("Hello, world!")
            
            assert result is True


class TestInterviewAI:
    """Test cases for interview AI."""
    
    @pytest.fixture
    def interview_ai(self):
        """Create a test interview AI."""
        return InterviewAI()
    
    @pytest.mark.asyncio
    async def test_initialize_interview(self, interview_ai):
        """Test interview initialization."""
        candidate_info = {"name": "John Doe", "experience_level": "mid"}
        role_info = {"title": "Software Developer"}
        
        with patch('openai.ChatCompletion.acreate') as mock_openai:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Welcome to the interview!"
            mock_openai.return_value = mock_response
            
            result = await interview_ai.initialize_interview(candidate_info, role_info)
            
            assert isinstance(result, str)
            assert len(result) > 0
            assert interview_ai.candidate_info == candidate_info
    
    @pytest.mark.asyncio
    async def test_analyze_response(self, interview_ai):
        """Test response analysis."""
        question = "Tell me about yourself"
        answer = "I'm a software developer with 5 years of experience"
        
        with patch('openai.ChatCompletion.acreate') as mock_openai:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = json.dumps({
                "content_quality": {"score": 8, "reasoning": "Good response"},
                "communication_clarity": {"score": 7, "reasoning": "Clear communication"},
                "technical_depth": {"score": 6, "reasoning": "Basic technical info"},
                "key_insights": ["Experienced developer"],
                "areas_to_explore": ["Specific technologies"],
                "overall_assessment": "Good introduction",
                "follow_up_suggestions": ["Ask about specific projects"]
            })
            mock_openai.return_value = mock_response
            
            result = await interview_ai.analyze_response(question, answer)
            
            assert isinstance(result, dict)
            assert "content_quality" in result
            assert "overall_assessment" in result
    
    def test_should_end_interview(self, interview_ai):
        """Test interview end condition."""
        # Test with max questions reached
        interview_ai.questions_asked = interview_ai.max_questions
        assert interview_ai.should_end_interview() is True
        
        # Test with normal progress
        interview_ai.questions_asked = 5
        interview_ai.current_stage_index = 2
        assert interview_ai.should_end_interview() is False


class TestMeetingUtils:
    """Test cases for meeting utilities."""
    
    def test_validate_meeting_url_valid(self):
        """Test valid meeting URL validation."""
        valid_urls = [
            "https://teams.microsoft.com/l/meetup-join/test123",
            "https://teams.live.com/meet/test456",
            "https://meet.lync.com/test789"
        ]
        
        for url in valid_urls:
            assert MeetingUtils.validate_meeting_url(url) is True
    
    def test_validate_meeting_url_invalid(self):
        """Test invalid meeting URL validation."""
        invalid_urls = [
            "https://example.com/meeting",
            "not-a-url",
            "",
            None
        ]
        
        for url in invalid_urls:
            assert MeetingUtils.validate_meeting_url(url) is False
    
    def test_extract_meeting_info(self):
        """Test meeting information extraction."""
        test_url = "https://teams.microsoft.com/l/meetup-join/19%3ameeting_test123%40thread.v2"
        
        info = MeetingUtils.extract_meeting_info(test_url)
        
        assert isinstance(info, dict)
        assert "meeting_id" in info
        assert "url_type" in info
        assert info["url_type"] == "deep_link"
    
    def test_format_participant_info(self):
        """Test participant information formatting."""
        participant_data = {
            "id": "participant_123",
            "info": {
                "identity": {
                    "user": {
                        "displayName": "John Doe",
                        "userPrincipalName": "john@example.com"
                    }
                }
            },
            "mediaState": {
                "audio": {"state": "unmuted"}
            }
        }
        
        formatted = MeetingUtils.format_participant_info(participant_data)
        
        assert formatted["display_name"] == "John Doe"
        assert formatted["email"] == "john@example.com"
        assert formatted["is_muted"] is False
        assert formatted["user_type"] == "user"


class TestInterviewOrchestrator:
    """Test cases for interview orchestrator."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create a test orchestrator."""
        return InterviewBotOrchestrator()
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, orchestrator):
        """Test successful orchestrator initialization."""
        with patch.object(orchestrator.auth_handler, 'authenticate_bot', return_value=True), \
             patch.object(orchestrator.speech_processor, 'initialize_recognizer', return_value=True), \
             patch.object(orchestrator.speech_processor, 'initialize_synthesizer', return_value=True), \
             patch.object(orchestrator.speech_processor, 'handle_audio_feedback', return_value=True):
            
            result = await orchestrator.initialize()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_initialize_auth_failure(self, orchestrator):
        """Test orchestrator initialization with auth failure."""
        with patch.object(orchestrator.auth_handler, 'authenticate_bot', return_value=False):
            
            result = await orchestrator.initialize()
            
            assert result is False
    
    def test_get_interview_results(self, orchestrator):
        """Test interview results retrieval."""
        orchestrator.interview_session_id = "test_session_123"
        orchestrator.interview_transcript = [
            {"timestamp": "2024-01-01T10:00:00", "speaker": "interviewer", "content": "Hello"}
        ]
        orchestrator.interview_results = {"overall_score": 8}
        
        results = orchestrator.get_interview_results()
        
        assert results["session_id"] == "test_session_123"
        assert "transcript" in results
        assert "ai_assessment" in results
        assert "session_metadata" in results


# Integration tests
class TestIntegration:
    """Integration test cases."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_mock(self):
        """Test the full interview workflow with mocked components."""
        # This would be a comprehensive integration test
        # that mocks external services but tests the full flow
        
        orchestrator = InterviewBotOrchestrator()
        
        # Mock all external dependencies
        with patch.object(orchestrator.auth_handler, 'authenticate_bot', return_value=True), \
             patch.object(orchestrator.speech_processor, 'initialize_recognizer', return_value=True), \
             patch.object(orchestrator.speech_processor, 'initialize_synthesizer', return_value=True), \
             patch.object(orchestrator.speech_processor, 'handle_audio_feedback', return_value=True):
            
            # Initialize
            init_result = await orchestrator.initialize()
            assert init_result is True
            
            # Test that components are properly initialized
            assert orchestrator.auth_handler is not None
            assert orchestrator.speech_processor is not None
            assert orchestrator.interview_ai is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])