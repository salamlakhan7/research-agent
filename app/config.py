import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
GUEST_FREE_USES = 1

# Models (we can change these later)
GROQ_MODEL = "openai/gpt-oss-120b"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LOCAL_SUMMARIZER_MODEL = "sshleifer/distilbart-cnn-12-6"

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
USER_DAILY_LIMIT = 5

# Search and summary settings
MAX_SEARCH_RESULTS = 5
DEDUP_THRESHOLD = 0.88


def check_keys():
    missing = [name for name, val in
               [("GROQ_API_KEY", GROQ_API_KEY), ("TAVILY_API_KEY", TAVILY_API_KEY)]
               if not val]
    if missing:
        raise RuntimeError(f"Missing keys in .env: {', '.join(missing)}")