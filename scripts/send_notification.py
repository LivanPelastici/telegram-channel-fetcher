import os
import requests

def send_telegram_message(bot_token, chat_id, text):
    """Send a formatted message to a Telegram chat"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    formatted_text = f"<b>📱 New Message Alert</b>\n\n<pre>{text}</pre>"
    
    # Telegram limit: 4096
    if len(formatted_text) > 4000:
        formatted_text = formatted_text[:4000] + "\n... [truncated]"
    
    payload = {
        'chat_id': chat_id,
        'text': formatted_text,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        
        if data.get('ok'):
            print(f"✅ Notification sent successfully to chat ID: {chat_id}")
            return True
        else:
            print(f"❌ Failed to send notification: {data.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Error sending notification: {e}")
        return False

def main():
    bot_token = os.environ.get('BOT_TOKEN')
    notify_chat_id = os.environ.get('NOTIFY_CHAT_ID')
    
    if not bot_token:
        print("❌ BOT_TOKEN not set for notification")
        return
    
    if not notify_chat_id:
        print("ℹ️ No notification chat ID provided, skipping notification")
        return
    
    print(f"📤 Sending notification to chat ID: {notify_chat_id}")
    
    try:
        with open('message_output.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "Full JSON Response:" in content:
            content = content.split("Full JSON Response:")[0].strip()
        
        send_telegram_message(bot_token, notify_chat_id, content)
        
    except FileNotFoundError:
        print("❌ No message_output.txt file found")
        send_telegram_message(bot_token, notify_chat_id, "❌ Error: Could not retrieve message")

if __name__ == "__main__":
    main()