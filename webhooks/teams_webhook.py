"""Flask webhook handler for Teams callbacks and events."""

import logging
import json
from datetime import datetime
from flask import Flask, request, jsonify
from config.settings import settings

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = settings.bot_app_password


class TeamsWebhookHandler:
    """Handles incoming webhooks from Microsoft Teams and Azure services."""
    
    def __init__(self):
        """Initialize the webhook handler."""
        self.active_calls = {}
        self.event_callbacks = {}
    
    def register_callback(self, event_type: str, callback):
        """Register a callback for specific event types."""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)
    
    def trigger_callbacks(self, event_type: str, data: dict):
        """Trigger registered callbacks for an event type."""
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in callback for {event_type}: {str(e)}")


# Global webhook handler instance
webhook_handler = TeamsWebhookHandler()


@app.route('/webhook/teams', methods=['POST'])
def handle_teams_callback():
    """Handle incoming Teams bot framework callbacks."""
    try:
        data = request.get_json()
        
        if not data:
            logger.warning("Received empty Teams callback")
            return jsonify({"status": "error", "message": "No data received"}), 400
        
        event_type = data.get('type', 'unknown')
        logger.info(f"Received Teams callback: {event_type}")
        
        # Handle different types of Teams events
        if event_type == 'message':
            return handle_message_event(data)
        elif event_type == 'conversationUpdate':
            return handle_conversation_update(data)
        elif event_type == 'invoke':
            return handle_invoke_event(data)
        else:
            logger.info(f"Unhandled Teams event type: {event_type}")
            return jsonify({"status": "ok"}), 200
            
    except Exception as e:
        logger.error(f"Error handling Teams callback: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/webhook/calls', methods=['POST'])
def handle_call_callback():
    """Handle incoming call-related callbacks from Microsoft Graph."""
    try:
        data = request.get_json()
        
        if not data:
            logger.warning("Received empty call callback")
            return jsonify({"status": "error", "message": "No data received"}), 400
        
        # Extract call information
        call_id = data.get('callId')
        event_type = data.get('eventType', 'unknown')
        
        logger.info(f"Received call callback - Call ID: {call_id}, Event: {event_type}")
        
        # Handle different call events
        if event_type == 'callEstablished':
            return handle_call_established(data)
        elif event_type == 'callTerminated':
            return handle_call_terminated(data)
        elif event_type == 'participantJoined':
            return handle_participant_joined(data)
        elif event_type == 'participantLeft':
            return handle_participant_left(data)
        elif event_type == 'mediaReceived':
            return handle_media_received(data)
        else:
            logger.info(f"Unhandled call event type: {event_type}")
            return jsonify({"status": "ok"}), 200
            
    except Exception as e:
        logger.error(f"Error handling call callback: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/webhook/speech', methods=['POST'])
def handle_speech_events():
    """Handle speech recognition and synthesis events."""
    try:
        data = request.get_json()
        
        if not data:
            logger.warning("Received empty speech callback")
            return jsonify({"status": "error", "message": "No data received"}), 400
        
        event_type = data.get('eventType', 'unknown')
        logger.info(f"Received speech callback: {event_type}")
        
        # Handle speech events
        if event_type == 'speechRecognized':
            return handle_speech_recognized(data)
        elif event_type == 'speechSynthesized':
            return handle_speech_synthesized(data)
        elif event_type == 'audioStreamStarted':
            return handle_audio_stream_started(data)
        elif event_type == 'audioStreamStopped':
            return handle_audio_stream_stopped(data)
        else:
            logger.info(f"Unhandled speech event type: {event_type}")
            return jsonify({"status": "ok"}), 200
            
    except Exception as e:
        logger.error(f"Error handling speech callback: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


def handle_message_event(data: dict):
    """Handle Teams message events."""
    try:
        message_text = data.get('text', '')
        sender = data.get('from', {})
        
        logger.info(f"Message from {sender.get('name', 'Unknown')}: {message_text}")
        
        # Trigger callbacks
        webhook_handler.trigger_callbacks('message', data)
        
        # Respond to the message if needed
        response = {
            "type": "message",
            "text": "Thank you for your message. The interview bot is currently active."
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error handling message event: {str(e)}")
        return jsonify({"status": "error"}), 500


def handle_conversation_update(data: dict):
    """Handle Teams conversation update events."""
    try:
        members_added = data.get('membersAdded', [])
        members_removed = data.get('membersRemoved', [])
        
        for member in members_added:
            logger.info(f"Member joined: {member.get('name', 'Unknown')}")
        
        for member in members_removed:
            logger.info(f"Member left: {member.get('name', 'Unknown')}")
        
        # Trigger callbacks
        webhook_handler.trigger_callbacks('conversationUpdate', data)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Error handling conversation update: {str(e)}")
        return jsonify({"status": "error"}), 500


def handle_invoke_event(data: dict):
    """Handle Teams invoke events."""
    try:
        invoke_name = data.get('name', '')
        invoke_value = data.get('value', {})
        
        logger.info(f"Invoke event: {invoke_name}")
        
        # Trigger callbacks
        webhook_handler.trigger_callbacks('invoke', data)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Error handling invoke event: {str(e)}")
        return jsonify({"status": "error"}), 500


def handle_call_established(data: dict):
    """Handle call established events."""
    try:
        call_id = data.get('callId')
        webhook_handler.active_calls[call_id] = {
            "established_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        logger.info(f"Call established: {call_id}")
        
        # Trigger callbacks
        webhook_handler.trigger_callbacks('callEstablished', data)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Error handling call established: {str(e)}")
        return jsonify({"status": "error"}), 500


def handle_call_terminated(data: dict):
    """Handle call terminated events."""
    try:
        call_id = data.get('callId')
        
        if call_id in webhook_handler.active_calls:
            webhook_handler.active_calls[call_id]["status"] = "terminated"
            webhook_handler.active_calls[call_id]["terminated_at"] = datetime.now().isoformat()
        
        logger.info(f"Call terminated: {call_id}")
        
        # Trigger callbacks
        webhook_handler.trigger_callbacks('callTerminated', data)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Error handling call terminated: {str(e)}")
        return jsonify({"status": "error"}), 500


def handle_participant_joined(data: dict):
    """Handle participant joined events."""
    try:
        participant = data.get('participant', {})
        call_id = data.get('callId')
        
        logger.info(f"Participant joined call {call_id}: {participant.get('displayName', 'Unknown')}")
        
        # Trigger callbacks
        webhook_handler.trigger_callbacks('participantJoined', data)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Error handling participant joined: {str(e)}")
        return jsonify({"status": "error"}), 500


def handle_participant_left(data: dict):
    """Handle participant left events."""
    try:
        participant = data.get('participant', {})
        call_id = data.get('callId')
        
        logger.info(f"Participant left call {call_id}: {participant.get('displayName', 'Unknown')}")
        
        # Trigger callbacks
        webhook_handler.trigger_callbacks('participantLeft', data)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Error handling participant left: {str(e)}")
        return jsonify({"status": "error"}), 500


def handle_media_received(data: dict):
    """Handle media received events."""
    try:
        media_type = data.get('mediaType', 'unknown')
        call_id = data.get('callId')
        
        logger.debug(f"Media received for call {call_id}: {media_type}")
        
        # Trigger callbacks
        webhook_handler.trigger_callbacks('mediaReceived', data)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Error handling media received: {str(e)}")
        return jsonify({"status": "error"}), 500


def handle_speech_recognized(data: dict):
    """Handle speech recognition events."""
    try:
        recognized_text = data.get('text', '')
        confidence = data.get('confidence', 0.0)
        
        logger.info(f"Speech recognized (confidence: {confidence}): {recognized_text}")
        
        # Trigger callbacks
        webhook_handler.trigger_callbacks('speechRecognized', data)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Error handling speech recognized: {str(e)}")
        return jsonify({"status": "error"}), 500


def handle_speech_synthesized(data: dict):
    """Handle speech synthesis events."""
    try:
        text = data.get('text', '')
        duration = data.get('duration', 0)
        
        logger.info(f"Speech synthesized ({duration}ms): {text[:50]}...")
        
        # Trigger callbacks
        webhook_handler.trigger_callbacks('speechSynthesized', data)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Error handling speech synthesized: {str(e)}")
        return jsonify({"status": "error"}), 500


def handle_audio_stream_started(data: dict):
    """Handle audio stream started events."""
    try:
        stream_id = data.get('streamId', 'unknown')
        
        logger.info(f"Audio stream started: {stream_id}")
        
        # Trigger callbacks
        webhook_handler.trigger_callbacks('audioStreamStarted', data)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Error handling audio stream started: {str(e)}")
        return jsonify({"status": "error"}), 500


def handle_audio_stream_stopped(data: dict):
    """Handle audio stream stopped events."""
    try:
        stream_id = data.get('streamId', 'unknown')
        
        logger.info(f"Audio stream stopped: {stream_id}")
        
        # Trigger callbacks
        webhook_handler.trigger_callbacks('audioStreamStopped', data)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Error handling audio stream stopped: {str(e)}")
        return jsonify({"status": "error"}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_calls": len(webhook_handler.active_calls)
    }), 200


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False
    )