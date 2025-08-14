#!/usr/bin/env python3
"""
SeatSeeker - UC Merced Course Availability Notifier
Main launcher script for the downloadable program.
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'flask',
        'requests',
        'sqlite3'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install dependencies with:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def start_dashboard(port=5000, debug=False):
    """Start the web dashboard"""
    print(f"🚀 Starting SeatSeeker Dashboard...")
    print(f"🌐 Dashboard will be available at: http://localhost:{port}")
    print(f"📧 Email notifications will be sent when courses become available")
    print(f"⏰ Press Ctrl+C to stop the dashboard")
    print("-" * 50)
    
    try:
        from app import app
        app.run(host='0.0.0.0', port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")

def start_scheduler(interval=300):
    """Start the background scheduler"""
    print(f"⏰ Starting SeatSeeker Scheduler...")
    print(f"🔄 Checking courses every {interval} seconds")
    print(f"📧 Sending email notifications when courses become available")
    print(f"⏰ Press Ctrl+C to stop the scheduler")
    print("-" * 50)
    
    try:
        from checker_service import main
        main()
    except KeyboardInterrupt:
        print("\n🛑 Scheduler stopped by user")
    except Exception as e:
        print(f"❌ Error starting scheduler: {e}")

def setup_database():
    """Initialize the database"""
    print("🗄️  Setting up database...")
    try:
        from app import init_db
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Error setting up database: {e}")

def show_status():
    """Show current system status"""
    print("📊 SeatSeeker Status")
    print("-" * 30)
    
    # Check database
    db_path = Path(__file__).parent / 'database.db'
    if db_path.exists():
        print(f"✅ Database: {db_path}")
    else:
        print("❌ Database: Not found")
    
    # Check configuration
    config_path = Path(__file__).parent / 'config.env'
    if config_path.exists():
        print(f"✅ Configuration: {config_path}")
    else:
        print("❌ Configuration: config.env not found")
    
    # Check if scheduler is running
    print("🔄 Scheduler: Check with 'ps aux | grep checker_service'")

def main():
    parser = argparse.ArgumentParser(
        description="SeatSeeker - UC Merced Course Availability Notifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py dashboard          # Start web dashboard
  python run.py scheduler          # Start background scheduler
  python run.py dashboard --port 8080  # Start dashboard on port 8080
  python run.py setup              # Setup database and configuration
  python run.py status             # Show system status
        """
    )
    
    parser.add_argument('command', choices=['dashboard', 'scheduler', 'setup', 'status'],
                       help='Command to run')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port for dashboard (default: 5000)')
    parser.add_argument('--interval', type=int, default=300,
                       help='Check interval in seconds for scheduler (default: 300)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode for dashboard')
    
    args = parser.parse_args()
    
    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    if args.command == 'dashboard':
        start_dashboard(args.port, args.debug)
    elif args.command == 'scheduler':
        start_scheduler(args.interval)
    elif args.command == 'setup':
        setup_database()
    elif args.command == 'status':
        show_status()

if __name__ == '__main__':
    main()
