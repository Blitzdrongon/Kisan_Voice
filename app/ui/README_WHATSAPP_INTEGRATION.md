# KisanVoice WhatsApp Bot Integration

This document describes the integration of the KisanVoice AI workflow into a WhatsApp bot using Twilio.

## Overview

The `whatsapp_test.py` file has been enhanced to include the full KisanVoice AI workflow, providing:

- 🌾 **Agricultural AI Conversations**: Intelligent responses about farming, crops, and agriculture
- 🖼️ **Image Analysis**: Analyze crop photos, plant diseases, and agricultural images
- 🎤 **Voice Transcription**: Convert voice messages to text and respond intelligently
- 💬 **Multilingual Support**: Support for Kannada and English languages
- 🧠 **Conversation Memory**: Remember previous conversations and context
- 🌤️ **Weather Information**: Provide weather updates and agricultural advice

## Features

### 1. Text Conversations
- Natural language processing for agricultural queries
- Context-aware responses based on conversation history
- Multilingual support (Kannada/English)

### 2. Image Analysis
- Upload crop photos for disease identification
- Plant growth analysis
- Agricultural image interpretation
- Handled by KisanVoice workflow nodes

### 3. Voice Messages
- Automatic transcription of voice messages
- Voice-to-text conversion handled by workflow
- Intelligent responses to spoken queries

### 4. Memory & Context
- Conversation history tracking
- User session management
- Contextual responses based on previous interactions

## Architecture

```
WhatsApp Message → Twilio → Flask App → KisanVoice Workflow
                                                      ↓
                                              AI Processing
                                                      ↓
                                              Response Generation
                                                      ↓
                                              WhatsApp Response
```

## Components

### 1. MessageProcessor
- Handles incoming WhatsApp messages
- Integrates with KisanVoice workflow
- Manages user sessions and conversation history
- Processes text, images, and voice messages

### 2. KisanVoice Workflow Integration
- Uses the full LangGraph workflow
- Includes conversation nodes for different intents
- Memory management for persistent conversations
- AI service integration (Groq, ElevenLabs, Weather)

### 3. Media Handling
- Downloads and processes media from WhatsApp
- Image analysis using AI services
- Voice transcription capabilities
- File management and cleanup

## API Endpoints

### POST /whatsapp
- **Purpose**: Twilio webhook endpoint for incoming WhatsApp messages
- **Input**: Twilio webhook payload
- **Output**: TwiML response for WhatsApp

### GET /health
- **Purpose**: Health check endpoint
- **Output**: Service status and configuration info

### GET /stats
- **Purpose**: Usage statistics
- **Output**: Active sessions and conversation counts

## Configuration

### Environment Variables
```bash
# Twilio Configuration
TWILIO_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# KisanVoice AI Services
GROQ_API_KEY=your_groq_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
```

### File Structure
```
KisanVoice/app/ui/
├── whatsapp_test.py              # Main WhatsApp bot with KisanVoice integration
├── test_whatsapp_integration.py  # Integration test script
├── README_WHATSAPP_INTEGRATION.md # This documentation
└── uploads/                      # Directory for media files
```

## Usage

### 1. Start the Bot
```bash
cd KisanVoice/app/ui
python whatsapp_test.py
```

### 2. Configure Twilio Webhook
- Set webhook URL to: `https://your-domain.com/whatsapp`
- Use HTTP POST method
- Configure for WhatsApp messages

### 3. Test the Integration
```bash
python test_whatsapp_integration.py
```

## Message Flow

### Text Messages
1. User sends text message to WhatsApp
2. Twilio forwards to webhook endpoint
3. MessageProcessor detects language
4. KisanVoice workflow processes the message
5. AI generates contextual response
6. Response sent back via WhatsApp

### Image Messages
1. User sends image to WhatsApp
2. Image downloaded and saved locally
3. Image path passed to KisanVoice workflow
4. Workflow nodes handle image analysis automatically
5. Agricultural advice/analysis sent as response

### Voice Messages
1. User sends voice message to WhatsApp
2. Audio file downloaded and saved
3. Audio path passed to KisanVoice workflow
4. Workflow nodes handle transcription and processing
5. AI response sent back via WhatsApp

## Example Conversations

### Kannada Conversation
```
User: ನಮಸ್ಕಾರ, ನನ್ನ ಬತ್ತದ ಬೆಳೆ ಹೇಗಿದೆ?
Bot: ನಮಸ್ಕಾರ! ನಿಮ್ಮ ಬತ್ತದ ಬೆಳೆಯ ಬಗ್ಗೆ ಮಾಹಿತಿ ನೀಡಲು, ದಯವಿಟ್ಟು ನಿಮ್ಮ ಬೆಳೆಯ ಚಿತ್ರವನ್ನು ಕಳುಹಿಸಿ. ನಾನು ರೋಗಗಳು, ಕೀಟಗಳು, ಅಥವಾ ಪೋಷಕಾಂಶದ ಕೊರತೆಯನ್ನು ಗುರುತಿಸಲು ಸಹಾಯ ಮಾಡಬಹುದು.
```

### English Conversation
```
User: What's the weather like for farming today?
Bot: I'd be happy to help with weather information for farming! To provide accurate weather data, I'll need to know your location. Could you please share your city or region? I can then provide current weather conditions and farming recommendations.
```

### Image Analysis
```
User: [Sends image of crop with yellow leaves]
Bot: ಚಿತ್ರ ವಿಶ್ಲೇಷಣೆ: ನಿಮ್ಮ ಬೆಳೆಯಲ್ಲಿ ಹಳದಿ ಎಲೆಗಳು ಕಾಣುತ್ತಿವೆ. ಇದು ಸಾಮಾನ್ಯವಾಗಿ ಪೋಷಕಾಂಶದ ಕೊರತೆ ಅಥವಾ ರೋಗದ ಸೂಚನೆಯಾಗಿರಬಹುದು. ನಿಖರವಾದ ರೋಗನಿರ್ಣಯಕ್ಕಾಗಿ, ದಯವಿಟ್ಟು ಹೆಚ್ಚು ವಿವರಗಳನ್ನು ನೀಡಿ.
```

## Error Handling

The bot includes comprehensive error handling:

- **Service Unavailable**: Graceful fallback when AI services are down
- **Invalid Media**: Clear error messages for unsupported file types
- **Transcription Failures**: Helpful messages when voice transcription fails
- **Network Issues**: Retry mechanisms and user-friendly error messages

## Monitoring

### Health Check
```bash
curl http://localhost:5000/health
```

### Statistics
```bash
curl http://localhost:5000/stats
```

## Development

### Adding New Features
1. Extend the `MessageProcessor` class
2. Add new conversation nodes to the workflow
3. Update the intent classification logic
4. Test with the integration test script

### Debugging
- Check logs for detailed error information
- Use the test script to verify components
- Monitor the health endpoint for service status

## Deployment

### Production Considerations
- Use a production WSGI server (Gunicorn)
- Set up proper logging
- Configure environment variables securely
- Use HTTPS for webhook endpoints
- Implement rate limiting
- Set up monitoring and alerting

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "whatsapp_test.py"]
```

## Support

For issues or questions:
1. Check the logs for error details
2. Verify environment variable configuration
3. Test individual components using the test script
4. Review the KisanVoice workflow documentation

## License

This integration is part of the KisanVoice project and follows the same licensing terms.
