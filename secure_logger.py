"""
Secure logging configuration that masks sensitive data
"""
import re
from loguru import logger

class SensitiveDataFilter:
    """Filter to mask sensitive data in logs"""
    
    # Patterns to mask
    SENSITIVE_PATTERNS = [
        # API Keys
        (r'(xai-)[A-Za-z0-9]{20,}', r'\1***MASKED***'),
        (r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}):[0-9a-f]{32}', r'***FAL_KEY_MASKED***'),
        
        # OAuth tokens
        (r'(ya29\.)[A-Za-z0-9_-]+', r'\1***MASKED***'),
        (r'(1//)[0-9A-Za-z_-]+', r'\1***MASKED***'),
        
        # Google credentials
        (r'"private_key":\s*"[^"]*"', r'"private_key": "***MASKED***"'),
        (r'"private_key_id":\s*"[^"]*"', r'"private_key_id": "***MASKED***"'),
        (r'"client_secret":\s*"[^"]*"', r'"client_secret": "***MASKED***"'),
        
        # Generic patterns
        (r'(api[_-]?key\s*[:=]\s*)["\']?[^"\'\s]+["\']?', r'\1"***MASKED***"'),
        (r'(password\s*[:=]\s*)["\']?[^"\'\s]+["\']?', r'\1"***MASKED***"'),
        (r'(secret\s*[:=]\s*)["\']?[^"\'\s]+["\']?', r'\1"***MASKED***"'),
        (r'(token\s*[:=]\s*)["\']?[^"\'\s]+["\']?', r'\1"***MASKED***"'),
        
        # Bearer tokens in headers
        (r'(Bearer\s+)[A-Za-z0-9_-]+', r'\1***MASKED***'),
        
        # Environment variables that might contain secrets
        (r'(GROK_API_KEY=)[^\s]+', r'\1***MASKED***'),
        (r'(FAL_KEY=)[^\s]+', r'\1***MASKED***'),
        (r'(FAL_API_KEY=)[^\s]+', r'\1***MASKED***'),
    ]
    
    def __call__(self, record):
        """Filter log record to mask sensitive data"""
        # Get the log message
        message = record["message"]
        
        # Apply all masking patterns
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
        
        # Update the record with masked message
        record["message"] = message
        return record

def setup_secure_logger():
    """Configure logger with security filters"""
    # Remove default handler
    logger.remove()
    
    # Add console handler with filter
    logger.add(
        lambda msg: print(msg),
        filter=SensitiveDataFilter(),
        level="DEBUG"
    )
    
    # Add file handler with filter and rotation
    logger.add(
        "logs/video_automation_{time:YYYY-MM-DD}.log",
        filter=SensitiveDataFilter(),
        rotation="1 day",
        retention="7 days",
        level="INFO",
        encoding="utf-8"
    )
    
    return logger

# Example usage in other files:
# from secure_logger import setup_secure_logger
# logger = setup_secure_logger()