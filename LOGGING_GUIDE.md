# Krishi Project - Comprehensive Logging Guide

## Overview

This Krishi project includes a comprehensive logging system that tracks:
- **Startup events** and system information
- **Database connections** and queries
- **HTTP requests and responses**
- **All errors with detailed traceback**
- **System-level debug information**

## Log Files Location

All log files are stored in the `logs/` directory at the project root:

```
krishi/
├── logs/
│   ├── krishi_main.log          # Main application log (all events)
│   ├── krishi_errors.log        # Error-specific log
│   ├── krishi_database.log      # Database connection and query logs
│   ├── krishi_requests.log      # HTTP request/response logs
│   └── krishi_startup.log       # Startup and initialization logs
```

Each log file uses rotating file handlers:
- **Max file size**: 10MB for most logs, 5MB for startup log
- **Backup count**: 10 backups kept (when log reaches max size, it rotates)
- **Format**: UTF-8 encoding for all files

---

## Quick Start

### 1. Run the Startup Logger (FIRST THING TO DO)

```bash
# Navigate to project directory
cd krishi_Connect\krishicon\krishi

# Run the startup logger
python startup_logger.py
```

**What it does:**
- Checks Python and Django setup
- Tests MySQL/Database connection
- Shows all project configurations
- Reports any connection issues with specific help
- Suggests fixes if database is not running

**Output will show:**
```
================================================================================
  KRISHI PROJECT - STARTUP LOG
================================================================================

[INFO] Startup initiated at: 2024-01-15 10:30:45
...
[DATABASE CONNECTION TEST]
Database Engine: django.db.backends.mysql
Database Name: krishi_db
Database User: root
Database Host: localhost
Database Port: 3306

Attempting database connection...
✓ Database Connection: SUCCESS
MySQL Version: 8.0.36
...
```

### 2. Start Your Development Server

```bash
python manage.py runserver
```

---

## Understanding Log File Contents

### A. Main Log File (`krishi_main.log`)

Contains ALL application events with DEBUG and above levels.

**Sample entries:**
```
[DEBUG] 2024-01-15 10:31:22 | krishi.views | get_products:45 | Fetching products for user: john_doe
[INFO] 2024-01-15 10:31:23 | krishi.models | save:102 | New vegetable saved: Tomato
[WARNING] 2024-01-15 10:31:25 | krishi_app | views | cart_total:156 | Cart is empty for user: anonymous
```

**When to use:**
- General troubleshooting
- Tracking application flow
- Performance analysis

---

### B. Error Log File (`krishi_errors.log`)

ONLY captures ERROR and CRITICAL level events with full traceback.

**Sample entries:**
```
[ERROR] 2024-01-15 10:32:10 | /krishi/products/views.py:78 | get_product_list() | 
Product not found
Exception Type: <class 'Product.DoesNotExist'>

Traceback (most recent call last):
  File "/path/to/views.py", line 78, in get_product_list
    product = Product.objects.get(id=product_id)
  File "/path/to/models.py", line 45, in get
    return super().get(*args, **kwargs)
Product.DoesNotExist: Product matching query does not exist.
```

**When to use:**
- **Critical for debugging** - start here when something breaks
- Shows exact file, line number, and function
- Includes complete error traceback
- Helps identify root cause quickly

---

### C. Database Log File (`krishi_database.log`)

Logs all database connections, queries, and operations.

**Sample entries:**
```
[DEBUG] 2024-01-15 10:30:45 | django.db.backends.mysql | connect:215 | Creating database connection
[DEBUG] 2024-01-15 10:30:46 | django.db.backends.mysql | execute:89 | SELECT VERSION();
[DEBUG] 2024-01-15 10:30:47 | krishi_app.models | save:50 | INSERT INTO krishi_app_vegetable (name, price) VALUES ('Tomato', 50.00)
[DEBUG] 2024-01-15 10:31:02 | django.db.backends.mysql | close:180 | Connection closed
```

**When to use:**
- Check if database connection is working
- Debug SQL queries
- Monitor database performance
- Track migration execution

---

### D. Request Log File (`krishi_requests.log`)

Logs every HTTP request and response with metadata.

**Sample REQUEST entry:**
```
[REQUEST] {
  'method': 'POST',
  'path': '/products/add-to-cart/',
  'client_ip': '192.168.1.100',
  'user': 'john_doe',
  'content_type': 'application/json',
  'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
  'post_data': {'product_id': 5, 'quantity': 2}
}
```

**Sample RESPONSE entry:**
```
[RESPONSE] {
  'method': 'POST',
  'path': '/products/add-to-cart/',
  'status_code': 200,
  'content_type': 'application/json',
  'client_ip': '192.168.1.100'
}
```

**When to use:**
- Debug API requests
- Track user interactions
- Monitor response codes (200, 404, 500, etc.)
- Analyze request patterns

---

### E. Startup Log File (`krishi_startup.log`)

Comprehensive startup information - same as `startup_logger.py` output.

**Sample entries:**
```
[INFO] 2024-01-15 10:30:20 | startup_logger.py:150 | main() | Python Version: 3.11.2
[INFO] 2024-01-15 10:30:20 | startup_logger.py:155 | main() | Platform: win32
[INFO] 2024-01-15 10:30:21 | startup_logger.py:200 | log_database_connection() | Database Engine: django.db.backends.mysql
[ERROR] 2024-01-15 10:30:22 | startup_logger.py:220 | log_database_connection() | Database Connection Failed: OperationalError: (2003, "Can't connect to MySQL server on 'localhost' (10061)")
[ERROR] 2024-01-15 10:30:22 | startup_logger.py:225 | log_database_connection() | HELP: XAMPP MySQL not running. Start XAMPP and ensure MySQL is running on port 3306.
```

