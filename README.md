# AI Search Agent

An AI-powered search agent that processes research tasks using the Tavily API. This application allows users to submit research queries, categorize them by importance and topic, and receive detailed analysis with credible sources.

## Features

- Task queue management with priority handling
- Category-specific insights and analysis
- Source credibility scoring
- Caching mechanism for efficient processing
- Real-time status updates
- Dark/Light theme support
- Responsive UI

## Tech Stack

- Backend: Python with Flask
- Frontend: HTML, CSS, JavaScript
- API: Tavily API for research
- Additional: CORS, async/await support

## Setup

1. Clone the repository:
```bash
git clone https://github.com/ozzy2438/search-agent.git
cd search-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.example` to create your own `.env` file:
   ```bash
   cp .env.example .env
   ```
   - Edit `.env` and replace the placeholder values with your actual API keys:
   ```
   TAVILY_API_KEY=your_actual_tavily_api_key_here
   ```
   
   ⚠️ **Security Note**: 
   - Never commit your `.env` file to version control
   - Keep your API keys private and secure
   - The `.env` file is already in `.gitignore` to prevent accidental commits

4. Run the application:
```bash
python src/run.py
```

The application will be available at `http://localhost:5002`

## Usage

1. Enter your research query in the text area
2. Select a category (General, Science, Technology, Business, Health)
3. Set importance level (1-5)
4. Click "Add Task" to queue your research request
5. Use "Process Tasks" to start processing the queue
6. View results in real-time with detailed analysis

## Security Best Practices

1. API Key Protection:
   - Store API keys in `.env` file
   - Never commit `.env` file to version control
   - Use environment variables in production
   
2. Rate Limiting:
   - Configure rate limits in `.env`
   - Monitor API usage
   
3. Error Handling:
   - Sensitive error details are logged but not exposed to users
   - All API responses are sanitized

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 