#!/usr/bin/env python3
"""
Get last message from Telegram channel using Telethon
Works for any public channel without needing bot to join
"""

import os
import sys
import json
from datetime import datetime
from telethon import TelegramClient
from telethon.errors import (
    ChannelPrivateError, 
    ChannelInvalidError,
    UsernameNotOccupiedError
)
from telethon.tl.types import (
    MessageMediaPhoto,
    MessageMediaDocument,
    MessageMediaWebPage
)

def clean_channel_url(channel_url):
    """Extract clean channel username from URL"""
    if not channel_url:
        return None
    
    channel_url = channel_url.strip()
    
    # Remove @ if present
    if channel_url.startswith('@'):
        channel_url = channel_url[1:]
    
    # Extract from t.me URL
    if 't.me/' in channel_url:
        parts = channel_url.split('t.me/')
        if len(parts) > 1:
            channel_url = parts[1].split('/')[0]
    
    # Remove joinchat/ prefix
    if channel_url.startswith('joinchat/'):
        channel_url = channel_url.replace('joinchat/', '')
    
    return channel_url

def parse_message(message):
    """Parse Telegram message to structured format"""
    if not message:
        return None
    
    parsed = {
        'message_id': message.id,
        'date': message.date.isoformat() if message.date else None,
        'type': 'text'
    }
    
    # Text content
    if message.text:
        parsed['text'] = message.text
    elif message.caption:
        parsed['text'] = message.caption
        parsed['type'] = 'media_with_caption'
    
    # Media types
    if message.media:
        if isinstance(message.media, MessageMediaPhoto):
            parsed['media_type'] = 'photo'
            parsed['type'] = 'photo' if not message.text else 'photo_with_caption'
        elif isinstance(message.media, MessageMediaDocument):
            doc = message.media.document
            if doc:
                for attr in doc.attributes:
                    if hasattr(attr, 'file_name'):
                        parsed['file_name'] = attr.file_name
                    if hasattr(attr, 'duration'):
                        parsed['duration'] = attr.duration
                        
            # Determine document type
            mime_type = doc.mime_type if doc else ''
            if 'video' in mime_type:
                parsed['media_type'] = 'video'
                parsed['type'] = 'video' if not message.caption else 'video_with_caption'
            elif 'audio' in mime_type:
                parsed['media_type'] = 'audio'
                parsed['type'] = 'audio'
            elif 'image' in mime_type:
                parsed['media_type'] = 'image'
                parsed['type'] = 'image'
            else:
                parsed['media_type'] = 'document'
                parsed['type'] = 'document'
        elif isinstance(message.media, MessageMediaWebPage):
            parsed['media_type'] = 'webpage'
            if hasattr(message.media, 'webpage') and message.media.webpage:
                parsed['url'] = message.media.webpage.url
                parsed['title'] = message.media.webpage.title
                parsed['description'] = message.media.webpage.description
    
    # Views count
    if hasattr(message, 'views') and message.views:
        parsed['views'] = message.views
    
    # Forward info
    if message.forward:
        parsed['forwarded'] = True
        if hasattr(message.forward, 'from_id') and message.forward.from_id:
            parsed['forward_from'] = str(message.forward.from_id)
    
    # Reply info
    if message.reply_to:
        parsed['reply_to'] = {
            'message_id': message.reply_to.reply_to_msg_id
        }
    
    # Reactions
    if hasattr(message, 'reactions') and message.reactions:
        parsed['reactions'] = []
        for reaction in message.reactions.results:
            if hasattr(reaction, 'reaction'):
                parsed['reactions'].append({
                    'emoji': reaction.reaction.emoticon if hasattr(reaction.reaction, 'emoticon') else '👍',
                    'count': reaction.count
                })
    
    return parsed

