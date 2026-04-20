"""
Krishi Project - Log Monitoring Utility
Monitor logs in real-time while your Django server is running
"""

import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Get project directories
PROJECT_DIR = Path(__file__).parent
LOGS_DIR = PROJECT_DIR / 'logs'

class LogMonitor:
    """Monitor and display log files"""
    
    def __init__(self, log_files=None):
        """Initialize monitor with specific log files"""
        self.log_files = log_files or self.get_available_logs()
        self.file_positions = {}
        self.initialize_positions()
    
    @staticmethod
    def get_available_logs():
        """Get all available log files"""
        if not LOGS_DIR.exists():
            print(f"ERROR: Logs directory not found: {LOGS_DIR}")
            return []
        
        logs = {
            'errors': LOGS_DIR / 'krishi_errors.log',
            'startup': LOGS_DIR / 'krishi_startup.log',
            'database': LOGS_DIR / 'krishi_database.log',
            'requests': LOGS_DIR / 'krishi_requests.log',
            'main': LOGS_DIR / 'krishi_main.log',
        }
        
        return {k: v for k, v in logs.items() if v.exists()}
    
    def initialize_positions(self):
        """Initialize file reading positions"""
        for name, filepath in self.log_files.items():
            try:
                self.file_positions[name] = filepath.stat().st_size
            except:
                self.file_positions[name] = 0
    
    def read_new_lines(self, filepath, last_pos):
        """Read new lines from file since last position"""
        try:
            current_size = filepath.stat().st_size
            
            # Handle file rotation (size decreased)
            if current_size < last_pos:
                last_pos = 0
            
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(last_pos)
                new_lines = f.readlines()
                new_pos = f.tell()
            
            return new_lines, new_pos
        except Exception as e:
            return [], last_pos
    
    def print_header(self, log_name):
        """Print log header"""
        print(f"\n{'='*80}")
        print(f"  {log_name.upper()} LOG")
        print(f"  Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
    
    def print_log_lines(self, lines, log_name):
        """Print log lines with color coding"""
        if not lines:
            return
        
        for line in lines:
            line = line.rstrip()
            if not line:
                continue
            
            # Color code based on log level
            if '[ERROR]' in line or '[CRITICAL]' in line:
                print(f"\033[91m{line}\033[0m")  # Red
            elif '[WARNING]' in line:
                print(f"\033[93m{line}\033[0m")  # Yellow
            elif '[INFO]' in line:
                print(f"\033[92m{line}\033[0m")  # Green
            elif '[DEBUG]' in line:
                print(f"\033[94m{line}\033[0m")  # Blue
            else:
                print(line)
    
    def monitor_single_log(self, log_name, filepath, interval=2):
        """Monitor single log file continuously"""
        print(f"Monitoring: {log_name}")
        print(f"File: {filepath}")
        print(f"Update interval: {interval} seconds")
        print("\nPress Ctrl+C to stop\n")
        
        try:
            while True:
                new_lines, new_pos = self.read_new_lines(
                    filepath,
                    self.file_positions[log_name]
                )
                
                if new_lines:
                    self.print_header(log_name)
                    self.print_log_lines(new_lines, log_name)
                    self.file_positions[log_name] = new_pos
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print(f"\n\nMonitoring stopped.")
    
    def monitor_all_logs(self, interval=2):
        """Monitor all logs continuously"""
        print("Monitoring all log files...")
        print(f"Update interval: {interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                has_updates = False
                
                for log_name, filepath in self.log_files.items():
                    new_lines, new_pos = self.read_new_lines(
                        filepath,
                        self.file_positions[log_name]
                    )
                    
                    if new_lines:
                        if not has_updates:
                            has_updates = True
                        
                        self.print_header(log_name)
                        self.print_log_lines(new_lines, log_name)
                        self.file_positions[log_name] = new_pos
                
                if not has_updates:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for new log entries...", end='\r')
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print(f"\n\nMonitoring stopped.")
    
    def show_errors_only(self, lines_to_show=20):
        """Show only recent errors"""
        error_file = LOGS_DIR / 'krishi_errors.log'
        
        if not error_file.exists():
            print("No error log file found.")
            return
        
        try:
            with open(error_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading error log: {e}")
            return
        
        # Get last N error lines
        display_lines = lines[-lines_to_show:] if len(lines) > lines_to_show else lines
        
        print(f"{'='*80}")
        print(f"  RECENT ERRORS (Last {len(display_lines)} lines)")
        print(f"{'='*80}\n")
        
        for line in display_lines:
            print(f"\033[91m{line}\033[0m", end='')  # Red
    
    def show_summary(self):
        """Show summary of all logs"""
        print(f"{'='*80}")
        print("  LOG SUMMARY")
        print(f"{'='*80}\n")
        
        stats = {}
        
        for log_name, filepath in self.log_files.items():
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                error_count = len([l for l in lines if '[ERROR]' in l])
                warning_count = len([l for l in lines if '[WARNING]' in l])
                info_count = len([l for l in lines if '[INFO]' in l])
                
                stats[log_name] = {
                    'total_lines': len(lines),
                    'errors': error_count,
                    'warnings': warning_count,
                    'info': info_count,
                    'size_mb': filepath.stat().st_size / (1024*1024)
                }
            except:
                pass
        
        print(f"{'Log':<15} {'Total':<10} {'Errors':<10} {'Warnings':<10} {'Size (MB)':<10}")
        print("-" * 55)
        
        for log_name, stat in stats.items():
            print(f"{log_name:<15} {stat['total_lines']:<10} {stat['errors']:<10} {stat['warnings']:<10} {stat['size_mb']:<10.2f}")


def main():
    parser = argparse.ArgumentParser(
        description='Krishi Project Log Monitor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python log_monitor.py -m errors          Monitor error log
  python log_monitor.py -m all             Monitor all logs
  python log_monitor.py -s                 Show error summary
  python log_monitor.py --summary          Show all logs summary
  python log_monitor.py --errors           Show recent errors
        """
    )
    
    parser.add_argument('-m', '--monitor',
                        choices=['all', 'errors', 'startup', 'database', 'requests', 'main'],
                        help='Monitor specific log or all logs')
    parser.add_argument('-i', '--interval',
                        type=int, default=2,
                        help='Update interval in seconds (default: 2)')
    parser.add_argument('-s', '--summary',
                        action='store_true',
                        help='Show log summary')
    parser.add_argument('-e', '--errors',
                        action='store_true',
                        help='Show recent errors')
    parser.add_argument('-l', '--list',
                        action='store_true',
                        help='List available log files')
    
    args = parser.parse_args()
    
    monitor = LogMonitor()
    
    if not monitor.log_files:
        print("ERROR: No log files found!")
        print(f"Expected logs in: {LOGS_DIR}")
        sys.exit(1)
    
    if args.list:
        print(f"{'='*80}")
        print("  AVAILABLE LOG FILES")
        print(f"{'='*80}\n")
        for name, filepath in monitor.log_files.items():
            size_mb = filepath.stat().st_size / (1024*1024)
            print(f"{name:<15} {str(filepath):<60} ({size_mb:.2f} MB)")
        return
    
    if args.summary:
        monitor.show_summary()
        return
    
    if args.errors:
        monitor.show_errors_only()
        return
    
    if args.monitor == 'all':
        monitor.monitor_all_logs(args.interval)
    elif args.monitor in monitor.log_files:
        filepath = monitor.log_files[args.monitor]
        monitor.monitor_single_log(args.monitor, filepath, args.interval)
    else:
        print("No monitoring option specified. Use -h for help")
        print("\nQuick commands:")
        print("  Monitor errors only:    python log_monitor.py -m errors")
        print("  Monitor all logs:       python log_monitor.py -m all")
        print("  Show summary:           python log_monitor.py --summary")
        print("  List all logs:          python log_monitor.py --list")


if __name__ == '__main__':
    main()
