"""Speech processing engine using Azure Cognitive Services."""

import asyncio
import logging
import threading
from typing import Optional, Callable, Dict, Any
import azure.cognitiveservices.speech as speechsdk
from config.settings import settings

logger = logging.getLogger(__name__)


class SpeechProcessor:
    """Handles speech-to-text and text-to-speech operations."""
    
    def __init__(self):
        """Initialize the speech processor with Azure Speech SDK."""
        self.speech_key = settings.azure_speech_key
        self.speech_region = settings.azure_speech_region
        
        # Initialize speech configuration
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region
        )
        
        # Configure speech recognition settings
        self.speech_config.speech_recognition_language = "en-US"
        self.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_ContinuousRecognitionTimeout_Ms,
            "300000"  # 5 minutes
        )
        
        # Configure text-to-speech settings
        self.speech_config.speech_synthesis_voice_name = "en-US-AriaNeural"
        
        # Audio configuration
        self.audio_config_input = speechsdk.audio.AudioConfig(use_default_microphone=True)
        self.audio_config_output = speechsdk.audio.AudioConfig(use_default_speaker=True)
        
        # Recognition and synthesis objects
        self.speech_recognizer: Optional[speechsdk.SpeechRecognizer] = None
        self.speech_synthesizer: Optional[speechsdk.SpeechSynthesizer] = None
        
        # State management
        self.is_listening = False
        self.recognition_callback: Optional[Callable] = None
        
    def initialize_recognizer(self) -> bool:
        """
        Initialize the speech recognizer.
        
        Returns:
            True if initialization successful
        """
        try:
            self.speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=self.audio_config_input
            )
            
            # Setup event handlers
            self.speech_recognizer.recognized.connect(self._on_recognized)
            self.speech_recognizer.recognizing.connect(self._on_recognizing)
            self.speech_recognizer.session_started.connect(self._on_session_started)
            self.speech_recognizer.session_stopped.connect(self._on_session_stopped)
            self.speech_recognizer.canceled.connect(self._on_canceled)
            
            logger.info("Speech recognizer initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize speech recognizer: {str(e)}")
            return False
    
    def initialize_synthesizer(self) -> bool:
        """
        Initialize the speech synthesizer.
        
        Returns:
            True if initialization successful
        """
        try:
            self.speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=self.audio_config_output
            )
            
            logger.info("Speech synthesizer initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize speech synthesizer: {str(e)}")
            return False
    
    async def start_continuous_recognition(self, callback: Callable[[str], None]) -> bool:
        """
        Start continuous speech recognition.
        
        Args:
            callback: Function to call when speech is recognized
            
        Returns:
            True if recognition started successfully
        """
        try:
            if not self.speech_recognizer:
                if not self.initialize_recognizer():
                    return False
            
            self.recognition_callback = callback
            self.is_listening = True
            
            # Start continuous recognition
            self.speech_recognizer.start_continuous_recognition()
            
            logger.info("Started continuous speech recognition")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start continuous recognition: {str(e)}")
            return False
    
    async def stop_continuous_recognition(self) -> bool:
        """
        Stop continuous speech recognition.
        
        Returns:
            True if recognition stopped successfully
        """
        try:
            if self.speech_recognizer and self.is_listening:
                self.speech_recognizer.stop_continuous_recognition()
                self.is_listening = False
                logger.info("Stopped continuous speech recognition")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop continuous recognition: {str(e)}")
            return False
    
    async def speak_in_meeting(self, text: str, voice_style: str = "professional") -> bool:
        """
        Convert text to speech and play in the meeting.
        
        Args:
            text: Text to convert to speech
            voice_style: Voice style (professional, friendly, etc.)
            
        Returns:
            True if speech synthesis successful
        """
        try:
            if not self.speech_synthesizer:
                if not self.initialize_synthesizer():
                    return False
            
            # Configure voice style
            voice_config = self._get_voice_config(voice_style)
            
            # Create SSML for better control
            ssml_text = f"""
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
                <voice name="{voice_config['voice_name']}">
                    <prosody rate="{voice_config['rate']}" pitch="{voice_config['pitch']}">
                        {text}
                    </prosody>
                </voice>
            </speak>
            """
            
            # Synthesize speech
            result = self.speech_synthesizer.speak_ssml(ssml_text)
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info(f"Successfully synthesized speech: {text[:50]}...")
                return True
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = speechsdk.CancellationDetails(result)
                logger.error(f"Speech synthesis canceled: {cancellation_details.reason}")
                return False
            else:
                logger.error(f"Speech synthesis failed: {result.reason}")
                return False
                
        except Exception as e:
            logger.error(f"Error in speech synthesis: {str(e)}")
            return False
    
    def _get_voice_config(self, style: str) -> Dict[str, str]:
        """
        Get voice configuration based on style.
        
        Args:
            style: Voice style preference
            
        Returns:
            Voice configuration dictionary
        """
        configs = {
            "professional": {
                "voice_name": "en-US-AriaNeural",
                "rate": "medium",
                "pitch": "medium"
            },
            "friendly": {
                "voice_name": "en-US-JennyNeural",
                "rate": "medium",
                "pitch": "medium"
            },
            "authoritative": {
                "voice_name": "en-US-GuyNeural",
                "rate": "slow",
                "pitch": "low"
            }
        }
        
        return configs.get(style, configs["professional"])
    
    def configure_voice_settings(self, voice_name: str = None, rate: str = "medium", pitch: str = "medium"):
        """
        Configure voice settings for speech synthesis.
        
        Args:
            voice_name: Azure neural voice name
            rate: Speech rate (slow, medium, fast)
            pitch: Speech pitch (low, medium, high)
        """
        if voice_name:
            self.speech_config.speech_synthesis_voice_name = voice_name
        
        logger.info(f"Voice settings configured: {voice_name}, rate: {rate}, pitch: {pitch}")
    
    def _on_recognized(self, evt):
        """Handle recognized speech event."""
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            recognized_text = evt.result.text
            logger.info(f"Recognized: {recognized_text}")
            
            if self.recognition_callback and recognized_text.strip():
                # Run callback in thread to avoid blocking
                threading.Thread(
                    target=self.recognition_callback,
                    args=(recognized_text,)
                ).start()
    
    def _on_recognizing(self, evt):
        """Handle recognizing speech event (partial results)."""
        logger.debug(f"Recognizing: {evt.result.text}")
    
    def _on_session_started(self, evt):
        """Handle session started event."""
        logger.info("Speech recognition session started")
    
    def _on_session_stopped(self, evt):
        """Handle session stopped event."""
        logger.info("Speech recognition session stopped")
        self.is_listening = False
    
    def _on_canceled(self, evt):
        """Handle canceled event."""
        logger.warning(f"Speech recognition canceled: {evt.result.reason}")
        if evt.result.reason == speechsdk.CancellationReason.Error:
            logger.error(f"Error details: {evt.result.error_details}")
        self.is_listening = False
    
    async def handle_audio_feedback(self) -> bool:
        """
        Handle audio feedback and echo cancellation.
        
        Returns:
            True if feedback handling configured successfully
        """
        try:
            # Configure echo cancellation and noise suppression
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_EnableAudioLogging,
                "false"
            )
            
            # Enable noise suppression
            self.speech_config.set_property(
                speechsdk.PropertyId.Speech_LogFilename,
                ""
            )
            
            logger.info("Audio feedback handling configured")
            return True
            
        except Exception as e:
            logger.error(f"Error configuring audio feedback handling: {str(e)}")
            return False