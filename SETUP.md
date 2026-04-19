# 🚀 KisanVoice Setup Guide

This guide will help you set up and run the KisanVoice chatbot on your system.

## 📋 Prerequisites

- **Docker & Docker Compose** installed on your system
- **Python 3.9+** (for local development)
- **API Keys** for the required services

## 🔑 Required API Keys

### 1. Groq API Key
- Visit [Groq Console](https://console.groq.com/)
- Create an account and get your API key
- This will be used for Llama-3.3-70b-versatile and Llama-3.2-90b-vision-preview

### 2. ElevenLabs API Key
- Visit [ElevenLabs](https://elevenlabs.io/)
- Create an account and get your API key
- This will be used for Text-to-Speech

### 3. OpenWeather API Key
- Visit [OpenWeather](https://openweathermap.org/api)
- Create an account and get your API key
- This will be used for weather information

### 4. WhatsApp Business API (Optional)
- Visit [Meta for Developers](https://developers.facebook.com/docs/whatsapp)
- Set up WhatsApp Business API
- Get your access token, phone number ID, and verify token

## 🐳 Quick Start with Docker

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd KisanVoice
```

### 2. Configure Environment
```bash
# Copy environment template
cp env.example .env

# Edit .env file with your API keys
nano .env
```

Fill in your API keys:
```env
GROQ_API_KEY=your_groq_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token_here
WHATSAPP_PHONE_NUMBER_ID=your_whatsapp_phone_number_id
WHATSAPP_VERIFY_TOKEN=your_whatsapp_verify_token
```

### 3. Run with Docker Compose
```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f kisanvoice
```

### 4. Access the Application
- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🖥️ Local Development Setup

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables
```bash
export GROQ_API_KEY="your_key_here"
export ELEVENLABS_API_KEY="your_key_here"
export OPENWEATHER_API_KEY="your_key_here"
export WHATSAPP_ACCESS_TOKEN="your_token_here"
export WHATSAPP_PHONE_NUMBER_ID="your_id_here"
export WHATSAPP_VERIFY_TOKEN="your_token_here"
```

### 4. Run Tests
```bash
python test_setup.py
```

### 5. Start the Application
```bash
# Start Chainlit UI
chainlit run ui/chainlit_app.py --host 0.0.0.0 --port 8000

# Or start FastAPI backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🔧 Configuration Options

### Language Settings
- **Default Language**: Set `DEFAULT_LANGUAGE` in `.env` (default: "kn" for Kannada)
- **Supported Languages**: Configure `SUPPORTED_LANGUAGES` in `.env`

### Model Configuration
- **Text Model**: `llama-3.3-70b-versatile` (via Groq)
- **Vision Model**: `llama-3.2-90b-vision-preview` (via Groq)
- **TTS Voice**: Configure `TTS_VOICE_ID` in `.env`

### Server Configuration
- **Host**: Set `HOST` in `.env` (default: 0.0.0.0)
- **Port**: Set `PORT` in `.env` (default: 8000)

## 📱 WhatsApp Integration

### 1. Webhook Setup
- Your webhook URL: `https://your-domain.com/whatsapp/webhook`
- Verify token: Use the same value as `WHATSAPP_VERIFY_TOKEN` in `.env`

### 2. Test WhatsApp Integration
```bash
# Send test message via API
curl -X POST "http://localhost:8000/whatsapp/send" \
  -H "Content-Type: application/json" \
  -d '{"to": "+1234567890", "message": "Hello from KisanVoice!", "language": "kn"}'
```

## 🌐 Production Deployment

### 1. Environment Variables
- Set `DEBUG=false` in production
- Use strong, unique values for all API keys
- Configure proper CORS origins

### 2. SSL/HTTPS
- Uncomment and configure HTTPS in `docker/nginx/nginx.conf`
- Add your SSL certificates
- Update domain names

### 3. Security
- Enable authentication if needed
- Configure rate limiting
- Set up proper logging and monitoring

### 4. Scaling
- Use multiple app instances behind load balancer
- Configure Redis clustering if needed
- Set up proper health checks

## 🧪 Testing

### 1. Basic Functionality
```bash
# Test configuration
python test_setup.py

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/info
```

### 2. Chat Testing
- Open http://localhost:8000 in your browser
- Try different languages (Kannada/English)
- Test image upload and analysis
- Test weather queries

### 3. API Testing
```bash
# Test chat endpoint
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "ಹವಾಮಾನ ಹೇಗಿದೆ?", "language": "kn"}'
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Docker Compose Issues
```bash
# Check service logs
docker-compose logs kisanvoice

# Restart services
docker-compose restart

# Rebuild containers
docker-compose up -d --build
```

#### 2. API Key Issues
- Verify all API keys are correctly set in `.env`
- Check API key permissions and quotas
- Ensure services are accessible from your network

#### 3. Port Conflicts
- Check if port 8000 is already in use
- Change port in `.env` and `docker-compose.yml`
- Update Nginx configuration if needed

#### 4. Memory Issues
- Increase Docker memory limits
- Check system resources
- Optimize model usage

### Logs and Debugging
```bash
# View application logs
docker-compose logs -f kisanvoice

# View Nginx logs
docker-compose logs -f nginx

# View Redis logs
docker-compose logs -f redis
```

## 📚 Additional Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Chainlit Documentation](https://docs.chainlit.io/)
- [Groq API Documentation](https://console.groq.com/docs)
- [ElevenLabs API Documentation](https://elevenlabs.io/docs)
- [OpenWeather API Documentation](https://openweathermap.org/api)
- [WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp)

## 🤝 Support

If you encounter issues:
1. Check the logs for error messages
2. Verify all API keys and configurations
3. Test individual services separately
4. Check the troubleshooting section above
5. Open an issue in the repository

---

**Happy Farming with KisanVoice! 🌾🤖**

