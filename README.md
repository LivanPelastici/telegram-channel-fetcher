# 📱 Telegram Channel Message Fetcher

> Fetch the last message from any public Telegram channel using GitHub Actions - **no bot required!**

[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://telegram.org)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

---

## About 
goal of this project was to bring an idea to users how they can use workflows to get telegram messages , im not looking any updates for that repo .
anyone can use this code freely 

## ✨ Features

- ✅ **No bot needed** - Works with your Telegram user account
- ✅ **Any public channel** - Even if you're not a member
- ✅ **One-click execution** - Trigger from GitHub web interface
- ✅ **Artifact download** - Get results as JSON or text
- ✅ **Free to use** - Runs on GitHub Actions (free tier)
- ✅ **Secure** - Credentials encrypted as GitHub secrets

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Get Your Telegram API Credentials

1. Go to **[https://my.telegram.org](https://my.telegram.org)**
2. Login with your phone number
3. Click **"API Development Tools"**
4. Fill the form:
   - App title: `GitHub Fetcher`
   - Short name: `ghfetch`
   - Platform: `Desktop`
5. Click **"Create application"**
6. You'll receive:
   - **api_id**: `12345678`
   - **api_hash**: `abc123def456...`

> ⚠️ **Never share these credentials!** They give access to your Telegram account.

---

### Step 2: Add Files to Your Repository

**Create this file structure:**
