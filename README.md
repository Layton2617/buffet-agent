# Digital Buffett - AI Financial Advisor

A sophisticated AI financial advisor system that mimics Warren Buffett's investment philosophy and decision-making process. Built with Flask backend and React frontend, featuring RAG (Retrieval-Augmented Generation), financial analysis tools, and belief tracking.

## Features

### Core Capabilities
- **Chat Interface**: Interactive conversation with AI Warren Buffett
- **Financial Tools**: DCF calculator, P/E analyzer, margin of safety calculator, Buffett score
- **RAG System**: Retrieval from Buffett's shareholder letters (1977-2021)
- **Belief Tracking**: Temporal belief system for market context
- **Chain-of-Thought**: Step-by-step reasoning display
- **Portfolio Analysis**: Multi-stock evaluation using Buffett methodology

### Technical Architecture
- **Backend**: Flask with SQLAlchemy, OpenAI GPT-4 integration
- **Frontend**: React with Tailwind CSS and shadcn/ui components
- **Database**: SQLite for conversations, beliefs, and recommendations
- **AI Integration**: OpenAI API with custom prompting and tool calling
- **Deployment**: Render-ready with Docker support

## Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key
- Node.js 18+ (for development)

### Environment Setup
1. Clone the repository
2. Set environment variable:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

### Local Development
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the Flask application:
   ```bash
   python src/main.py
   ```

3. Access the application at `http://localhost:5000`

## Deployment on Render

### Method 1: Direct GitHub Deployment
1. Fork this repository to your GitHub account
2. Connect your GitHub account to Render
3. Create a new Web Service on Render
4. Select this repository
5. Configure environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `FLASK_ENV`: production
6. Deploy

### Method 2: Manual Upload
1. Download the ZIP file
2. Upload to Render as a new Web Service
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python src/main.py`
5. Configure environment variables as above

## Project Structure

```
buffett-agent/
├── src/
│   ├── models/
│   │   └── conversation.py      # Database models
│   ├── routes/
│   │   └── buffett_routes.py    # API endpoints
│   ├── static/                  # Built React frontend
│   ├── database/
│   │   └── app.db              # SQLite database
│   ├── buffett_agent.py        # Main AI agent
│   ├── financial_tools.py      # Financial calculations
│   ├── rag_system.py          # Retrieval system
│   ├── belief_system.py       # Belief tracking
│   └── main.py                 # Flask application
├── requirements.txt            # Python dependencies
├── render.yaml                # Render configuration
└── README.md                  # This file
```

## API Endpoints

### Chat & Analysis
- `POST /api/chat` - Send message to Buffett agent
- `GET /api/conversation/{session_id}` - Get conversation history

### Financial Tools
- `POST /api/tools/dcf` - Calculate DCF valuation
- `POST /api/tools/pe` - Analyze P/E ratios
- `POST /api/tools/margin` - Calculate margin of safety
- `POST /api/tools/buffett-score` - Calculate Buffett score

### Belief System
- `GET /api/beliefs` - Get current beliefs
- `POST /api/beliefs/update` - Update beliefs from news

### Portfolio
- `POST /api/portfolio/analyze` - Analyze portfolio

## Usage Examples

### Chat Interface
Ask questions like:
- "Should I invest in Apple at current prices?"
- "How do you calculate intrinsic value?"
- "What's your view on the current market?"

### Financial Tools
Use the tools tab to:
- Calculate DCF for specific cash flows
- Analyze P/E ratios vs industry averages
- Determine margin of safety for investments
- Get overall Buffett score for companies

### Belief Tracking
Monitor how market beliefs influence decisions:
- Fed policy changes
- Inflation trends
- Market sentiment shifts

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for AI functionality
- `FLASK_ENV`: Set to 'production' for deployment
- `PORT`: Port number (default: 5000)

### Customization
- Modify `src/rag_system.py` to add more Buffett content
- Update `src/financial_tools.py` for additional calculations
- Extend `src/belief_system.py` for more market factors

## Technical Details

### AI System
- Uses OpenAI GPT-4 with custom system prompts
- Implements Chain-of-Thought reasoning
- RAG system with semantic search
- Tool calling for financial calculations

### Database Schema
- Conversations: User messages and agent responses
- Beliefs: Temporal belief states with confidence scores
- Portfolio: Investment recommendations and analysis

### Security
- Input validation and sanitization
- Rate limiting considerations
- API key protection
- CORS configuration for frontend

## Troubleshooting

### Common Issues
1. **OpenAI API Key**: Ensure valid API key is set
2. **Database**: SQLite file permissions
3. **CORS**: Frontend-backend communication
4. **Dependencies**: Check Python version compatibility

### Logs
Check application logs for detailed error information:
```bash
python src/main.py
```

