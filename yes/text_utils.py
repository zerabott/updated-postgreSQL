"""
Text utility functions for the Telegram bot
"""
import re


def escape_markdown_text(text):
    """
    Escape special characters for Telegram MarkdownV2 parsing
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text safe for MarkdownV2
    """
    if not text:
        return ""
    
    # MarkdownV2 special characters that need escaping
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    escaped_text = str(text)
    for char in special_chars:
        escaped_text = escaped_text.replace(char, f'\\{char}')
    
    return escaped_text


def truncate_text(text, max_length=100):
    """
    Truncate text to specified length with ellipsis
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."


def sanitize_content(content):
    """
    Sanitize user input content
    
    Args:
        content: Raw content from user
        
    Returns:
        Sanitized content
    """
    if not content:
        return ""
    
    # Remove extra whitespace
    content = re.sub(r'\s+', ' ', content.strip())
    
    # Basic length check
    if len(content) < 5:
        return ""
    
    return content


def format_time_ago(dt):
    """
    Format datetime to human-readable "time ago" format
    
    Args:
        dt: datetime object
        
    Returns:
        Human-readable time string
    """
    from datetime import datetime, timezone
    import math
    
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
        
    diff = now - dt
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes}m ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours}h ago"
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f"{days}d ago"
    else:
        weeks = int(seconds // 604800)
        return f"{weeks}w ago"
