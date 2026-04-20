# 🌾 Krishi Project - Complete Logging System

## What You Have

A comprehensive logging and monitoring system that tracks **EVERYTHING** happening in your Krishi Django project:

- ✅ Project startup and initialization
- ✅ Database connections and all queries
- ✅ HTTP requests and responses
- ✅ ALL errors with full details and causes
- ✅ Real-time monitoring while server runs
- ✅ Automatically rotated log files

---

## 📂 Files Included

### 1. **Main Configuration**
- `krishi/settings.py` - Updated with comprehensive logging configuration
- `krishi/middleware.py` - Request/response logging middleware

### 2. **Executable Scripts**

| File | Purpose | How to Run |
|------|---------|-----------|
| `startup_logger.py` | Check startup, DB connection, system info | `python startup_logger.py` |
| `log_monitor.py` | Real-time log monitoring while server runs | `python log_monitor.py -m all` |
| `RUN_STARTUP_CHECK.bat` | Windows batch file (click to run) | Double-click the file |
| `RUN_STARTUP_CHECK.ps1` | PowerShell version | `powershell -ExecutionPolicy Bypass -File RUN_STARTUP_CHECK.ps1` |

### 3. **Documentation**
- `LOGGING_GUIDE.md` - **Detailed guide** with examples
- `LOGGING_QUICK_REFERENCE.md` - **Quick lookup** for common issues
- `README.md` - This file

### 4. **Log Output Files** (Created in `logs/` folder)
```
logs/
├── krishi_main.log          (All events)
├── krishi_errors.log        (Errors only)
├── krishi_database.log      (Database operations)
├── krishi_requests.log      (HTTP requests)
└── krishi_startup.log       (Startup info)
```

---

## 🚀 Getting Started (3 Simple Steps)

### Step 1️⃣ Run Startup Check

```bash
cd krishi_Connect\krishicon\krishi
python startup_logger.py
```

**Output shows:**
```
✓ Python version, Platform, Django setup
✓ Database configuration and connection test
✓ All installed apps
✓ Migrations status
✓ File structure check
✓ Location of all log files
```

**What to look for:**
- ✓ marks = All good
- ✗ marks = Fix this before continuing

### Step 2️⃣ Start Your Server

```bash
python manage.py runserver
```

### Step 3️⃣ Monitor Logs (Optional)

In a **new terminal/PowerShell**:

```bash
# Monitor only errors
python log_monitor.py -m errors

# Monitor all logs
python log_monitor.py -m all

# Show summary
python log_monitor.py --summary
```

---

## 🔍 When Something Goes Wrong

### Problem: Application Error / Server Crash

**Solution:**
1. Look at: `logs/krishi_errors.log` ⭐
2. Find the **MOST RECENT [ERROR]** entry
3. Note the **file path, line number, and error message**
4. Fix your code and restart server

**Example error log entry:**
```
[ERROR] 2024-01-15 10:32:10 | /krishi/products/views.py:78 | get_product()
TypeError: 'NoneType' object is not subscriptable

File "/krishi/products/views.py", line 78, in get_product
    name = product['name']  ← This is the problem!
TypeError: 'NoneType' object is not subscriptable
```

**Fix:** Add a None check before accessing the dictionary

---

### Problem: Database Connection Fails

**Solution:**
1. Run: `python startup_logger.py`
2. Look for database connection error
3. Check error message for specific help

**Common issues:**
```
✗ Can't connect to MySQL server → Start XAMPP, enable MySQL
✗ Unknown database 'krishi_db' → Create database in phpMyAdmin
✗ Access denied for user 'root' → Check credentials in settings.py
```

---

### Problem: Page Shows 404 Not Found

**Solution:**
1. Check: `logs/krishi_requests.log`
2. Find: `[RESPONSE] 'status_code': 404`
3. Fix: Add route to `urls.py`

---

### Problem: Form Not Submitting

**Solution:**
1. Check: `logs/krishi_requests.log` for POST request
2. If status 500, check: `logs/krishi_errors.log`
3. Look for form validation or processing error

---

