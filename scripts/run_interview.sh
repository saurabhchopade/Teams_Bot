#!/bin/bash

# Microsoft Teams Interview Bot - Quick Start Script
# This script provides an easy way to run interviews

set -e

echo "🤖 Microsoft Teams Interview Bot"
echo "==============================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

# Load environment variables
source .env

# Check required environment variables
required_vars=("AZURE_CLIENT_ID" "AZURE_CLIENT_SECRET" "AZURE_TENANT_ID" "OPENAI_API_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables:"
    printf '   %s\n' "${missing_vars[@]}"
    echo "Please configure these in your .env file."
    exit 1
fi

echo "✅ Environment configuration validated"
echo ""

# Function to validate Teams meeting URL
validate_meeting_url() {
    local url=$1
    if [[ $url == *"teams.microsoft.com"* ]] || [[ $url == *"teams.live.com"* ]]; then
        return 0
    else
        return 1
    fi
}

# Interactive mode if no arguments provided
if [ $# -eq 0 ]; then
    echo "🎯 Interactive Interview Setup"
    echo "=============================="
    
    # Get meeting URL
    while true; do
        read -p "📅 Teams Meeting URL: " MEETING_URL
        if validate_meeting_url "$MEETING_URL"; then
            break
        else
            echo "❌ Invalid Teams meeting URL. Please provide a valid Teams meeting link."
        fi
    done
    
    # Get candidate name
    read -p "👤 Candidate Name: " CANDIDATE_NAME
    
    # Get candidate email (optional)
    read -p "📧 Candidate Email (optional): " CANDIDATE_EMAIL
    
    # Get role
    read -p "💼 Role (default: Software Developer): " ROLE
    ROLE=${ROLE:-"Software Developer"}
    
    # Get experience level
    echo "📊 Experience Level:"
    echo "   1) Junior"
    echo "   2) Mid (default)"
    echo "   3) Senior"
    read -p "Select (1-3): " LEVEL_CHOICE
    
    case $LEVEL_CHOICE in
        1) EXPERIENCE_LEVEL="junior" ;;
        3) EXPERIENCE_LEVEL="senior" ;;
        *) EXPERIENCE_LEVEL="mid" ;;
    esac
    
    # Get focus areas
    echo "🎯 Technical Focus Areas (space-separated, optional):"
    echo "   Examples: python javascript react nodejs algorithms system_design"
    read -p "Focus Areas: " FOCUS_AREAS_INPUT
    
    # Convert to array
    if [ -n "$FOCUS_AREAS_INPUT" ]; then
        read -ra FOCUS_AREAS <<< "$FOCUS_AREAS_INPUT"
    else
        FOCUS_AREAS=()
    fi
    
    # Get duration
    read -p "⏱️  Interview Duration (minutes, default: 45): " DURATION
    DURATION=${DURATION:-45}
    
    # Get log level
    echo "📝 Log Level:"
    echo "   1) INFO (default)"
    echo "   2) DEBUG"
    echo "   3) WARNING"
    read -p "Select (1-3): " LOG_CHOICE
    
    case $LOG_CHOICE in
        2) LOG_LEVEL="DEBUG" ;;
        3) LOG_LEVEL="WARNING" ;;
        *) LOG_LEVEL="INFO" ;;
    esac
    
    echo ""
    echo "📋 Interview Configuration:"
    echo "=========================="
    echo "Candidate: $CANDIDATE_NAME"
    echo "Email: ${CANDIDATE_EMAIL:-"Not provided"}"
    echo "Role: $ROLE"
    echo "Experience: $EXPERIENCE_LEVEL"
    echo "Focus Areas: ${FOCUS_AREAS[*]:-"General"}"
    echo "Duration: $DURATION minutes"
    echo "Log Level: $LOG_LEVEL"
    echo ""
    
    read -p "Start interview? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo "Interview cancelled."
        exit 0
    fi
    
    # Build command
    CMD="python main.py --meeting_url \"$MEETING_URL\" --candidate_name \"$CANDIDATE_NAME\" --role \"$ROLE\" --experience_level \"$EXPERIENCE_LEVEL\" --duration $DURATION --log_level $LOG_LEVEL"
    
    if [ -n "$CANDIDATE_EMAIL" ]; then
        CMD="$CMD --candidate_email \"$CANDIDATE_EMAIL\""
    fi
    
    if [ ${#FOCUS_AREAS[@]} -gt 0 ]; then
        CMD="$CMD --focus_areas ${FOCUS_AREAS[*]}"
    fi
    
else
    # Command line mode
    CMD="python main.py $*"
fi

echo "🚀 Starting interview..."
echo "Command: $CMD"
echo ""

# Start webhook server in background
echo "🌐 Starting webhook server..."
python -m webhooks.teams_webhook &
WEBHOOK_PID=$!

# Wait for webhook server to start
sleep 3

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🧹 Cleaning up..."
    if [ -n "$WEBHOOK_PID" ]; then
        kill $WEBHOOK_PID 2>/dev/null || true
    fi
    echo "✅ Cleanup completed"
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Run the interview
echo "🎤 Starting interview bot..."
eval $CMD

echo ""
echo "✅ Interview completed!"
echo ""
echo "📊 Results saved to the current directory"
echo "📋 Check the logs for detailed information"