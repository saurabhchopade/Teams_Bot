# Microsoft Teams Interview Bot with Direct Voice Integration

A comprehensive Python-based AI interview bot that can join Microsoft Teams meetings, conduct intelligent interviews using natural voice interaction, and provide detailed candidate assessments.

## 🚀 Features

### Core Capabilities
- **Direct Teams Integration**: Programmatically joins any Teams meeting using meeting links
- **Real-time Voice Interaction**: Speaks questions and listens to responses with natural voice processing
- **AI-Powered Interviews**: Uses OpenAI GPT for intelligent question generation and response analysis
- **Comprehensive Assessment**: Provides detailed candidate evaluations and hiring recommendations
- **Professional Audio Quality**: Advanced speech processing with noise reduction and echo cancellation

### Technical Highlights
- **Azure Integration**: Full integration with Microsoft Graph API, Azure Bot Framework, and Cognitive Services
- **Async Architecture**: High-performance asynchronous design for real-time operations
- **Robust Error Handling**: Comprehensive error handling and recovery mechanisms
- **Extensible Design**: Modular architecture for easy customization and extension

## 📋 Prerequisites

### Azure Services Required
1. **Azure AD App Registration** with the following permissions:
   - `OnlineMeetings.ReadWrite.All`
   - `Calls.AccessMedia.All`
   - `Calls.JoinGroupCall.All`
   - `CallRecords.Read.All`

2. **Azure Bot Framework** registration
3. **Azure Cognitive Services** (Speech Services)
4. **OpenAI API** access

### System Requirements
- Python 3.8+
- Windows/Linux/macOS
- Microphone and speakers (for local testing)
- Stable internet connection

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd teams-interview-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Azure and OpenAI credentials:
```env
# Azure AD Configuration
AZURE_CLIENT_ID=your-azure-client-id
AZURE_CLIENT_SECRET=your-azure-client-secret
AZURE_TENANT_ID=your-azure-tenant-id

# Azure Bot Framework
BOT_APP_ID=your-bot-app-id
BOT_APP_PASSWORD=your-bot-app-password
BOT_ENDPOINT=https://your-bot-endpoint.ngrok.io

# Azure Cognitive Services
AZURE_SPEECH_KEY=your-speech-service-key
AZURE_SPEECH_REGION=eastus

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
```

### 4. Setup Webhook Endpoint (Development)
For development, use ngrok to expose your local server:

```bash
# Install ngrok (if not already installed)
# Download from https://ngrok.com/

# Expose local port 5000
ngrok http 5000

# Copy the HTTPS URL to your .env file as BOT_ENDPOINT
```

## 🚀 Usage

### Basic Usage
```bash
python main.py \
  --meeting_url "https://teams.microsoft.com/l/meetup-join/19%3ameeting_..." \
  --candidate_name "John Doe" \
  --role "Senior Python Developer"
```

### Advanced Usage
```bash
python main.py \
  --meeting_url "https://teams.microsoft.com/l/meetup-join/..." \
  --candidate_name "Jane Smith" \
  --candidate_email "jane@example.com" \
  --role "Full Stack Developer" \
  --experience_level "senior" \
  --focus_areas "python" "react" "system_design" \
  --duration 60 \
  --log_level "DEBUG"
```

### Programmatic Usage
```python
from orchestrator.interview_orchestrator import InterviewBotOrchestrator

async def run_interview():
    orchestrator = InterviewBotOrchestrator()
    
    # Initialize the bot
    await orchestrator.initialize()
    
    # Configure interview
    candidate_info = {
        "name": "John Doe",
        "email": "john@example.com",
        "experience_level": "mid"
    }
    
    role_info = {
        "title": "Software Developer",
        "focus_areas": ["python", "algorithms"]
    }
    
    # Start interview
    success = await orchestrator.start_interview_session(
        meeting_url="https://teams.microsoft.com/l/meetup-join/...",
        candidate_info=candidate_info,
        role_info=role_info
    )
    
    if success:
        results = orchestrator.get_interview_results()
        print(f"Interview completed! Overall score: {results['ai_assessment']['overall_score']}")

# Run the interview
import asyncio
asyncio.run(run_interview())
```

## 🏗️ Architecture

### Component Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    Interview Orchestrator                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    Auth     │  │   Meeting   │  │   Speech    │         │
│  │  Handler    │  │     Bot     │  │ Processor   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Interview   │  │  Webhook    │  │   Utils     │         │
│  │     AI      │  │  Handler    │  │             │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Authentication Handler** (`auth/teams_auth.py`)
   - Azure AD authentication
   - Token management
   - Permission validation

2. **Meeting Bot** (`teams/meeting_bot.py`)
   - Teams meeting integration
   - Audio stream management
   - Participant monitoring

3. **Speech Processor** (`speech/speech_processor.py`)
   - Speech-to-text conversion
   - Text-to-speech synthesis
   - Audio quality optimization

4. **Interview AI** (`ai/interview_brain.py`)
   - Question generation
   - Response analysis
   - Performance assessment

5. **Orchestrator** (`orchestrator/interview_orchestrator.py`)
   - Main coordination logic
   - Interview flow management
   - Result compilation

## 🔧 Configuration

### Interview Settings
Customize interview behavior in `config/settings.py`:

```python
# Interview duration
INTERVIEW_DURATION_MINUTES = 45

# Maximum questions
MAX_QUESTIONS = 15

# AI model
OPENAI_MODEL = "gpt-4"

# Speech settings
AZURE_SPEECH_REGION = "eastus"
```

