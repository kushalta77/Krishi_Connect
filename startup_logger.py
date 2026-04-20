"""
Krishi Project - Comprehensive Startup & Connection Logger
This script logs all startup events, database connections, and system information
"""

import os
import sys
import logging
import django
from datetime import datetime
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'krishi.settings')
sys.path.insert(0, str(Path(__file__).parent))

# Initialize Django
django.setup()

from django.conf import settings
from django.db import connection
from django.test.utils import CaptureQueriesContext

# Get startup logger
startup_logger = logging.getLogger('startup')

def log_separator(message=""):
    """Print formatted separator"""
    print("\n" + "="*80)
    if message:
        print(f"  {message}")
        print("="*80)
    else:
        print("="*80 + "\n")

def print_and_log(message, level='info'):
    """Print to console and log"""
    print(message)
    if level == 'info':
        startup_logger.info(message)
    elif level == 'error':
        startup_logger.error(message)
    elif level == 'warning':
        startup_logger.warning(message)
    elif level == 'debug':
        startup_logger.debug(message)
    elif level == 'critical':
        startup_logger.critical(message)

def log_system_info():
    """Log system and environment information"""
    log_separator("SYSTEM & ENVIRONMENT INFORMATION")
    
    info_dict = {
        'Python Version': sys.version,
        'Platform': sys.platform,
        'Python Executable': sys.executable,
        'Working Directory': os.getcwd(),
        'Django Version': django.VERSION,
        'DEBUG Mode': settings.DEBUG,
        'Time Zone': settings.TIME_ZONE,
    }
    
    for key, value in info_dict.items():
        msg = f"{key}: {value}"
        print_and_log(msg, 'info')

def log_project_settings():
    """Log Django project settings"""
    log_separator("PROJECT CONFIGURATION")
    
    config_info = {
        'Base Directory': str(settings.BASE_DIR),
        'Logs Directory': str(settings.LOGS_DIR),
        'Static URL': settings.STATIC_URL,
        'Media URL': settings.MEDIA_URL,
        'Allowed Hosts': settings.ALLOWED_HOSTS if settings.ALLOWED_HOSTS else "[]",
        'Secret Key Set': "Yes" if settings.SECRET_KEY else "No",
    }
    
    for key, value in config_info.items():
        msg = f"{key}: {value}"
        print_and_log(msg, 'info')

def log_installed_apps():
    """Log installed applications"""
    log_separator("INSTALLED APPLICATIONS")
    
    for i, app in enumerate(settings.INSTALLED_APPS, 1):
        msg = f"{i}. {app}"
        print_and_log(msg, 'debug')

def log_database_connection():
    """Test and log database connection"""
    log_separator("DATABASE CONNECTION TEST")
    
    db_config = settings.DATABASES['default']
    
    # Log database configuration
    print_and_log(f"Database Engine: {db_config['ENGINE']}", 'info')
    print_and_log(f"Database Name: {db_config['NAME']}", 'info')
    print_and_log(f"Database User: {db_config['USER']}", 'info')
    print_and_log(f"Database Host: {db_config['HOST']}", 'info')
    print_and_log(f"Database Port: {db_config['PORT']}", 'info')
    
    # Try to connect
    print_and_log("\nAttempting database connection...", 'info')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        print_and_log("✓ Database Connection: SUCCESS", 'info')
        startup_logger.info("✓ Database Connection: SUCCESS")
        
        # Get database info
        try:
            with connection.cursor() as cursor:
                if 'mysql' in db_config['ENGINE'].lower():
                    cursor.execute("SELECT VERSION();")
                    version = cursor.fetchone()[0]
                    print_and_log(f"MySQL Version: {version}", 'info')
                    startup_logger.info(f"MySQL Version: {version}")
        except Exception as e:
            startup_logger.warning(f"Could not fetch database version: {str(e)}")
        
        return True
        
    except Exception as e:
        error_msg = f"✗ Database Connection: FAILED"
        print_and_log(error_msg, 'error')
        print_and_log(f"Error Details: {type(e).__name__}: {str(e)}", 'error')
        startup_logger.error(f"Database Connection Failed: {type(e).__name__}: {str(e)}")
        
        # Provide specific error help
        if 'Connection refused' in str(e):
            help_msg = "HELP: XAMPP MySQL not running. Start XAMPP and ensure MySQL is running on port 3306."
            print_and_log(help_msg, 'error')
            startup_logger.error(help_msg)
        elif 'Unknown database' in str(e):
            help_msg = "HELP: Database 'krishi_db' does not exist. Create it using: CREATE DATABASE krishi_db;"
            print_and_log(help_msg, 'error')
            startup_logger.error(help_msg)
        elif 'Access denied' in str(e):
            help_msg = "HELP: Database credentials incorrect. Check USER and PASSWORD in settings.py"
            print_and_log(help_msg, 'error')
            startup_logger.error(help_msg)
        
        return False

