"""Main entry point for the Microsoft Teams Interview Bot."""

import asyncio
import logging
import argparse
import sys
from typing import Dict, Optional
from dotenv import load_dotenv

from orchestrator.interview_orchestrator import InterviewBotOrchestrator
from config.settings import settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('interview_bot.log')
    ]
)

logger = logging.getLogger(__name__)


async def run_interview_bot(
    meeting_url: str,
    candidate_name: str,
    candidate_email: str = None,
    role_title: str = "Software Developer",
    experience_level: str = "mid",
    focus_areas: list = None,
    interview_duration: int = None
) -> bool:
    """
    Run the interview bot for a single interview session.
    
    Args:
        meeting_url: Teams meeting join URL
        candidate_name: Name of the candidate
        candidate_email: Email of the candidate (optional)
        role_title: Title of the role being interviewed for
        experience_level: Experience level (junior, mid, senior)
        focus_areas: List of technical areas to focus on
        interview_duration: Duration in minutes (optional)
        
    Returns:
        True if interview completed successfully
    """
    orchestrator = None
    
    try:
        logger.info("Starting Microsoft Teams Interview Bot")
        logger.info(f"Candidate: {candidate_name}")
        logger.info(f"Role: {role_title}")
        logger.info(f"Meeting URL: {meeting_url[:50]}...")
        
        # Initialize orchestrator
        orchestrator = InterviewBotOrchestrator()
        
        if not await orchestrator.initialize():
            logger.error("Failed to initialize interview bot")
            return False
        
        # Prepare candidate information
        candidate_info = {
            "name": candidate_name,
            "email": candidate_email,
            "experience_level": experience_level
        }
        
        # Prepare role information
        role_info = {
            "title": role_title,
            "level": experience_level,
            "focus_areas": focus_areas or ["general programming", "problem solving"]
        }
        
        # Override duration if specified
        if interview_duration:
            settings.interview_duration_minutes = interview_duration
        
        # Start the interview session
        success = await orchestrator.start_interview_session(
            meeting_url=meeting_url,
            candidate_info=candidate_info,
            role_info=role_info
        )
        
        if success:
            # Save interview results
            results_file = orchestrator.save_interview_results()
            logger.info(f"Interview completed successfully. Results saved to: {results_file}")
            
            # Print summary
            results = orchestrator.get_interview_results()
            print_interview_summary(results)
            
            return True
        else:
            logger.error("Interview session failed")
            return False
            
    except KeyboardInterrupt:
        logger.info("Interview interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in interview bot: {str(e)}")
        return False
    finally:
        # Cleanup
        if orchestrator:
            await orchestrator._cleanup_session()


def _validate_environment() -> bool:
    """
    Validate that all required environment variables are set.
    
    Returns:
        True if environment is valid
    """
    try:
        required_vars = [
            'AZURE_CLIENT_ID',
            'AZURE_CLIENT_SECRET', 
            'AZURE_TENANT_ID',
            'AZURE_SPEECH_KEY',
            'AZURE_SPEECH_REGION',
            'GOOGLE_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(settings, var.lower(), None):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        # Validate Azure Speech region format
        if not settings.azure_speech_region or len(settings.azure_speech_region) < 2:
            logger.error("Invalid Azure Speech region")
            return False
        
        logger.info("Environment validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Environment validation error: {str(e)}")
        return False


def print_interview_summary(results: Dict):
    """Print a summary of the interview results."""
    try:
        print("\n" + "="*60)
        print("INTERVIEW SUMMARY")
        print("="*60)
        
        metadata = results.get("session_metadata", {})
        ai_assessment = results.get("ai_assessment", {})
        
        print(f"Session ID: {results.get('session_id', 'N/A')}")
        print(f"Duration: {metadata.get('duration_minutes', 'N/A')} minutes")
        print(f"Total Exchanges: {metadata.get('total_exchanges', 'N/A')}")
        
        if ai_assessment:
            print(f"\nOverall Score: {ai_assessment.get('overall_score', 'N/A')}/10")
            print(f"Recommendation: {ai_assessment.get('recommendation', 'N/A').upper()}")
            
            category_scores = ai_assessment.get('category_scores', {})
            if category_scores:
                print("\nCategory Scores:")
                for category, score in category_scores.items():
                    print(f"  {category.replace('_', ' ').title()}: {score}/10")
            
            strengths = ai_assessment.get('strengths', [])
            if strengths:
                print("\nKey Strengths:")
                for strength in strengths[:3]:  # Top 3
                    print(f"  • {strength}")
            
            improvements = ai_assessment.get('areas_for_improvement', [])
            if improvements:
                print("\nAreas for Improvement:")
                for improvement in improvements[:3]:  # Top 3
                    print(f"  • {improvement}")
        
        print("="*60)
        
    except Exception as e:
        logger.error(f"Error printing interview summary: {str(e)}")


def validate_meeting_url(url: str) -> bool:
    """Validate that the meeting URL is a valid Teams meeting URL."""
    teams_patterns = [
        "teams.microsoft.com",
        "teams.live.com",
        "meetup-join"
    ]
    
    return any(pattern in url.lower() for pattern in teams_patterns)


def main():
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Microsoft Teams Interview Bot with AI-powered conversations"
    )
    
    # Required arguments
    parser.add_argument(
        "--meeting_url",
        required=True,
        help="Microsoft Teams meeting join URL"
    )
    
    parser.add_argument(
        "--candidate_name",
        required=True,
        help="Name of the candidate being interviewed"
    )
    
    # Optional arguments
    parser.add_argument(
        "--candidate_email",
        help="Email address of the candidate"
    )
    
    parser.add_argument(
        "--role",
        default="Software Developer",
        help="Role/position being interviewed for (default: Software Developer)"
    )
    
    parser.add_argument(
        "--experience_level",
        choices=["junior", "mid", "senior"],
        default="mid",
        help="Experience level of the candidate (default: mid)"
    )
    
    parser.add_argument(
        "--focus_areas",
        nargs="+",
        help="Technical areas to focus on (e.g., python javascript react)"
    )
    
    parser.add_argument(
        "--duration",
        type=int,
        help="Interview duration in minutes (default: from config)"
    )
    
    parser.add_argument(
        "--log_level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate meeting URL
    if not validate_meeting_url(args.meeting_url):
        print("Error: Invalid Teams meeting URL provided")
        print("Please provide a valid Microsoft Teams meeting join URL")
        sys.exit(1)
    
    # Update log level if specified
    if args.log_level:
        logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Print startup information
    print("Microsoft Teams Interview Bot")
    print("="*40)
    print(f"Candidate: {args.candidate_name}")
    print(f"Role: {args.role}")
    print(f"Experience Level: {args.experience_level}")
    if args.focus_areas:
        print(f"Focus Areas: {', '.join(args.focus_areas)}")
    print(f"Duration: {args.duration or settings.interview_duration_minutes} minutes")
    print("="*40)
    print()
    
    # Run the interview bot
    try:
        success = asyncio.run(run_interview_bot(
            meeting_url=args.meeting_url,
            candidate_name=args.candidate_name,
            candidate_email=args.candidate_email,
            role_title=args.role,
            experience_level=args.experience_level,
            focus_areas=args.focus_areas,
            interview_duration=args.duration
        ))
        
        if success:
            print("\nInterview completed successfully!")
            sys.exit(0)
        else:
            print("\nInterview failed. Check logs for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nInterview interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()