**When to use:**
- Troubleshoot startup issues
- Verify system configuration
- Check initial database connection
- Review initial setup problems

---

## Common Issues & How to Find Them

### Issue 1: Database Connection Not Working

**Steps:**
1. Look at `krishi_startup.log` or run `startup_logger.py`
2. Check for error messages like:
   - `"Can't connect to MySQL server"` → XAMPP MySQL not running
   - `"Unknown database"` → Database doesn't exist
   - `"Access denied"` → Wrong credentials

**How to fix:**
- Start XAMPP Control Panel
- Click "Start" next to MySQL
- Run `startup_logger.py` again to verify

---

### Issue 2: Application Error

**Steps:**
1. Open `krishi_errors.log`
2. Look for `[ERROR]` or `[CRITICAL]` entries
3. Note the file path and line number
4. Check the traceback for the root cause

**Example:**
```
File "/krishi/products/views.py", line 78, in get_product
    product = Product.objects.get(id=product_id)
Product.DoesNotExist: Product matching query does not exist.
```
→ Product ID doesn't exist in database, check ID before query

---

### Issue 3: Request Not Working Properly

**Steps:**
1. Open `krishi_requests.log`
2. Find the problematic request
3. Check the response status code
4. If 500 error, check `krishi_errors.log` for details

---

### Issue 4: Slow Performance

**Steps:**
1. Open `krishi_database.log`
2. Look for slow queries
3. Open `krishi_main.log` for debug info
4. Check for N+1 query problems

---

## Using Logging in Your Code

### Log Messages from Views

```python
import logging

logger = logging.getLogger('krishi_app')

def my_view(request):
    logger.info(f"User {request.user} accessed product view")
    
    try:
        product = Product.objects.get(id=product_id)
        logger.debug(f"Product found: {product.name}")
    except Product.DoesNotExist:
        logger.error(f"Product {product_id} not found", exc_info=True)
        return HttpResponseNotFound()
    
    return render(request, 'product_detail.html', {'product': product})
```

### Log Database Operations

```python
logger = logging.getLogger('django.db.backends')

def create_order(user, products):
    logger.debug(f"Creating order for user {user} with {len(products)} products")
    order = Order.objects.create(user=user)
    logger.info(f"Order {order.id} created successfully")
```

### Log Errors with Stack Traces

```python
import traceback

try:
    # Some operation
    result = dangerous_operation()
except Exception as e:
    logger.error(f"Operation failed: {str(e)}", exc_info=True)
    # exc_info=True includes full traceback
```

---

## Log Levels Explained

| Level | Use When | Example |
|-------|----------|---------|
| DEBUG | Detailed diagnostic info | Variable values, function calls, DB queries |
| INFO | General info | Application started, user logged in |
| WARNING | Something unexpected | Missing file, deprecated function usage |
| ERROR | Bug or unexpected behavior | Exception caught, validation failed |
| CRITICAL | System failure | Database down, critical error |

---

## Reading Log Files Efficiently

### Using PowerShell to Filter Logs

**View only errors from today:**
```powershell
Get-Content krishi_errors.log | Select-String "ERROR" | Tail -20
```

**View all errors from the last hour:**
```powershell
Get-Content krishi_errors.log | Select-String "$(Get-Date -Format 'HH')"
```

**View specific app logs:**
```powershell
Get-Content krishi_main.log | Select-String "krishi_app"
```

### Using Command Line (Windows)

**View last 50 lines of error log:**
```cmd
type krishi_errors.log | more
```

**Search for specific error:**
```cmd
findstr "DatabaseError" krishi_errors.log
```

---

## Best Practices

1. **Always run `startup_logger.py` first** after project setup
2. **Check `krishi_errors.log` immediately** when something breaks
3. **Use `krishi_database.log`** for database-related issues
4. **Monitor `krishi_requests.log`** for API integration issues
5. **Keep logs backed up** for debugging historical issues
6. **Rotate logs monthly** once they get large

---

## Configuration Reference

### Log Format

```
[LEVEL] YYYY-MM-DD HH:MM:SS | file_path | function_name:line_number | Message
```

**Example:**
```
[ERROR] 2024-01-15 10:32:10 | /krishi/products/views.py:78 | get_product_list() | Product not found
```

### Log Rotation

- Logs automatically rotate when they reach 10MB
- 10 backup files are kept per log
- Old logs are not deleted, just rotated to `.log.1`, `.log.2`, etc.

### Disable Logging (Debug Mode Only)

In `settings.py`, change:
```python
'level': 'DEBUG',  # Change to 'ERROR' to only log errors
```

---

## Troubleshooting Logging Itself

### Logs not appearing?

1. Check `logs/` directory exists
2. Verify file permissions (logs folder writable)
3. Restart Django server
4. Run `startup_logger.py` to test

### Too many log files?

- This is normal - they rotate automatically
- To clean: delete `.log.1`, `.log.2`, etc. (keep `.log`)

---

## Summary

The logging system is now fully operational and will:
✓ Log every startup event  
✓ Track all database connections  
✓ Record every HTTP request/response  
✓ Capture all errors with full context  
✓ Help you debug issues quickly  

**Start here:** Run `python startup_logger.py` and check the output!
