# 🔒 Security Guide - SeatSeeker

This document outlines security considerations for the SeatSeeker program.

## 🚨 Critical Security Items

### **DO NOT COMMIT THESE FILES:**
- `.env` - Contains your email credentials
- `database.db` - Contains user subscription data
- Any files with hardcoded passwords or API keys

### **SAFE TO COMMIT:**
- `config.env` - Template file (no real credentials)
- `course.json` - Public course data only
- `available_CRNS.txt` - Public course numbers only

## 🔐 What's Protected

### 1. **Email Credentials**
- **Location**: `.env` file (created from `config.env` template)
- **Contains**: Email address, app password, SMTP settings
- **Protection**: Listed in `.gitignore`, never committed to repository

### 2. **User Data**
- **Location**: `database.db` (SQLite database)
- **Contains**: User emails, course subscriptions, timestamps
- **Protection**: Listed in `.gitignore`, never committed to repository

### 3. **Environment Configuration**
- **Location**: `.env` file
- **Contains**: All user-specific settings
- **Protection**: Listed in `.gitignore`, created locally during installation

## 🛡️ Security Measures Implemented

### 1. **No Hardcoded Credentials**
- ✅ Removed hardcoded email/password from code
- ✅ All credentials now use environment variables
- ✅ Template file (`config.env`) contains no real data

### 2. **Comprehensive .gitignore**
- ✅ Protects `.env` files
- ✅ Protects database files
- ✅ Protects Python cache files
- ✅ Protects virtual environments
- ✅ Protects temporary files

### 3. **Environment Variable Usage**
- ✅ All sensitive data loaded from environment
- ✅ Clear error messages if configuration missing
- ✅ Secure credential handling

## 📋 Pre-Push Checklist

Before pushing code to any repository, ensure:

- [ ] No `.env` files exist in the repository
- [ ] No `database.db` files exist in the repository
- [ ] No hardcoded passwords in any code files
- [ ] `.gitignore` file is present and up-to-date
- [ ] `config.env` template contains no real credentials

## 🔍 How to Check for Sensitive Data

### Search for hardcoded credentials:
```bash
grep -r "password\|secret\|key\|token" . --exclude-dir=venv --exclude-dir=__pycache__
```

### Check for .env files:
```bash
find . -name ".env*" -type f
```

### Check for database files:
```bash
find . -name "*.db" -o -name "*.sqlite*"
```

## 🚀 Safe Distribution

When distributing the program:

1. **Include**: All source code, templates, documentation
2. **Exclude**: Any `.env` files, database files, virtual environments
3. **Template**: Provide `config.env` as a template only
4. **Instructions**: Guide users to create their own `.env` file

## 📧 Email Security Best Practices

### Gmail Setup:
1. Enable 2-factor authentication
2. Generate App Password (not regular password)
3. Use App Password in `.env` file
4. Never commit the `.env` file

### Other Email Providers:
1. Check provider's SMTP settings
2. Use appropriate authentication method
3. Test email sending before deployment

## 🔄 Regular Security Maintenance

- [ ] Regularly update dependencies
- [ ] Monitor for security vulnerabilities
- [ ] Review access logs if applicable
- [ ] Keep email credentials secure
- [ ] Rotate passwords periodically

## 📞 Security Issues

If you discover a security vulnerability:

1. **DO NOT** create a public issue
2. **DO** contact the maintainer privately
3. **DO** provide detailed information about the issue
4. **DO** wait for acknowledgment before public disclosure

---

**Remember: Security is everyone's responsibility!** 🔒