### Voice Configuration
Customize voice settings:

```python
speech_processor.configure_voice_settings(
    voice_name="en-US-AriaNeural",  # Professional female voice
    rate="medium",
    pitch="medium"
)
```

### Question Customization
Modify question templates in `ai/interview_brain.py`:

```python
self.question_templates = {
    "technical_skills": [
        "Explain your experience with [technology]",
        "How would you approach [technical challenge]?",
        # Add custom questions here
    ]
}
```

## 📊 Interview Results

The bot generates comprehensive interview results including:

### Assessment Categories
- **Technical Skills**: Depth of knowledge and practical experience
- **Communication**: Clarity and professional presentation
- **Problem Solving**: Analytical thinking and approach
- **Cultural Fit**: Team collaboration and adaptability

### Output Format
```json
{
  "session_id": "interview_20241201_143022",
  "overall_score": 8.2,
  "category_scores": {
    "technical_skills": 8.5,
    "communication": 8.0,
    "problem_solving": 8.3,
    "cultural_fit": 7.8
  },
  "recommendation": "hire",
  "strengths": [
    "Strong technical foundation",
    "Clear communication style",
    "Good problem-solving approach"
  ],
  "areas_for_improvement": [
    "Could elaborate more on system design",
    "More specific examples would be helpful"
  ],
  "transcript": [...],
  "session_metadata": {...}
}
```

## 🧪 Testing

### Run Unit Tests
```bash
pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Test authentication
pytest tests/test_interview_bot.py::TestTeamsAuthenticator -v

# Test speech processing
pytest tests/test_interview_bot.py::TestSpeechProcessor -v

# Test AI components
pytest tests/test_interview_bot.py::TestInterviewAI -v
```

### Integration Testing
```bash
# Run integration tests (requires valid credentials)
pytest tests/test_interview_bot.py::TestIntegration -v
```

## 🚨 Troubleshooting

### Common Issues

#### Authentication Errors
```
Error: Failed to acquire access token
```
**Solution**: Verify Azure AD app registration and permissions

#### Meeting Join Failures
```
Error: Failed to join Teams meeting
```
**Solutions**:
- Verify meeting URL format
- Check bot permissions
- Ensure meeting is active

#### Speech Recognition Issues
```
Error: Speech recognition not working
```
**Solutions**:
- Check microphone permissions
- Verify Azure Speech Service credentials
- Test audio input/output devices

#### API Rate Limits
```
Error: OpenAI API rate limit exceeded
```
**Solution**: Implement request throttling or upgrade API plan

### Debug Mode
Enable detailed logging:
```bash
python main.py --log_level DEBUG --meeting_url "..." --candidate_name "..."
```

### Health Check
Test webhook endpoints:
```bash
curl http://localhost:5000/health
```

## 🔒 Security Considerations

### Data Privacy
- All audio is processed in real-time and not stored permanently
- Interview transcripts are saved locally only
- Candidate information is handled according to privacy policies

### Access Control
- Bot requires explicit meeting invitation or join permissions
- All API calls use secure authentication tokens
- Webhook endpoints include security validation

### Compliance
- Ensure compliance with local recording and privacy laws
- Obtain candidate consent for AI-powered interviews
- Follow organizational data handling policies

## 🚀 Deployment

### Production Deployment

#### Azure Container Instances
```bash
# Build Docker image
docker build -t teams-interview-bot .

# Deploy to Azure
az container create \
  --resource-group myResourceGroup \
  --name interview-bot \
  --image teams-interview-bot \
  --environment-variables \
    AZURE_CLIENT_ID=... \
    AZURE_CLIENT_SECRET=... \
    # ... other environment variables
```

#### Azure App Service
```bash
# Deploy using Azure CLI
az webapp up \
  --name teams-interview-bot \
  --resource-group myResourceGroup \
  --runtime "PYTHON|3.9"
```

### Environment-Specific Configuration
- **Development**: Use ngrok for webhook endpoints
- **Staging**: Deploy to Azure with test credentials
- **Production**: Use production Azure resources with monitoring

## 📈 Monitoring and Analytics

### Logging
The bot provides comprehensive logging:
- Authentication events
- Meeting join/leave events
- Speech recognition accuracy
- AI response quality
- Error tracking

### Metrics
Track key performance indicators:
- Interview completion rate
- Average interview duration
- Speech recognition accuracy
- Candidate satisfaction scores

### Health Monitoring
```bash
# Check bot health
curl https://your-bot-endpoint.azurewebsites.net/health
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install development dependencies: `pip install -r requirements-dev.txt`
4. Run tests: `pytest`
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Add comprehensive docstrings
- Maintain test coverage above 80%

### Adding New Features
1. Create feature branch
2. Implement feature with tests
3. Update documentation
4. Submit pull request with description

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [Azure Bot Framework Documentation](https://docs.microsoft.com/en-us/azure/bot-service/)
- [Microsoft Graph API Documentation](https://docs.microsoft.com/en-us/graph/)
- [Azure Cognitive Services Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/)

### Community
- GitHub Issues for bug reports
- GitHub Discussions for questions
- Stack Overflow with tag `teams-interview-bot`

### Professional Support
For enterprise support and custom implementations, contact the development team.

---

**Note**: This bot is designed for professional interview scenarios. Always ensure compliance with local laws and organizational policies regarding AI-powered interviews and data privacy.