### Problem: Data Not Saving to Database

**Solution:**
1. Check: `logs/krishi_database.log` for INSERT queries
2. If no INSERT, check: `logs/krishi_main.log` for logic errors
3. If INSERT but data missing, check model constraints and required fields

---

## 📊 Understanding the Log Files

### 🔴 `krishi_errors.log` (Most Important!)

**Contains:** Only ERROR and CRITICAL level entries with full traceback

**When to use:** Something broke - start here!

**Info provided:**
- Exact file path and line number
- Function name
- Error type and message
- Full Python traceback
- Timestamp

**Example:**
```
[ERROR] 2024-01-15 10:32:10 | /krishi/products/views.py:78 | get_product()
Product not found: Product matching query does not exist.

Traceback (most recent call last):
  File "/krishi/products/views.py", line 78, in get_product
    product = Product.objects.get(id=product_id)
  File "/django/db/models/query.py", line 390, in get
    raise self.model.DoesNotExist(...)
Product.DoesNotExist: Product matching query does not exist.
```

---

### 🟡 `krishi_startup.log`

**Contains:** System info, Django setup, database connection test results

**When to use:** Server won't start, database connection issues

**Info provided:**
- Python version, platform
- Django version
- Database engine and credentials
- MySQL version
- Migrations status
- File structure check

**Example:**
```
[INFO] Python Version: 3.11.2
[INFO] Platform: win32
[INFO] Django Version: (5, 2, 0, 'final', 0)
[INFO] Database Engine: django.db.backends.mysql
[INFO] ✓ Database Connection: SUCCESS
[INFO] MySQL Version: 8.0.36
[INFO] ✓ All migrations applied
```

---

### 🔵 `krishi_database.log`

**Contains:** Database connection, queries, operations

**When to use:** Database-related issues, checking what SQL is running

**Info provided:**
- Connection attempts and status
- SQL queries being executed
- Query results
- Database operations (INSERT, UPDATE, DELETE, SELECT)

**Example:**
```
[DEBUG] Creating database connection
[DEBUG] SELECT VERSION();
[DEBUG] SELECT * FROM krishi_app_userprofile WHERE id = 5
[DEBUG] INSERT INTO krishi_app_vegetable (name, price) VALUES ('Tomato', 50.00)
[DEBUG] Connection closed
```

---

### 🟢 `krishi_requests.log`

**Contains:** HTTP requests and responses

**When to use:** Tracking user actions, API integration issues

**Info provided:**
- HTTP method (GET, POST, etc.)
- URL path
- Query parameters and POST data
- Status code (200, 404, 500, etc.)
- Client IP and user info
- User agent

**Example:**
```
[REQUEST] {'method': 'POST', 'path': '/cart/add/', 'post_data': {'product_id': 5}}
[RESPONSE] {'method': 'POST', 'path': '/cart/add/', 'status_code': 200}

[REQUEST] {'method': 'GET', 'path': '/products/xyz', 'user': 'john_doe'}
[RESPONSE] {'status_code': 404}  ← Product not found!
```

---

### ⚪ `krishi_main.log`

**Contains:** ALL events from DEBUG level and above

**When to use:** General troubleshooting, understanding application flow

**Info provided:** Everything from other logs combined

---

## 💻 Command Reference

### View Logs

**View last 50 lines of error log:**
```powershell
Get-Content .\logs\krishi_errors.log -Tail 50
```

**Search for specific error:**
```powershell
Select-String "DatabaseError" .\logs\krishi_errors.log
```

**Find all 500 errors in requests log:**
```powershell
Select-String "500" .\logs\krishi_requests.log
```

**Monitor errors in real-time:**
```bash
python log_monitor.py -m errors
```

**Get summary of all logs:**
```bash
python log_monitor.py --summary
```

---

## 📋 Log Levels Quick Reference

```python
logger.debug("Variable x = 5")           # Detailed info (debugging)
logger.info("User logged in")            # General information
logger.warning("Cache miss, using DB")   # Unexpected but handled
logger.error("Database query failed")     # Something went wrong
logger.critical("Out of memory!")         # System failure
```