async def get_channel_message(api_id, api_hash, phone_number, channel_url):
    """Get last message from channel using Telethon"""
    
    # Clean channel URL
    channel_username = clean_channel_url(channel_url)
    
    if not channel_username:
        return {
            'success': False,
            'error': 'Invalid channel URL'
        }
    
    # Create client
    client = TelegramClient('github_session', int(api_id), api_hash)
    
    try:
        # Start client with phone number
        await client.start(phone=phone_number)
        
        print(f"✅ Connected to Telegram as user")
        
        # Get channel entity
        try:
            entity = await client.get_entity(channel_username)
        except UsernameNotOccupiedError:
            return {
                'success': False,
                'error': f"Channel @{channel_username} does not exist"
            }
        except ChannelPrivateError:
            return {
                'success': False,
                'error': f"Channel @{channel_username} is private and you're not a member"
            }
        except ValueError as e:
            return {
                'success': False,
                'error': f"Cannot find channel: {channel_username}. Error: {str(e)}"
            }
        
        # Get channel info
        channel_info = {
            'id': str(entity.id),
            'title': entity.title,
            'username': entity.username or channel_username,
            'type': 'supergroup' if getattr(entity, 'megagroup', False) else 'channel',
            'participants_count': getattr(entity, 'participants_count', 0) if hasattr(entity, 'participants_count') else None
        }
        
        # Get last message
        messages = await client.get_messages(entity, limit=1)
        
        if not messages or not messages[0]:
            return {
                'success': True,
                'channel': channel_info,
                'message': None,
                'warning': 'Channel has no messages'
            }
        
        message = messages[0]
        
        # Parse message
        parsed_message = parse_message(message)
        
        return {
            'success': True,
            'channel': channel_info,
            'message': parsed_message,
            'total_messages': getattr(entity, 'broadcast', False) and 'N/A' or None
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }
    finally:
        await client.disconnect()
        # Clean up session file
        try:
            if os.path.exists('github_session.session'):
                os.remove('github_session.session')
        except:
            pass

def format_text_output(result):
    """Format result as readable text"""
    if not result.get('success'):
        return f"❌ Error: {result.get('error', 'Unknown error')}"
    
    lines = []
    
    # Channel info
    channel = result.get('channel', {})
    lines.append("=" * 50)
    lines.append(f"📢 Channel: {channel.get('title', 'Unknown')}")
    lines.append(f"   Username: @{channel.get('username', 'N/A')}")
    lines.append(f"   Type: {channel.get('type', 'unknown')}")
    lines.append("=" * 50)
    
    # Message
    message = result.get('message')
    if not message:
        lines.append("⚠️ No messages in channel")
        if result.get('warning'):
            lines.append(f"Note: {result['warning']}")
        return '\n'.join(lines)
    
    lines.append(f"🆔 Message ID: {message.get('message_id')}")
    lines.append(f"📅 Date: {message.get('date', 'Unknown')}")
    lines.append(f"📝 Type: {message.get('type', 'text')}")
    
    if message.get('views'):
        lines.append(f"👁️ Views: {message['views']}")
    
    lines.append("-" * 50)
    
    # Content
    if message.get('text'):
        lines.append(f"💬 Content:")
        lines.append(message['text'])
    
    # Media info
    if message.get('media_type'):
        lines.append(f"\n📎 Media: {message['media_type']}")
        if message.get('file_name'):
            lines.append(f"   File: {message['file_name']}")
        if message.get('duration'):
            lines.append(f"   Duration: {message['duration']}s")
    
    # URLs
    if message.get('url'):
        lines.append(f"\n🔗 URL: {message['url']}")
        if message.get('title'):
            lines.append(f"   Title: {message['title']}")
    
    # Forwarded
    if message.get('forwarded'):
        lines.append("\n↗️ Forwarded message")
    
    # Reply
    if message.get('reply_to'):
        lines.append(f"\n💬 Reply to message: {message['reply_to']['message_id']}")
    
    # Reactions
    if message.get('reactions'):
        reactions_str = ' '.join([f"{r['emoji']}{r['count']}" for r in message['reactions']])
        lines.append(f"\n👍 Reactions: {reactions_str}")
    
    lines.append("=" * 50)
    
    return '\n'.join(lines)

def main():
    # Get environment variables
    api_id = os.environ.get('TELEGRAM_API_ID')
    api_hash = os.environ.get('TELEGRAM_API_HASH')
    phone_number = os.environ.get('PHONE_NUMBER')
    channel_url = os.environ.get('CHANNEL_URL')
    output_format = os.environ.get('OUTPUT_FORMAT', 'json')
    
    # Validate inputs
    if not all([api_id, api_hash, phone_number]):
        missing = []
        if not api_id: missing.append('TELEGRAM_API_ID')
        if not api_hash: missing.append('TELEGRAM_API_HASH')
        if not phone_number: missing.append('PHONE_NUMBER')
        
        result = {
            'success': False,
            'error': f'Missing required secrets: {", ".join(missing)}'
        }
    elif not channel_url:
        result = {
            'success': False,
            'error': 'No channel URL provided'
        }
    else:
        # Run async function
        import asyncio
        result = asyncio.run(get_channel_message(
            int(api_id),
            api_hash,
            phone_number,
            channel_url
        ))
    
    # Save JSON output
    with open('message_output.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Save text output
    text_output = format_text_output(result)
    with open('message_output.txt', 'w', encoding='utf-8') as f:
        f.write(text_output)
    
    # Print to console
    if output_format == 'text':
        print(text_output)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Exit with error code if failed
    if not result.get('success'):
        sys.exit(1)

if __name__ == '__main__':
    main()
