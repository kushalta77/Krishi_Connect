# Krishi Project - Logging Quick Reference

## ⚡ Quick Start (3 Steps)

### Step 1: Run Startup Check
```bash
cd krishi_Connect\krishicon\krishi
python startup_logger.py
```
**Result:** Shows system info, database status, and any connection errors

### Step 2: Check the Errors
If something is broken, open these in order:
1. `logs/krishi_errors.log` ← **START HERE**
2. `logs/krishi_startup.log` ← If startup fails
3. `logs/krishi_database.log` ← If database issues

### Step 3: Start Server
```bash
python manage.py runserver
```

---

## 📁 Log Files at a Glance

| Log File | Purpose | When to Use |
|----------|---------|------------|
| `krishi_errors.log` | **ERRORS ONLY** | Something crashed/broken |
| `krishi_startup.log` | Startup debug | First run or server won't start |
| `krishi_database.log` | Database debug | DB connection issues |
| `krishi_requests.log` | API/Web requests | Track user requests |
| `krishi_main.log` | Everything | General troubleshooting |

---

## 🔍 Finding Your Error

### Error Type 1: "Can't Connect to Database"
**File:** `krishi_startup.log` or run `startup_logger.py`
**Look for:**
```
✗ Database Connection: FAILED
Error Details: OperationalError: (2003, "Can't connect to MySQL server")
HELP: XAMPP MySQL not running. Start XAMPP...
```
**Fix:** Start XAMPP, ensure MySQL is running

---

### Error Type 2: "Page Shows Error 500"
**File:** `krishi_errors.log`
**Look for:**
```
[ERROR] 2024-01-15 10:32:10 | /krishi/products/views.py:78 | get_product()
Exception: [ACTUAL ERROR HERE]
```
**Action:** Read the exception message, fix your code

---

### Error Type 3: "Form Submission Failed"
**Files:** `krishi_requests.log` → `krishi_errors.log`
**Look for:**
1. In requests log: `[RESPONSE] ... 'status_code': 500`
2. In errors log: Find what caused the 500 error

---

### Error Type 4: "Database Looks Wrong"
**File:** `krishi_database.log`
**Look for:** SQL queries to see what's happening
```
[DEBUG] ... INSERT INTO krishi_app_vegetable (name, price) VALUES (...)
[DEBUG] ... SELECT * FROM krishi_app_orders WHERE user_id = 5
```

---

## 📋 What Each Log Shows

### `krishi_errors.log` (Most Important!)
```
[ERROR] 2024-01-15 10:32:10 | /path/to/file.py:78 | function_name()
actual error message
Exception Type: NameError
Traceback: [full Python traceback]
```
✓ File path and line number  
✓ Function name  
✓ Error type  
✓ Full traceback  

---

### `krishi_startup.log`
```
Python Version: 3.11.2
Platform: win32
Django Version: (5, 2, 0, 'final', 0)
DEBUG Mode: True
Database Engine: django.db.backends.mysql
✓ Database Connection: SUCCESS
✓ All migrations applied
Startup completed at: 2024-01-15 10:30:45
```

---

### `krishi_database.log`
```
[DEBUG] Testing connection to MySQL
[DEBUG] SELECT VERSION();
Result: MySQL 8.0.36
[DEBUG] SELECT * FROM krishi_app_userprofile LIMIT 1
[DEBUG] UPDATE krishi_app_cart SET total=500 WHERE id=3
```

---

### `krishi_requests.log`
```
[REQUEST] {
  'method': 'GET',
  'path': '/products/',
  'user': 'john_doe',
  'status_code': 200
}

[REQUEST] {
  'method': 'POST',
  'path': '/cart/add/',
  'post_data': {'product_id': 5, 'quantity': 2}
}
```

---

## 🎯 Common Scenarios

### Scenario A: Server Won't Start
```
Action: Run startup_logger.py
├─ Shows: system info, DB connection status
└─ Look for: ✗ symbols indicating failures
```

### Scenario B: Page Shows 404 Error
```
Action: Check krishi_requests.log
├─ Find: [RESPONSE] with status_code: 404
└─ Check: /projectname/urls.py for route
```

### Scenario C: Page Shows 500 Error
```
Action: Open krishi_errors.log (MOST RECENT ENTRY)
├─ Shows: exact file, line, function, error
├─ Shows: full traceback
└─ Fix: address the error in your code
```

### Scenario D: Form Not Submitting
```
Action 1: Check krishi_requests.log for the POST
Action 2: If status 500, check krishi_errors.log
Action 3: Look for form validation errors
```

### Scenario E: Data Not Saving
```
Action 1: Check krishi_database.log for INSERT queries
Action 2: Check krishi_errors.log for database errors
Action 3: Verify model constraints, required fields
```

---

## 🔧 Useful Commands

### View Last Error
**PowerShell:**
```powershell
Get-Content krishi_errors.log -Tail 50  # Last 50 lines
```

### Find Specific Error
**PowerShell:**
```powershell
Select-String "404" krishi_requests.log  # Find 404 errors
Select-String "DatabaseError" krishi_errors.log
```

### Monitor Log in Real-Time (PowerShell)
```powershell
Get-Content krishi_errors.log -Wait -Tail 20
```

### Find Errors from Last Hour
```powershell
$hour = (Get-Date).Hour.ToString("D2")
Select-String $hour krishi_errors.log
```

---

## ✅ Checklist When Something's Wrong

- [ ] Run `startup_logger.py` and note any ✗ marks
- [ ] Open `krishi_errors.log` and read the most recent ERROR
- [ ] Look at the file path and line number shown
- [ ] Read the exception message carefully
- [ ] Check the traceback to understand what happened
- [ ] Fix your code based on the error
- [ ] Restart server: `python manage.py runserver`

---

## 📊 Log Levels Explained

```
DEBUG  - Detailed info, variable values, function calls
INFO   - General information, user actions
WARNING - Unexpected but handled situations  
ERROR  - Something went wrong (but app still running)
CRITICAL - System failure (app might crash)
```

**In your code:**
```python
logger.debug("x = 5")          # Detailed debug info
logger.info("User logged in")  # General info
logger.warning("Cache miss")   # Unexpected but OK
logger.error("DB query failed") # ERROR - something broke!
logger.critical("Out of memory") # CRITICAL - system fail!
```

---

## 🎓 Example: Actual Error Investigation

### User Reports: "Can't add product to cart"

**Step 1:** Check requests log
```powershell
Select-String "cart/add" krishi_requests.log
# Found: [RESPONSE] {'status_code': 500}
```

**Step 2:** Check errors log
```
[ERROR] 2024-01-15 10:35:20 | /products/views.py:45 | add_to_cart()
TypeError: 'NoneType' object is not subscriptable
```

**Step 3:** Fix code
- Go to `/products/views.py` line 45
- Something is None that shouldn't be
- Add checking before accessing it

**Step 4:** Restart and verify
```bash
python manage.py runserver
# Try same action again
# Check logs for success
```

---

## 🚀 Summary

**Remember:**
- 🟥 **Broken?** → Check `krishi_errors.log` first
- 🟡 **Starting?** → Run `startup_logger.py`
- 🟢 **All good?** → Check `krishi_main.log` periodically

**File locations:**
```
krishi/
└── logs/
    ├── krishi_errors.log ⭐ (Start here)
    ├── krishi_startup.log
    ├── krishi_database.log
    ├── krishi_requests.log
    └── krishi_main.log
```

**Most used command:**
```bash
python startup_logger.py
```

---

**Need more details?** Read `LOGGING_GUIDE.md` in the same directory
