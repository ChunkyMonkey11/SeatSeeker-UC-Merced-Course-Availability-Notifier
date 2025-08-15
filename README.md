# 🎓 SeatSeeker - UC Merced Course Availability Notifier

**SeatSeeker** is a self-hosted, downloadable program that monitors UC Merced's course registration system and notifies you via email when courses become available. Never miss your chance to enroll in the class you need again!

## ✨ Features

- 🎯 **Complete Course Coverage** - Monitors ALL 53+ subject codes at UC Merced
- 🌐 **Beautiful Web Dashboard** - Easy-to-use interface for managing subscriptions
- 📧 **Email Notifications** - Instant alerts when courses become available
- ⏰ **Background Monitoring** - Runs continuously in the background
- 🔒 **Self-Hosted** - Your data stays on your machine
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🗄️ **SQLite Database** - Lightweight, no external database required

## 🚀 Quick Start - Run on Your Own Machine

### Prerequisites

Before you begin, make sure you have:

- **Python 3.8 or higher** installed on your machine
- **pip3** (Python package installer) 
- **Git** (to download the code) or ability to download files
- **A Gmail account** (recommended for email notifications)

#### Check if you have Python installed:
```bash
python3 --version
```

If you don't have Python, download it from [python.org](https://python.org)

### Step 1: Download the Program

**Option A: Using Git (Recommended)**
```bash
git clone <repository-url>
cd seatseeker/main
```

**Option B: Manual Download**
1. Download the ZIP file from the repository
2. Extract it to a folder on your computer
3. Open terminal/command prompt
4. Navigate to the `main` folder

### Step 2: Run the Installation Script

**On Mac/Linux:**
```bash
chmod +x install.sh
./install.sh
```

**On Windows:**
```bash
# If you have Git Bash or WSL, use the same commands as Mac/Linux
# Otherwise, run these commands manually:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py setup
```

### Step 3: Configure Your Email Settings

1. **Open the `.env` file** that was created in the main folder
2. **Edit these lines** with your email information:

```env
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
```

