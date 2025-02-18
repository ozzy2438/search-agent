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
Create a `.env` file in the root directory with:
```
TAVILY_API_KEY=your_api_key_here
```

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

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 