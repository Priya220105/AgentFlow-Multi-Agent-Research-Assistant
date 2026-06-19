# utils/rate_limit.py

import time

def gemini_safe_call(fn, *args, **kwargs):
    """
    Wraps a Gemini API call with a small delay to stay under the
    free tier's per-minute rate limit (5 requests/minute on some models).
    """
    result = fn(*args, **kwargs)
    time.sleep(5)  
    return result