#### Gmail Setup (Recommended):
1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to [Google Account Settings](https://myaccount.google.com/)
   - Click "Security" → "2-Step Verification" → "App passwords"
   - Generate a password for "Mail"
   - Use this 16-character password in your `.env` file
3. **Never use your regular Gmail password!**

#### Other Email Providers:
- Update `SMTP_SERVER` and `SMTP_PORT` for your provider
- Some providers may require different authentication

### Step 4: Start the Program

You need to run **two parts** of the program:

#### Part 1: Start the Web Dashboard
```bash
python run.py dashboard
```

You should see:
```
🚀 Starting SeatSeeker Dashboard...
🌐 Dashboard will be available at: http://localhost:5000
📧 Email notifications will be sent when courses become available
⏰ Press Ctrl+C to stop the dashboard
```

#### Part 2: Start the Background Monitor (New Terminal)
Open a **new terminal window** and run:
```bash
python run.py scheduler
```

You should see:
```
⏰ Starting SeatSeeker Scheduler...
🔄 Checking courses every 300 seconds
📧 Sending email notifications when courses become available
⏰ Press Ctrl+C to stop the scheduler
```

### Step 5: Access Your Dashboard

1. **Open your web browser**
2. **Go to**: `http://localhost:5000`
3. **You should see the SeatSeeker dashboard!**

## 📋 How to Use the Dashboard

### Adding Course Subscriptions:
1. **Enter your email** in the "Email Address" field
2. **Find your course CRNs** (Course Registration Numbers):
   - Go to [UC Merced Course Registration](https://reg-prod.ec.ucmerced.edu/)
   - Search for your desired courses
   - Note the CRN numbers (e.g., 30119, 33000)
3. **Enter the CRNs** in the "Course Registration Numbers" field (separated by commas)
4. **Click "Subscribe to Notifications"**

### Viewing Your Subscriptions:
- Your active subscriptions appear on the right side
- Status shows "PENDING" until a course becomes available
- When a course opens, you'll get an email notification

## ⚙️ Configuration Options

### Customizing Check Intervals

Edit your `.env` file to change how often courses are checked:

```env
CHECK_INTERVAL=300          # Check every 5 minutes (default)
ERROR_RETRY_INTERVAL=600    # Retry after 10 minutes on error
```

### Changing the Dashboard Port

If port 5000 is already in use:

```bash
python run.py dashboard --port 8080
```

Then access: `http://localhost:8080`

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### "Python not found" or "python3 not found"
```bash
# Try these commands:
python --version
python3 --version
py --version  # On Windows
```

**Solution**: Install Python from [python.org](https://python.org)

#### "pip not found" or "pip3 not found"
```bash
# Try these commands:
pip --version
pip3 --version
```

**Solution**: Install pip with your Python installation

#### "Module not found" errors
```bash
# Make sure you're in the virtual environment
source venv/bin/activate  # On Mac/Linux
venv\Scripts\activate     # On Windows

# Reinstall dependencies
pip install -r requirements.txt
```

#### "Email not sending" errors
1. **Check your `.env` file** - make sure all fields are filled
2. **For Gmail**: Use an App Password, not your regular password
3. **Test your email settings**:
   ```bash
   python run.py status
   ```

#### "Dashboard not loading"
1. **Check if the port is in use**:
   ```bash
   python run.py dashboard --port 8080
   ```
2. **Check firewall settings** - allow Python/Flask
3. **Try a different browser**

#### "Scheduler not working"
1. **Make sure the scheduler is running** in a separate terminal
2. **Check for error messages** in the scheduler terminal
3. **Verify your email configuration** in `.env`

### Getting Help

If you're still having issues:

1. **Check the console output** for error messages
2. **Verify your Python version**: `python3 --version`
3. **Check your `.env` file** configuration
4. **Try running in debug mode**:
   ```bash
   python run.py dashboard --debug
   ```

## 📱 Running on Different Operating Systems

### Windows
1. Install Python from [python.org](https://python.org)
2. Use Command Prompt or PowerShell
3. Commands are the same, but use `venv\Scripts\activate`

### Mac
1. Python usually comes pre-installed
2. Use Terminal app
3. All commands work as shown above

### Linux
1. Install Python: `sudo apt install python3 python3-pip` (Ubuntu/Debian)
2. Use terminal
3. All commands work as shown above

## 🔄 Keeping the Program Running

### For Continuous Monitoring:

#### Option 1: Keep Terminals Open
- Keep both terminal windows open
- Don't close them while you want monitoring active

#### Option 2: Use Screen/Tmux (Advanced)
```bash
# Install screen
sudo apt install screen  # Ubuntu/Debian
brew install screen      # Mac

# Start dashboard in screen
screen -S dashboard
python run.py dashboard
# Press Ctrl+A, then D to detach

# Start scheduler in screen
screen -S scheduler
python run.py scheduler
# Press Ctrl+A, then D to detach

# Reattach to screens
screen -r dashboard
screen -r scheduler
```

#### Option 3: System Service (Advanced)
Create systemd services for automatic startup (Linux only)

## 📊 Monitoring Your Program

### Check Program Status
```bash
python run.py status
```

### View Logs
- Dashboard logs appear in the terminal where you started it
- Scheduler logs appear in the scheduler terminal
- Enable debug mode for detailed logs:
  ```bash
  python run.py dashboard --debug
  ```

### Stop the Program
- **Dashboard**: Press `Ctrl+C` in the dashboard terminal
- **Scheduler**: Press `Ctrl+C` in the scheduler terminal

## 🔒 Security Notes

- Your `.env` file contains your email credentials - keep it secure
- The database file contains your subscription data - it's stored locally
- Never share your `.env` file or database file
- The program only connects to UC Merced's course registration system

## 📞 Support

If you need help:

1. **Check this README** for troubleshooting steps
2. **Review the error messages** in your terminal
3. **Verify your configuration** in the `.env` file
4. **Open an issue** on the project repository with:
   - Your operating system
   - Python version
   - Error messages
   - Steps you've tried

---

## 🎯 Quick Reference Commands

```bash
# Installation
./install.sh

# Start dashboard
python run.py dashboard

# Start scheduler (in new terminal)
python run.py scheduler

# Check status
python run.py status

# Setup database
python run.py setup

# Custom port
python run.py dashboard --port 8080

# Debug mode
python run.py dashboard --debug
```

---

**🎉 Happy course hunting with SeatSeeker!**

*Remember: Keep both the dashboard and scheduler running for full functionality!*
