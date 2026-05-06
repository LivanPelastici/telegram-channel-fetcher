#!/usr/bin/env python3
"""Send notification via Telegram bot"""

import os
import json
import requests

def send_telegram_message(bot_token, chat_id, text):
    """Send message via Telegram bot"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # Escape HTML
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Format message
    formatted_text = f"<b>📱 New Channel Message</b>\n\n<pre>{text[:3500]}</pre>"
    
    payload = {
        'chat_id': chat_id,
        'text': formatted_text,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        
        if data.get('ok'):
            print(f"✅ Notification sent to {chat_id}")
            return True
        else:
            print(f"❌ Failed: {data.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    bot_token = os.environ.get('BOT_TOKEN')
    notify_chat_id = os.environ.get('NOTIFY_CHAT_ID')
    
    if not bot_token:
        print("❌ BOT_TOKEN not set")
        return
    
    if not notify_chat_id:
        print("ℹ️ No notification chat ID")
        return
    
    # Read message
    try:
        with open('message_output.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if data.get('success') and data.get('message'):
            msg = data['message']
            text = msg.get('text', '')[:500]
            
            # Format notification
            notification = f"Channel: {data['channel']['title']}\n"
            notification += f"Date: {msg['date']}\n"
            notification += f"Type: {msg['type']}\n"
            if msg.get('views'):
                notification += f"Views: {msg['views']}\n"
            notification += f"\n{text}"
            
            send_telegram_message(bot_token, notify_chat_id, notification)
        else:
            send_telegram_message(bot_token, notify_chat_id, "No new messages")
            
    except FileNotFoundError:
        print("❌ message_output.json not found")

if __name__ == '__main__':
    main()
