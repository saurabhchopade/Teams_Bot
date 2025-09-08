"""Main orchestrator for the Teams Interview Bot."""

import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime
import json

from auth.teams_auth import TeamsAuthenticator
from teams.meeting_bot import TeamsMeetingBot
from speech.speech_processor import SpeechProcessor
from ai.interview_brain import InterviewAI
from config.settings import settings

logger = logging.getLogger(__name__)


class InterviewBotOrchestrator:
    """Main orchestrator that coordinates all components of the interview bot."""
    
    def __init__(self):
        """Initialize the interview bot orchestrator."""
        # Initialize components
        self.auth_handler = TeamsAuthenticator()
        self.meeting_bot: Optional[TeamsMeetingBot] = None
        self.speech_processor = SpeechProcessor()
        self.interview_ai = InterviewAI()
        
        # State management
        self.is_interview_active = False
        self.current_question: Optional[str] = None
        self.waiting_for_response = False
        self.interview_session_id = None
        
        # Interview data
        self.interview_transcript: list = []
        self.interview_results: Dict = {}
        
        # Event loop for handling real-time events
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None
        
    async def initialize(self) -> bool:
        """
        Initialize all components and authenticate.
        
        Returns:
            True if initialization successful
        """
        try:
            logger.info("Initializing Interview Bot Orchestrator...")
            
            # Authenticate with Azure
            if not await self.auth_handler.authenticate_bot():
                logger.error("Failed to authenticate bot")
                return False
            
            # Initialize speech processor
            if not self.speech_processor.initialize_recognizer():
                logger.error("Failed to initialize speech recognizer")
                return False
            
            if not self.speech_processor.initialize_synthesizer():
                logger.error("Failed to initialize speech synthesizer")
                return False
            
            # Setup audio feedback handling
            await self.speech_processor.handle_audio_feedback()
            
            logger.info("Interview Bot Orchestrator initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing orchestrator: {str(e)}")
            return False
    
    async def start_interview_session(self, meeting_url: str, candidate_info: Dict, role_info: Dict = None) -> bool:
        """
        Start a complete interview session.
        
        Args:
            meeting_url: Teams meeting join URL
            candidate_info: Information about the candidate
            role_info: Information about the role/position
            
        Returns:
            True if interview session started successfully
        """
        try:
            logger.info(f"Starting interview session for candidate: {candidate_info.get('name', 'Unknown')}")
            
            # Generate session ID
            self.interview_session_id = f"interview_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Initialize meeting bot
            self.meeting_bot = TeamsMeetingBot(self.auth_handler)
            
            # Join the Teams meeting
            async with self.meeting_bot:
                if not await self.meeting_bot.join_meeting(meeting_url):
                    logger.error("Failed to join Teams meeting")
                    return False
                
                logger.info("Successfully joined Teams meeting")
                
                # Initialize interview AI
                if role_info is None:
                    role_info = {"title": "Software Developer", "level": "mid"}
                
                opening_message = await self.interview_ai.initialize_interview(candidate_info, role_info)
                
                # Start the interview conversation
                self.is_interview_active = True
                await self._conduct_interview_session(opening_message)
                
                # Generate final assessment
                final_assessment = await self.interview_ai.generate_final_assessment()
                self.interview_results = final_assessment
                
                # Leave meeting gracefully
                await self._end_interview_gracefully()
                
                logger.info("Interview session completed successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error in interview session: {str(e)}")
            await self._cleanup_session()
            return False
    
    async def _conduct_interview_session(self, opening_message: str):
        """
        Conduct the main interview conversation loop.
        
        Args:
            opening_message: Initial message to start the interview
        """
        try:
            logger.info("Starting interview conversation loop")
            
            # Start speech recognition
            await self.speech_processor.start_continuous_recognition(
                callback=self._handle_candidate_response
            )
            
            # Speak the opening message
            await self._speak_question(opening_message)
            
            # Main interview loop
            while self.is_interview_active and not self.interview_ai.should_end_interview():
                # Wait for candidate response
                await self._wait_for_candidate_response()
                
                if not self.is_interview_active:
                    break
                
                # Generate and ask next question
                await self._process_next_question()
                
                # Small delay between questions
                await asyncio.sleep(2)
            
            # Stop speech recognition
            await self.speech_processor.stop_continuous_recognition()
            
            logger.info("Interview conversation loop completed")
            
        except Exception as e:
            logger.error(f"Error in interview conversation: {str(e)}")
            self.is_interview_active = False
    
    async def _speak_question(self, question: str):
        """
        Speak a question in the meeting.
        
        Args:
            question: Question text to speak
        """
        try:
            logger.info(f"Speaking question: {question[:50]}...")
            
            # Speak the question
            success = await self.speech_processor.speak_in_meeting(question, "professional")
            
            if success:
                self.current_question = question
                self.waiting_for_response = True
                
                # Add to transcript
                self.interview_transcript.append({
                    "timestamp": datetime.now().isoformat(),
                    "speaker": "interviewer",
                    "content": question,
                    "type": "question"
                })
            else:
                logger.error("Failed to speak question")
                
        except Exception as e:
            logger.error(f"Error speaking question: {str(e)}")
    
    def _handle_candidate_response(self, recognized_text: str):
        """
        Handle candidate's spoken response.
        
        Args:
            recognized_text: Text recognized from candidate's speech
        """
        try:
            if not self.waiting_for_response or not recognized_text.strip():
                return
            
            logger.info(f"Candidate response received: {recognized_text[:50]}...")
            
            # Add to transcript
            self.interview_transcript.append({
                "timestamp": datetime.now().isoformat(),
                "speaker": "candidate",
                "content": recognized_text,
                "type": "response",
                "question": self.current_question
            })
            
            # Mark response as received
            self.waiting_for_response = False
            
        except Exception as e:
            logger.error(f"Error handling candidate response: {str(e)}")
    
    async def _wait_for_candidate_response(self, timeout_seconds: int = 60):
        """
        Wait for candidate to respond to the current question.
        
        Args:
            timeout_seconds: Maximum time to wait for response
        """
        try:
            start_time = asyncio.get_event_loop().time()
            
            while self.waiting_for_response and self.is_interview_active:
                # Check for timeout
                if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                    logger.warning("Timeout waiting for candidate response")
                    
                    # Prompt candidate
                    prompt_message = "I didn't catch that. Could you please repeat your answer?"
                    await self._speak_question(prompt_message)
                    
                    # Reset timeout
                    start_time = asyncio.get_event_loop().time()
                
                await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error waiting for candidate response: {str(e)}")
    
    async def _process_next_question(self):
        """Process the candidate's response and generate the next question."""
        try:
            if not self.interview_transcript:
                return
            
            # Get the last candidate response
            last_response = None
            for entry in reversed(self.interview_transcript):
                if entry["type"] == "response":
                    last_response = entry
                    break
            
            if not last_response:
                logger.warning("No candidate response found to process")
                return
            
            # Analyze the response
            analysis = await self.interview_ai.analyze_response(
                question=last_response["question"],
                answer=last_response["content"]
            )
            
            # Add analysis to transcript
            last_response["analysis"] = analysis
            
            # Generate next question
            next_question = await self.interview_ai.generate_next_question(analysis)
            
            # Speak the next question
            await self._speak_question(next_question)
            
        except Exception as e:
            logger.error(f"Error processing next question: {str(e)}")
    
    async def _end_interview_gracefully(self):
        """End the interview with a closing message."""
        try:
            closing_message = (
                "Thank you for taking the time to interview with us today. "
                "You should hear back about the next steps within a few days. "
                "Have a great day!"
            )
            
            await self.speech_processor.speak_in_meeting(closing_message, "friendly")
            
            # Wait a moment before leaving
            await asyncio.sleep(3)
            
            # Leave the meeting
            if self.meeting_bot:
                await self.meeting_bot.leave_meeting()
            
            self.is_interview_active = False
            
            logger.info("Interview ended gracefully")
            
        except Exception as e:
            logger.error(f"Error ending interview gracefully: {str(e)}")
    
    async def _cleanup_session(self):
        """Clean up resources and connections."""
        try:
            logger.info("Cleaning up interview session...")
            
            # Stop interview
            self.is_interview_active = False
            
            # Stop speech recognition
            if self.speech_processor.is_listening:
                await self.speech_processor.stop_continuous_recognition()
            
            # Leave meeting if still connected
            if self.meeting_bot and self.meeting_bot.is_in_meeting:
                await self.meeting_bot.leave_meeting()
            
            logger.info("Session cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during session cleanup: {str(e)}")
    
    async def handle_real_time_events(self):
        """Handle real-time events during the interview."""
        try:
            while self.is_interview_active:
                # Monitor meeting participants
                if self.meeting_bot:
                    participants = await self.meeting_bot.get_meeting_participants()
                    
                    # Check if candidate left the meeting
                    if len(participants) < 2:  # Bot + candidate
                        logger.warning("Candidate may have left the meeting")
                        # Could implement reconnection logic here
                
                # Monitor interview progress
                progress = self.interview_ai.get_conversation_summary()
                logger.debug(f"Interview progress: {progress}")
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
        except Exception as e:
            logger.error(f"Error handling real-time events: {str(e)}")
    
    def get_interview_results(self) -> Dict[str, Any]:
        """
        Get the complete interview results.
        
        Returns:
            Dictionary containing all interview data and results
        """
        return {
            "session_id": self.interview_session_id,
            "transcript": self.interview_transcript,
            "ai_assessment": self.interview_results,
            "conversation_summary": self.interview_ai.get_conversation_summary(),
            "session_metadata": {
                "start_time": self.interview_transcript[0]["timestamp"] if self.interview_transcript else None,
                "end_time": datetime.now().isoformat(),
                "total_exchanges": len(self.interview_transcript),
                "duration_minutes": settings.interview_duration_minutes
            }
        }
    
    def save_interview_results(self, filepath: str = None) -> str:
        """
        Save interview results to a file.
        
        Args:
            filepath: Optional custom filepath
            
        Returns:
            Path to the saved file
        """
        try:
            if filepath is None:
                filepath = f"interview_results_{self.interview_session_id}.json"
            
            results = self.get_interview_results()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Interview results saved to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving interview results: {str(e)}")
            return ""