**What gets logged where:**
- DEBUG, INFO, WARNING, ERROR → All logs
- ERROR only → `krishi_errors.log`
- Database operations → `krishi_database.log`
- HTTP requests → `krishi_requests.log`

---

## 🛠️ Logging in Your Code

### Add logging to views.py

```python
import logging

logger = logging.getLogger('krishi_app')

def my_view(request):
    logger.info(f"User {request.user} accessed product view")
    
    try:
        product = Product.objects.get(id=product_id)
        logger.debug(f"Product found: {product.name}")
    except Product.DoesNotExist as e:
        logger.error(f"Product {product_id} not found: {str(e)}", exc_info=True)
        return HttpResponseNotFound()
    
    return render(request, 'product_detail.html', {'product': product})
```

### Add logging to models

```python
logger = logging.getLogger('krishi_app')

class Product(models.Model):
    def save(self, *args, **kwargs):
        logger.info(f"Saving product: {self.name}")
        super().save(*args, **kwargs)
        logger.debug(f"Product {self.id} saved successfully")
```

---

## ✅ Troubleshooting Checklist

When something goes wrong:

- [ ] Run `python startup_logger.py` - shows connection status
- [ ] Open `logs/krishi_errors.log` - read the most recent ERROR
- [ ] Note file, line number, and error type
- [ ] Search the traceback for YOUR code
- [ ] Fix the issue in your code
- [ ] Restart server: `python manage.py runserver`
- [ ] Test again and check logs for success

---

## 📈 Log File Size Management

Each log file automatically rotates:
- **Max size**: 10MB (5MB for startup)
- **Backups kept**: 10 files
- **Format**: When full, rotates to `.log.1`, `.log.2`, etc.
- **Auto cleanup**: Old backups automatically removed

---

## 🎯 Quick Reference by Scenario

### "My app crashed"
→ Check `krishi_errors.log` or run `python startup_logger.py`

### "Database won't connect"
→ Run `python startup_logger.py` and check database section

### "Form didn't submit"
→ Check `krishi_requests.log` for POST, then `krishi_errors.log`

### "404 error on page"
→ Check `krishi_requests.log` for status 404

### "Can't find what went wrong"
→ Run `python log_monitor.py --summary` for overview

---

## 📞 Need Help?

1. **Quick answers:** See `LOGGING_QUICK_REFERENCE.md`
2. **Detailed guide:** See `LOGGING_GUIDE.md`
3. **Specific log info:** Check the relevant log file
4. **Real-time monitoring:** Use `python log_monitor.py -m all`

---

## 🎓 Example: Debugging a Real Issue

**Scenario:** User says "I can't add products to cart"

**Investigation:**
```bash
# Step 1: Check requests
python log_monitor.py -m requests
# Found: POST /cart/add/ → Response 500

# Step 2: Check errors
Get-Content .\logs\krishi_errors.log -Tail 20
# Found error: "TypeError: 'NoneType' object is not subscriptable"
# At: /krishi/products/views.py:45

# Step 3: Look at the code
# Line 45: product_data = request.POST['product_id']
# Problem: POST data is None, not checking

# Step 4: Fix it
# Add: if 'product_id' not in request.POST: return error

# Step 5: Restart and verify
python manage.py runserver
# Test again - Success!
```

---

## 📝 Summary

**You now have:**
- ✅ Comprehensive logging for Django project
- ✅ Real-time monitoring while server runs
- ✅ Detailed error messages with exact locations
- ✅ Database connection tracking
- ✅ HTTP request/response logging
- ✅ Automatic log rotation
- ✅ Easy-to-use monitoring tools

**To start:**
1. Run: `python startup_logger.py`
2. Look for any ✗ symbols - fix them
3. Start server: `python manage.py runserver`
4. Monitor: `python log_monitor.py -m all` (in another terminal)

---

**Ready to debug like a pro! 🚀**

For more details, read:
- [Detailed Logging Guide](LOGGING_GUIDE.md)
- [Quick Reference](LOGGING_QUICK_REFERENCE.md)