def log_migrations_status():
    """Log database migrations status"""
    log_separator("MIGRATIONS STATUS")
    
    from django.db.migrations.executor import MigrationExecutor
    from django.db import DEFAULT_DB_ALIAS
    
    try:
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        if plan:
            print_and_log(f"Pending migrations: {len(plan)}", 'warning')
            startup_logger.warning(f"Found {len(plan)} pending migrations")
            for migration in plan:
                msg = f"  - {migration}"
                print_and_log(msg, 'warning')
        else:
            print_and_log("✓ All migrations applied", 'info')
            startup_logger.info("✓ All migrations applied")
            
    except Exception as e:
        startup_logger.error(f"Error checking migrations: {str(e)}")
        print_and_log(f"Error checking migrations: {str(e)}", 'error')

def log_static_and_media():
    """Log static and media file configuration"""
    log_separator("STATIC & MEDIA FILES")
    
    paths = {
        'Static URL': settings.STATIC_URL,
        'Static Root': str(settings.STATIC_ROOT),
        'Media URL': settings.MEDIA_URL,
        'Media Root': str(settings.MEDIA_ROOT),
    }
    
    for key, path in paths.items():
        exists = os.path.exists(path) if os.path.isabs(path) else "N/A (URL)"
        status = "✓ Exists" if exists == True else ("✗ Missing" if exists == False else exists)
        msg = f"{key}: {path} [{status}]"
        print_and_log(msg, 'info')

def log_file_structure():
    """Log important project directories"""
    log_separator("PROJECT FILE STRUCTURE")
    
    important_dirs = {
        'Templates': settings.BASE_DIR / 'templates',
        'Static Files': settings.STATIC_ROOT,
        'Media Files': settings.MEDIA_ROOT,
        'Logs': settings.LOGS_DIR,
    }
    
    for name, path in important_dirs.items():
        if os.path.exists(path):
            msg = f"✓ {name}: {path}"
            print_and_log(msg, 'info')
        else:
            msg = f"✗ {name}: {path} [MISSING]"
            print_and_log(msg, 'warning')
            startup_logger.warning(f"Missing directory: {path}")

def log_log_files_location():
    """Log where log files are being stored"""
    log_separator("LOG FILES LOCATION")
    
    log_files = {
        'Main Log': settings.MAIN_LOG_FILE,
        'Error Log': settings.ERROR_LOG_FILE,
        'Database Log': settings.DATABASE_LOG_FILE,
        'Request Log': settings.REQUEST_LOG_FILE,
        'Startup Log': settings.STARTUP_LOG_FILE,
    }
    
    for name, path in log_files.items():
        msg = f"{name}: {path}"
        print_and_log(msg, 'info')

def log_final_status(db_connected):
    """Log final startup status"""
    log_separator("STARTUP STATUS")
    
    status = "✓ READY" if db_connected else "✗ NOT READY"
    color_status = f"\n{status}\n"
    print_and_log(color_status, 'info' if db_connected else 'error')
    
    if db_connected:
        print_and_log("Project is ready to run. Start with: python manage.py runserver", 'info')
    else:
        print_and_log("Fix database connection before running the project.", 'error')
    
    print_and_log(f"\nStartup completed at: {datetime.now()}", 'info')

def main():
    """Run all startup checks and logging"""
    log_separator("KRISHI PROJECT - STARTUP LOG")
    print_and_log(f"Startup initiated at: {datetime.now()}", 'info')
    
    log_system_info()
    log_project_settings()
    log_installed_apps()
    db_connected = log_database_connection()
    
    if db_connected:
        log_migrations_status()
    
    log_static_and_media()
    log_file_structure()
    log_log_files_location()
    log_final_status(db_connected)
    
    log_separator()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n✗ CRITICAL ERROR: {type(e).__name__}: {str(e)}")
        startup_logger.critical(f"Startup failed: {type(e).__name__}: {str(e)}", exc_info=True)
        sys.exit(1)
