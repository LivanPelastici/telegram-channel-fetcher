import os
import json
import requests
from datetime import datetime

def extract_channel_info(channel_url):
    """Extract channel username from URL or direct username"""
    if not channel_url:
        return None
    
    channel_url = channel_url.strip().lstrip('@')
    
    if 't.me/' in channel_url:
        channel_url = channel_url.split('t.me/')[-1].split('/')[0]
    
    if '?' in channel_url:
        channel_url = channel_url.split('?')[0]
    
    return channel_url

def get_channel_messages(bot_token, channel_username):
    """Get last message from channel using multiple methods"""
    
    chat_info_url = f"https://api.telegram.org/bot{bot_token}/getChat?chat_id=@{channel_username}"
    
    try:
        chat_response = requests.get(chat_info_url)
        chat_data = chat_response.json()
        
        if not chat_data.get('ok'):
            return {
                'success': False,
                'error': f"Cannot access channel: {chat_data.get('description', 'Unknown error')}"
            }
        
        chat_id = chat_data['result']['id']
        chat_info = {
            'id': chat_id,
            'title': chat_data['result'].get('title', channel_username),
            'username': channel_username,
            'type': chat_data['result'].get('type', 'channel')
        }
        
        updates_url = f"https://api.telegram.org/bot{bot_token}/getUpdates?limit=100&timeout=0"
        updates_response = requests.get(updates_url)
        updates_data = updates_response.json()
        
        last_message = None
        
        if updates_data.get('ok') and updates_data.get('result'):
            for update in reversed(updates_data['result']):
                message = None
                if 'channel_post' in update:
                    if update['channel_post']['chat']['id'] == chat_id:
                        message = update['channel_post']
                elif 'message' in update:
                    if update['message']['chat']['id'] == chat_id:
                        message = update['message']
                
                if message:
                    last_message = parse_message(message)
                    break
        
        if last_message:
            return {
                'success': True,
                'channel': chat_info,
                'message': last_message,
                'fetched_at': datetime.utcnow().isoformat()
            }
        else:
            return {
                'success': True,
                'channel': chat_info,
                'message': None,
                'warning': 'No recent messages in updates. Bot may need to be in channel longer.',
                'fetched_at': datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def parse_message(message):
    """Parse a Telegram message into structured format"""
    parsed = {
        'message_id': message.get('message_id'),
        'date': message.get('date'),
        'date_iso': datetime.fromtimestamp(message.get('date', 0)).isoformat(),
        'type': 'unknown'
    }
    
    if 'text' in message:
        parsed['type'] = 'text'
        parsed['text'] = message['text']
    elif 'caption' in message:
        parsed['type'] = 'media_with_caption'
        parsed['caption'] = message['caption']
    
    if 'photo' in message:
        parsed['type'] = 'photo' if 'text' not in message else 'photo_with_caption'
        parsed['media_info'] = {
            'type': 'photo',
            'file_id': message['photo'][-1]['file_id'],
            'width': message['photo'][-1].get('width'),
            'height': message['photo'][-1].get('height')
        }
    elif 'video' in message:
        parsed['type'] = 'video' if 'caption' not in message else 'video_with_caption'
        parsed['media_info'] = {
            'type': 'video',
            'file_id': message['video']['file_id'],
            'duration': message['video'].get('duration'),
            'mime_type': message['video'].get('mime_type')
        }
    elif 'document' in message:
        parsed['type'] = 'document' if 'caption' not in message else 'document_with_caption'
        parsed['media_info'] = {
            'type': 'document',
            'file_id': message['document']['file_id'],
            'file_name': message['document'].get('file_name'),
            'mime_type': message['document'].get('mime_type'),
            'file_size': message['document'].get('file_size')
        }
    elif 'audio' in message:
        parsed['type'] = 'audio'
        parsed['media_info'] = {
            'type': 'audio',
            'file_id': message['audio']['file_id'],
            'duration': message['audio'].get('duration'),
            'title': message['audio'].get('title'),
            'performer': message['audio'].get('performer')
        }
    elif 'voice' in message:
        parsed['type'] = 'voice'
        parsed['media_info'] = {
            'type': 'voice',
            'file_id': message['voice']['file_id'],
            'duration': message['voice'].get('duration')
        }
    elif 'sticker' in message:
        parsed['type'] = 'sticker'
        parsed['media_info'] = {
            'type': 'sticker',
            'file_id': message['sticker']['file_id'],
            'emoji': message['sticker'].get('emoji')
        }
    
    if 'forward_from' in message:
        parsed['forwarded'] = True
        parsed['forward_from'] = {
            'id': message['forward_from'].get('id'),
            'name': f"{message['forward_from'].get('first_name', '')} {message['forward_from'].get('last_name', '')}".strip(),
            'username': message['forward_from'].get('username')
        }
    
    if 'forward_from_chat' in message:
        parsed['forwarded'] = True
        parsed['forward_from_chat'] = {
            'id': message['forward_from_chat'].get('id'),
            'title': message['forward_from_chat'].get('title'),
            'username': message['forward_from_chat'].get('username')
        }
    
    if 'entities' in message:
        parsed['entities'] = []
        for entity in message['entities']:
            entity_info = {
                'type': entity['type'],
                'offset': entity['offset'],
                'length': entity['length']
            }
            if entity['type'] == 'url' and 'text' in message:
                entity_info['url'] = message['text'][entity['offset']:entity['offset']+entity['length']]
            parsed['entities'].append(entity_info)
    
    return parsed

def save_outputs(result, output_format):
    """Save results in both JSON and text formats"""
    
    with open('message_output.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    with open('message_output.txt', 'w', encoding='utf-8') as f:
        if not result.get('success'):
            f.write(f"Error: {result.get('error', 'Unknown error')}\n")
        elif not result.get('message'):
            f.write(f"No messages found in channel: {result['channel']['title']}\n")
            f.write(f"Note: {result.get('warning', '')}\n")
        else:
            msg = result['message']
            ch = result['channel']
            
            f.write(f"Channel: {ch['title']} (@{ch['username']})\n")
            f.write(f"Message ID: {msg['message_id']}\n")
            f.write(f"Date: {msg['date_iso']}\n")
            f.write(f"Type: {msg['type']}\n")
            f.write("-" * 50 + "\n")
            
            if 'text' in msg:
                f.write(f"Text: {msg['text']}\n")
            if 'caption' in msg:
                f.write(f"Caption: {msg['caption']}\n")
            if 'media_info' in msg:
                f.write(f"Media: {json.dumps(msg['media_info'], indent=2)}\n")

def main():
    bot_token = os.environ.get('BOT_TOKEN')
    channel_url = os.environ.get('CHANNEL_URL')
    output_format = os.environ.get('OUTPUT_FORMAT', 'json')
    
    if not bot_token or not channel_url:
        result = {
            'success': False,
            'error': 'Missing BOT_TOKEN or CHANNEL_URL'
        }
        save_outputs(result, output_format)
        print(json.dumps(result))
        return
    
    channel_username = extract_channel_info(channel_url)
    
    if not channel_username:
        result = {
            'success': False,
            'error': f'Invalid channel URL: {channel_url}'
        }
        save_outputs(result, output_format)
        print(json.dumps(result))
        return
    
    result = get_channel_messages(bot_token, channel_username)
    save_outputs(result, output_format)
    
    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"status={'success' if result.get('success') else 'failed'}\n")
            f.write(f"message_json={json.dumps(result)}\n")
            
            if result.get('message') and result['message'].get('text'):
                text = result['message']['text'][:200]
                f.write(f"message_text={text}\n")
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()