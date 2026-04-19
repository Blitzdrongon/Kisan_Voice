# ರೈತಮಿತ್ರ (KisanVoice) 🌾

An AI-powered agricultural assistant chatbot designed to help farmers with crop management, weather information, and agricultural advice. Built with Chainlit for a modern chat interface.

## Features ✨

### 🌾 Agricultural Assistance
- Crop recommendations and cultivation techniques
- Pest and disease management
- Soil health and fertilizer advice
- Irrigation and water management

### 🌤️ Weather Information
- Current weather conditions
- Rainfall predictions
- Temperature and humidity data
- Weather-based farming recommendations

### 📸 Image Analysis
- Crop image analysis
- Pest and disease identification
- Soil condition assessment
- Plant health monitoring

### 🗣️ Voice Interaction
- Voice-based queries
- Audio responses
- Natural conversation flow

### 💾 Conversation Memory
- Remembers previous conversations
- Personalized agricultural advice
- Progress tracking and results

## Languages 🌍
- **Kannada** (Primary language)
- **English** (Secondary language)

## Technology Stack 🛠️

- **UI Framework**: Chainlit
- **AI Models**: Groq (LLaMA models)
- **Text-to-Speech**: ElevenLabs
- **Weather API**: OpenWeather
- **Memory**: SQLite + Qdrant
- **Language**: Python 3.13+

## Prerequisites 📋

- Python 3.13 or higher
- Required API keys:
  - Groq API key
  - ElevenLabs API key
  - OpenWeather API key

## Installation 🚀

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd KisanVoice
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` file with your API keys:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   OPENWEATHER_API_KEY=your_openweather_api_key_here
   ```

4. **Run the application**
   ```bash
   chainlit run app/main.py
   ```

5. **Access the application**
   Open your browser and go to `http://localhost:8000`

## Usage 📖

1. **Ask Questions**: Type your agricultural questions in Kannada or English
2. **Upload Images**: Share crop, pest, or disease photos for analysis
3. **Voice Interaction**: Use voice input for questions and receive audio responses
4. **Memory Features**: Ask about previous conversations and get personalized advice

## Example Questions 💭

- "ಈಗ ಬೆಳೆಯಲು ಯಾವ ಬೆಳೆ ಒಳ್ಳೆಯದು?" (What crop is good to grow now?)
- "ನನ್ನ ಬೆಳೆಗೆ ಯಾವ ರಾಸಾಯನಿಕಗಳು ಬೇಕು?" (What chemicals does my crop need?)
- "ಮಳೆ ಬರುವ ಸಾಧ್ಯತೆ ಇದೆಯೇ?" (Is there a chance of rain?)
- "ಈ ಚಿತ್ರದಲ್ಲಿ ಯಾವ ಕೀಟ ಇದೆ?" (What insect is in this picture?)
- "ನನ್ನ ಹಿಂದಿನ ಸಂವಾದಗಳನ್ನು ನೆನಪಿಸಿಕೊಳ್ಳಿ" (Remember my previous conversations)

## Project Structure 📁

```
KisanVoice/
├── app/
│   ├── core/           # Core configuration and state management
│   ├── nodes/          # Conversation workflow nodes
│   ├── services/       # External service integrations
│   └── main.py         # Main Chainlit application
├── .chainlit/          # Chainlit configuration
├── chainlit.md         # Welcome page content
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
└── README.md          # This file
```

## Configuration ⚙️

The application can be configured through:

- **Environment Variables**: Set in `.env` file
- **Chainlit Config**: Modify `.chainlit/config.toml`
- **Welcome Page**: Edit `chainlit.md`

## Development 🛠️

### Running in Development Mode
```bash
chainlit run app/main.py --dev
```

### Logs
Logs are stored in the `logs/` directory.

### Database
The application uses SQLite for conversation storage. The database file is created automatically at `kisanvoice.db`.

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Support 💬

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the example questions

---

**ರೈತಮಿತ್ರ** - Your Trusted Agricultural Assistant! 🌱
