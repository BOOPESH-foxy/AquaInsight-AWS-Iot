import os
from dotenv import load_dotenv
from aws_ssm.ssm_config import get_parameter

# Load .env for local development
load_dotenv()

def get_config(key, ssm_path=None, default=None):
    """ Get configuration value with SSM fallback to environment variables """
    
    # Try SSM parameter first (production)
    if ssm_path:
        try:
            value = get_parameter(ssm_path)
            if value is not None:
                return value
        except Exception:
            pass  # Fall back to .env
    
    # Fall back to environment variable (local development)
    return os.getenv(key, default)


