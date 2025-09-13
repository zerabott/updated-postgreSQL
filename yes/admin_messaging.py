import logging
from config import ADMIN_IDS
from db_connection import get_db_connection
from text_utils import escape_markdown_text

logger = logging.getLogger(__name__)

def ensure_admin_reply_tracking_migration():
    """Ensure admin_messages table has proper reply tracking"""
    try:
        db_conn = get_db_connection()
        with db_conn.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if admin_messages table exists and has the required columns
            if db_conn.use_postgresql:
                # PostgreSQL: Check if table exists and columns are present
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'admin_messages' AND table_schema = 'public'
                """)
                existing_columns = [row[0] for row in cursor.fetchall()]
                
                # Add replied_by_admin_id column if it doesn't exist
                if 'replied_by_admin_id' not in existing_columns:
                    cursor.execute("""
                        ALTER TABLE admin_messages 
                        ADD COLUMN replied_by_admin_id BIGINT
                    """)
                    logger.info("Added replied_by_admin_id column to admin_messages table (PostgreSQL)")
                    
                # Add reply_timestamp column if it doesn't exist
                if 'reply_timestamp' not in existing_columns:
                    cursor.execute("""
                        ALTER TABLE admin_messages 
                        ADD COLUMN reply_timestamp TIMESTAMP
                    """)
                    logger.info("Added reply_timestamp column to admin_messages table (PostgreSQL)")
            else:
                # SQLite: Use PRAGMA to check columns
                cursor.execute("PRAGMA table_info(admin_messages)")
                existing_columns = [row[1] for row in cursor.fetchall()]
                
                # Add replied_by_admin_id column if it doesn't exist
                if 'replied_by_admin_id' not in existing_columns:
                    cursor.execute("""
                        ALTER TABLE admin_messages 
                        ADD COLUMN replied_by_admin_id INTEGER
                    """)
                    logger.info("Added replied_by_admin_id column to admin_messages table (SQLite)")
                    
                # Add reply_timestamp column if it doesn't exist
                if 'reply_timestamp' not in existing_columns:
                    cursor.execute("""
                        ALTER TABLE admin_messages 
                        ADD COLUMN reply_timestamp TEXT
                    """)
                    logger.info("Added reply_timestamp column to admin_messages table (SQLite)")
            
            conn.commit()
            logger.info("Admin reply tracking migration completed successfully")
            
    except Exception as e:
        logger.error(f"Error in admin reply tracking migration: {e}")
        # Don't raise exception to avoid breaking the bot if migration fails
        pass

def save_user_message(user_id, message):
    """Save user message to admin"""
    try:
        db_conn = get_db_connection()
        with db_conn.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = db_conn.get_placeholder()
            cursor.execute(
                f"INSERT INTO admin_messages (user_id, user_message) VALUES ({placeholder}, {placeholder})",
                (user_id, message)
            )
            
            # Get the inserted message ID
            if db_conn.use_postgresql:
                cursor.execute("SELECT lastval()")
                message_id = cursor.fetchone()[0]
            else:
                message_id = cursor.lastrowid
                
            conn.commit()
            return message_id, None
    except Exception as e:
        return None, f"Database error: {str(e)}"

def check_message_reply_status(message_id):
    """Check if message has already been replied to and by whom"""
    try:
        db_conn = get_db_connection()
        with db_conn.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = db_conn.get_placeholder()
            cursor.execute(
                f"SELECT replied, admin_id, replied_by_admin_id, reply_timestamp FROM admin_messages WHERE message_id = {placeholder}",
                (message_id,)
            )
            result = cursor.fetchone()
            
            if result:
                replied, admin_id, replied_by_admin_id, reply_timestamp = result
                return {
                    'has_reply': bool(replied),
                    'replied_by_admin': replied_by_admin_id or admin_id,  # Use new column if available
                    'reply_timestamp': reply_timestamp
                }
            return None
    except Exception as e:
        logger.error(f"Error checking message reply status: {e}")
        return None

def save_admin_reply(message_id, admin_id, reply):
    """Save admin reply to user message with duplicate prevention"""
    try:
        # First, check if message has already been replied to
        reply_status = check_message_reply_status(message_id)
        if reply_status and reply_status['has_reply']:
            return False  # Already replied to
        
        db_conn = get_db_connection()
        with db_conn.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = db_conn.get_placeholder()
            
            # Use current timestamp for reply
            import datetime
            current_timestamp = datetime.datetime.now()
            
            if db_conn.use_postgresql:
                # PostgreSQL version with proper timestamp handling
                cursor.execute(
                    f"UPDATE admin_messages SET admin_reply = {placeholder}, admin_id = {placeholder}, replied = 1, replied_by_admin_id = {placeholder}, reply_timestamp = {placeholder} WHERE message_id = {placeholder} AND replied = 0",
                    (reply, admin_id, admin_id, current_timestamp, message_id)
                )
            else:
                # SQLite version with text timestamp
                cursor.execute(
                    f"UPDATE admin_messages SET admin_reply = {placeholder}, admin_id = {placeholder}, replied = 1, replied_by_admin_id = {placeholder}, reply_timestamp = {placeholder} WHERE message_id = {placeholder} AND replied = 0",
                    (reply, admin_id, admin_id, current_timestamp.strftime('%Y-%m-%d %H:%M:%S'), message_id)
                )
            
            # Check if any rows were updated (means reply was successful)
            rows_updated = cursor.rowcount
            conn.commit()
            
            return rows_updated > 0
            
    except Exception as e:
        logger.error(f"Error saving admin reply: {e}")
        return False

def get_pending_messages():
    """Get all pending user messages for admins"""
    db_conn = get_db_connection()
    with db_conn.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT message_id, user_id, user_message, timestamp
            FROM admin_messages 
            WHERE replied = 0 
            ORDER BY timestamp ASC
        ''')
        return cursor.fetchall()

def get_message_by_id(message_id):
    """Get specific message by ID"""
    db_conn = get_db_connection()
    with db_conn.get_connection() as conn:
        cursor = conn.cursor()
        placeholder = db_conn.get_placeholder()
        cursor.execute(
            f"SELECT * FROM admin_messages WHERE message_id = {placeholder}",
            (message_id,)
        )
        return cursor.fetchone()

async def send_message_to_admins(context, user_id, message):
    """Send user message to all admins with inline reply buttons"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    logger.info(f"Attempting to send message from user {user_id} to admins")
    
    message_id, error = save_user_message(user_id, message)
    
    if error:
        logger.error(f"Error saving message: {error}")
        return False, error
    
    logger.info(f"Message saved with ID: {message_id}")
    
    import datetime
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    admin_text = f"""
📨 *New User Message*

*Message ID:* \\#{message_id}
*From User:* {user_id}
*Timestamp:* {escape_markdown_text(current_time)}

*Message:*
{escape_markdown_text(message)}

*Reply Options:*
• Use the buttons below for quick reply
• Or use: `/reply {message_id} <your_response>`
"""
    
    # Create inline keyboard for admin actions
    keyboard = [
        [
            InlineKeyboardButton("💬 Quick Reply", callback_data=f"admin_reply_{message_id}"),
            InlineKeyboardButton("📋 View History", callback_data=f"admin_history_{user_id}")
        ],
        [
            InlineKeyboardButton("✅ Mark as Read", callback_data=f"admin_read_{message_id}"),
            InlineKeyboardButton("🔇 Ignore User", callback_data=f"admin_ignore_{user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    success_count = 0
    
    # Ensure there are admins in the list
    if not ADMIN_IDS:
        logger.warning("No admins configured!")
        return False, "No admins configured"
    
    logger.info(f"Sending to {len(ADMIN_IDS)} admin(s)")
    
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                reply_markup=reply_markup,
                parse_mode="MarkdownV2"
            )
            success_count += 1
            logger.info(f"Successfully sent to admin {admin_id}")
        except Exception as e:
            logger.error(f"Failed to send to admin {admin_id}: {e}")
    
    logger.info(f"Total successful sends: {success_count}")
    return success_count > 0, f"Sent to {success_count} admins"

async def send_admin_reply_to_user(context, message_id, admin_id, reply):
    """Send admin reply to user anonymously with duplicate prevention"""
    message_data = get_message_by_id(message_id)
    
    if not message_data:
        return False, "Message not found"
    
    # Check if message has already been replied to
    reply_status = check_message_reply_status(message_id)
    if reply_status and reply_status['has_reply']:
        # Message already has a reply - notify about duplicate attempt
        replied_by_admin = reply_status['replied_by_admin']
        if replied_by_admin == admin_id:
            return False, "You have already replied to this message"
        else:
            return False, f"This message has already been replied to by another admin (ID: {replied_by_admin})"
    
    user_id = message_data[1]  # user_id is at index 1
    
    # Save the reply with duplicate prevention
    reply_saved = save_admin_reply(message_id, admin_id, reply)
    if not reply_saved:
        # Double-check the reason for failure
        reply_status = check_message_reply_status(message_id)
        if reply_status and reply_status['has_reply']:
            replied_by_admin = reply_status['replied_by_admin']
            return False, f"Another admin (ID: {replied_by_admin}) replied to this message while you were typing"
        else:
            return False, "Failed to save reply due to database error"
    
    # Send to user
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"""
📧 *Admin Reply*

{escape_markdown_text(reply)}

This is an anonymous reply from the administration team\\.
If you need to respond, use "📞 Contact Admin" again\\.
""",
            parse_mode="MarkdownV2"
        )
        
        # Notify other admins that this message has been replied to
        await notify_other_admins_of_reply(context, message_id, admin_id, user_id)
        
        return True, "Reply sent successfully"
    except Exception as e:
        return False, f"Failed to send reply: {str(e)}"

async def notify_other_admins_of_reply(context, message_id, replying_admin_id, user_id):
    """Notify other admins that a message has been replied to"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    notification_text = f"""
✅ *Message \\#{message_id} has been replied to*

*From User:* {user_id}
*Replied by:* Admin {replying_admin_id}
*Status:* Resolved

This message is now marked as handled\\.
"""
    
    # Create keyboard with history option
    keyboard = [
        [
            InlineKeyboardButton("📋 View History", callback_data=f"admin_history_{user_id}"),
            InlineKeyboardButton("💬 Message Management", callback_data="admin_messages")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send to all other admins
    for admin_id in ADMIN_IDS:
        if admin_id != replying_admin_id:  # Don't notify the admin who replied
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=notification_text,
                    reply_markup=reply_markup,
                    parse_mode="MarkdownV2"
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id} about reply: {e}")

def mark_message_as_read(message_id):
    """Mark a message as read/handled"""
    try:
        db_conn = get_db_connection()
        with db_conn.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = db_conn.get_placeholder()
            cursor.execute(
                f"UPDATE admin_messages SET replied = 1 WHERE message_id = {placeholder}",
                (message_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error marking message as read: {e}")
        return False

def ignore_user_messages(user_id):
    """Mark all messages from a user as ignored/handled"""
    try:
        db_conn = get_db_connection()
        with db_conn.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = db_conn.get_placeholder()
            cursor.execute(
                f"UPDATE admin_messages SET replied = 1 WHERE user_id = {placeholder} AND replied = 0",
                (user_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error ignoring user messages: {e}")
        return False

def get_user_message_history(user_id, limit=10):
    """Get user's message history with admins - fixed version"""
    db_conn = get_db_connection()
    with db_conn.get_connection() as conn:
        cursor = conn.cursor()
        placeholder = db_conn.get_placeholder()
        cursor.execute(f'''
            SELECT message_id, user_message, timestamp, replied, admin_reply
            FROM admin_messages 
            WHERE user_id = {placeholder} 
            ORDER BY timestamp DESC 
            LIMIT {placeholder}
        ''', (user_id, limit))
        return cursor.fetchall()

# Run migration when module is imported
try:
    ensure_admin_reply_tracking_migration()
except Exception as e:
    logger.error(f"Failed to run admin_messaging migration on import: {e}")
