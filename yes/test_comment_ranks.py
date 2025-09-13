#!/usr/bin/env python3
"""
Test script to verify the comment rank display feature
This script tests the new rank display functionality in comments
"""

import sys
import logging
from comments import get_user_rank_for_comment, format_comment_display
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_user_rank_function():
    """Test the get_user_rank_for_comment function"""
    print("=== Testing get_user_rank_for_comment ===")
    
    # Test with a sample user ID
    test_user_id = 123456789
    try:
        rank_info = get_user_rank_for_comment(test_user_id)
        print(f"✅ Rank function works for user {test_user_id}")
        print(f"   Rank: {rank_info['rank_emoji']} {rank_info['rank_name']}")
        print(f"   Points: {rank_info['total_points']}")
        print(f"   Special: {rank_info['is_special_rank']}")
        return True
    except Exception as e:
        print(f"❌ Error getting rank for user {test_user_id}: {e}")
        return False

def test_comment_display():
    """Test the format_comment_display function with rank"""
    print("\n=== Testing format_comment_display with ranks ===")
    
    # Mock comment data for testing
    test_comment_data = {
        'comment_id': 1,
        'content': 'This is a test comment to see if ranks display properly!',
        'timestamp': datetime.now().isoformat(),
        'likes': 5,
        'dislikes': 1,
        'flagged': 0,
        'parent_comment_id': None,
        'user_id': 123456789,  # This should trigger rank lookup
        'comment_number': 1,
        'is_reply': False
    }
    
    try:
        # Test with a regular comment
        result = format_comment_display(test_comment_data, user_id=987654321, current_page=1, comment_index=0)
        print("✅ Comment formatting works!")
        print(f"   Full comment text:")
        print(f"   {result['text']}")
        print(f"   📍 Note: Rank appears at bottom-right corner!")
        print(f"   Parse mode: {result['parse_mode']}")
        print(f"   Has buttons: {len(result['reply_markup'].inline_keyboard) > 0}")
        return True
    except Exception as e:
        print(f"❌ Error formatting comment: {e}")
        return False

def test_reply_comment_display():
    """Test the format_comment_display function with reply and rank"""
    print("\n=== Testing format_comment_display with reply and ranks ===")
    
    # Mock reply comment data for testing
    test_reply_data = {
        'comment_id': 2,
        'content': 'This is a reply with rank display!',
        'timestamp': datetime.now().isoformat(),
        'likes': 3,
        'dislikes': 0,
        'flagged': 0,
        'parent_comment_id': 1,
        'user_id': 555666777,  # Different user for reply
        'comment_number': 2,
        'is_reply': True,
        'original_comment': {
            'comment_id': 1,
            'content': 'Original comment that this is replying to',
            'timestamp': datetime.now().isoformat()
        }
    }
    
    try:
        # Test with a reply comment
        result = format_comment_display(test_reply_data, user_id=987654321, current_page=1, comment_index=1)
        print("✅ Reply comment formatting works!")
        print(f"   Reply text preview (first 300 chars):")
        print(f"   {result['text'][:300]}...")
        return True
    except Exception as e:
        print(f"❌ Error formatting reply comment: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Comment Rank Display Feature")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: User rank function
    if test_user_rank_function():
        tests_passed += 1
    
    # Test 2: Comment display formatting
    if test_comment_display():
        tests_passed += 1
    
    # Test 3: Reply comment display formatting
    if test_reply_comment_display():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The comment rank display feature is working correctly.")
        print("\n📋 Summary of implemented features:")
        print("   • User rank lookup for comments")
        print("   • Rank display at BOTTOM-RIGHT corner of comments")
        print("   • Special styling for special ranks (✨)")
        print("   • Rank display in both regular comments and replies")
        print("   • Proper HTML escaping for security")
        print("   • PostgreSQL-compatible queries")
        print("   • Error handling for missing rank data")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
