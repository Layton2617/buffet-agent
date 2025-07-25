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

---

## Project Improvements and Refactoring Summary on July 24th

This section documents the major improvements, refactoring, and bug fixes made to the project, with a focus on clarity, robustness, and maintainability. Each file/module is described in detail, highlighting the changes compared to the initial version.

---

### 1. `src/buffett_agent.py`
- **Refactored agent orchestration:**  
  The `BuffettAgent` class now acts as the central orchestrator, coordinating between the RAG system, financial tools, and the belief system.
- **Ticker extraction with LLM:**  
  Integrated `LangChainTools.parse_tickers_with_langchain` for robust ticker extraction from user queries, ensuring only valid tickers are processed.
- **Dynamic news-driven belief updates:**  
  Added logic to fetch and process news for extracted tickers, updating the belief system automatically, evaluated by LLMs, and generated the key, summary, and confidence.
- **Cleaner data flow:**  
  Ensured that all financial tool inputs are dynamically fetched and validated, reducing reliance on hardcoded or sample data.

---

### 2. `src/belief_system.py`
- **Belief system modularization:**  
  The `BeliefTracker` class now manages beliefs, confidence levels, and causal relationships in a more modular way.
- **LLM integration for belief updates:**  
  Refactored to use a pluggable LLM interface (`LangChainOpenAI`), allowing for flexible and up-to-date language model usage.
- **Batch news processing:**  
  Improved the `update_beliefs_from_news` method to handle batch news updates, with robust parsing and error handling.

---

### 3. `src/financial_tools.py`
- **Simplified DCF calculation:**  
  Replaced the original multi-period DCF with a Gordon Growth Model (`simple_gordon_dcf`), using only one forward FCF and the formula FCF1/(r-g).
- **Per-share intrinsic value:**  
  Updated margin of safety calculations to use per-share intrinsic value (DCF divided by shares outstanding).

---

### 4. `src/resources/fin_data.py`
- **Robust financial data acquisition:**  
  The `MultiDataAgent` class now fetches data from multiple sources (yfinance, finnhub, simfin, Alpha Vantage) with improved error handling.
- **PE analysis improvements:**  
  Added methods to fetch historical PE ranges, industry average PE, and aggregate all necessary data for PE analysis.
- **Margin of safety automation:**  
  Automated the process of fetching current price, FCF, and shares outstanding for margin of safety calculations.

---

### 5. `src/parse_tools.py`
- **Centralized LLM parsing utilities:**  
  Created a new module to house all LLM-based parsing functions, such as ticker extraction and news-to-belief conversion.
- **Modern LangChain usage:**  
  Updated to use `llm.invoke()` instead of deprecated call patterns, ensuring compatibility with the latest LangChain versions.
- **Robust output parsing:**  
  Implemented fallback logic for JSON extraction and normalization, improving reliability when parsing LLM outputs.

---

### 6. `src/resources/data_template.py`
- **Class-based data templates:**  
  Refactored from static methods to an instantiable `DataTemplate` class, supporting dynamic data population and validation.
- **API alignment:**  
  Ensured that all data structures align with API requirements for seamless integration.

---

### 7. `src/main.py`
- **Flask app configuration:**  
  Enhanced development experience by enabling debug mode for real-time error tracking and hot reloading

---

### 8. General Improvements
- **Modernized LangChain usage:**  
  Removed deprecated patterns and ensured all LangChain calls are up-to-date.
- **Ticker validation:**  
  Added a utility to validate tickers using yfinance, filtering out invalid or non-tradable symbols.
- **Prompt engineering:**  
  Improved prompts for LLM-based extraction tasks, clarifying output formats and increasing reliability.
- **Error handling:**  
  Enhanced error handling and logging throughout the codebase, especially for external API calls and LLM integration.
- **Documentation:**  
  Added or improved code comments (in both English and Chinese) for better maintainability and onboarding.

---

## How to Use This Section

- Use this summary to quickly understand the evolution of the codebase and the rationale behind major changes.
- Refer to the detailed comments in each file for implementation specifics and usage examples.
- For further questions or contributions, see the [Contributing Guidelines](#) and [API Documentation](#).

