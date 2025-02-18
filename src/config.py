import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "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")
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RATE_LIMIT_CALLS = int(os.getenv("RATE_LIMIT_CALLS", "5"))
    RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    PORT = int(os.getenv("PORT", "5002"))
