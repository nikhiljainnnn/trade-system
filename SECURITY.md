# 🔒 Security Guidelines - Bitcoin Options Alert System

## ⚠️ IMPORTANT: Credential Security

### 🚨 **NEVER commit sensitive credentials to GitHub!**

This project has been updated to use environment variables for all sensitive information.

## 🛡️ **Secure Setup Instructions**

### **Local Development:**

1. **Create `.env` file** (never commit this):
   ```bash
   cp .env.example .env
   ```

2. **Add your credentials to `.env`**:
   ```
   TELEGRAM_BOT_TOKEN=your_actual_bot_token_here
   TELEGRAM_CHAT_ID=your_actual_chat_id_here
   ```

3. **The `.env` file is automatically ignored by Git**

### **Railway Cloud Deployment:**

1. **Go to Railway dashboard**
2. **Navigate to Variables tab**
3. **Add environment variables**:
   - `TELEGRAM_BOT_TOKEN`: Your bot token
   - `TELEGRAM_CHAT_ID`: Your chat ID

### **Testing:**

- **Use**: `python test_telegram_secure.py` ✅
- **Avoid**: `test_telegram.py` (has placeholder credentials)

## 📋 **Security Checklist**

- [ ] `.env` file is in `.gitignore`
- [ ] No hardcoded credentials in any `.py` files
- [ ] Railway environment variables are set
- [ ] Using `test_telegram_secure.py` for testing
- [ ] All sensitive files are excluded from Git

## 🚫 **What's Protected**

### **Files excluded from Git:**
- `.env` (local credentials)
- `.env.*` (environment-specific files)
- `*_secret.py` (any secret files)
- `*_secrets.yaml` (credential files)
- `test_telegram_local.py` (local test files)

### **Environment Variables Used:**
- `TELEGRAM_BOT_TOKEN` - Telegram bot authentication
- `TELEGRAM_CHAT_ID` - Your chat ID for alerts

## 🔧 **Migration from Hardcoded Credentials**

If you have old files with hardcoded credentials:

1. **Move credentials to `.env` file**
2. **Update code to use `os.getenv()`**
3. **Remove hardcoded values**
4. **Test with secure methods**
5. **Commit cleaned files**

## 🎯 **Best Practices**

### ✅ **Do:**
- Use environment variables for all secrets
- Test with `test_telegram_secure.py`
- Keep `.env` file local only
- Use Railway's environment variable system

### ❌ **Don't:**
- Commit `.env` files to Git
- Hardcode credentials in Python files
- Share credential files
- Push sensitive data to public repositories

## 🆘 **Emergency Response**

**If credentials were accidentally committed:**

1. **Immediately revoke the bot token**
2. **Create new bot token**
3. **Update all systems with new credentials**
4. **Remove sensitive commits from Git history**
5. **Update this documentation**

---

**🔒 Keep your credentials secure and your trading system safe!**