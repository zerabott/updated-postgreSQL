import re

# Utility function to check if a string contains only emoji
def is_valid_emoji(s):
    # Accept all actual emoji, reject known corrupted characters like '遅'
    # This regex covers most emoji blocks, but you may expand if needed
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    if not s:
        return False
    # Check each character, must all be emoji or valid emoji sequence
    return all(emoji_pattern.match(char) for char in s)

def get_user_rank_for_comment(user_id):
    """Get user's rank information for displaying under comments"""
    try:
        from ranking_integration import ranking_manager
        user_rank = ranking_manager.get_user_rank(user_id)
        default_emoji = '🥉'
        if user_rank:
            rank_emoji = user_rank.rank_emoji if is_valid_emoji(user_rank.rank_emoji) else default_emoji
            return {
                'rank_name': user_rank.rank_name,
                'rank_emoji': rank_emoji,
                'total_points': user_rank.total_points,
                'is_special_rank': user_rank.is_special_rank
            }
        else:
            # Default rank for new users
            return {
                'rank_name': 'Freshman',
                'rank_emoji': default_emoji,
                'total_points': 0,
                'is_special_rank': False
            }
    except Exception as e:
        logger.error(f"Error getting user rank for {user_id}: {e}")
        # Return default rank on error
        return {
            'rank_name': 'Freshman',
            'rank_emoji': '🥉',
            'total_points': 0,
            'is_special_rank': False
        }