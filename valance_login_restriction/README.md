# login_restriction — Odoo 19 Custom Module

## Purpose
Enforces server-side login time restrictions for specific users in IST (Asia/Kolkata, UTC+5:30).

| User   | Restriction                         |
|--------|-------------------------------------|
| Jigar  | **None** — can log in at any time   |
| Yash   | Blocked 8:00 PM → 10:00 AM IST      |
| Amit   | Blocked 8:00 PM → 10:00 AM IST      |
| Rahul  | Blocked 8:00 PM → 10:00 AM IST      |
| Venu   | Blocked 8:00 PM → 10:00 AM IST      |

---

## Installation

1. Copy the `login_restriction/` folder into your Odoo **addons path**.
2. Restart the Odoo service.
3. Enable **Developer Mode** (Settings → Activate the developer mode).
4. Go to **Settings → Apps**, click **Update App List**.
5. Search for **"User Login Time Restriction"** and click **Install**.

> **Dependency:** `pytz` must be available in your Python environment.
> It ships with every standard Odoo installation.

---

## How It Works

### Authentication override
The module inherits `res.users` and overrides **two** class-methods:

| Method          | Used by                                      |
|-----------------|----------------------------------------------|
| `_login()`      | Web client, mobile app (Odoo native calls)   |
| `authenticate()`| XML-RPC / JSON-RPC external API clients      |

Both methods call `super()` first (so Odoo validates credentials normally), then check the time window **only** if the login matches a restricted user.  
This means:
- Wrong passwords still return the standard "wrong credentials" error.
- Time-blocked logins get: **"Login not allowed during restricted hours (8 PM to 10 AM IST)"**

### Time window logic (`_is_restricted_hour`)
```
IST hour >= 20  →  blocked  (8 PM onward)
IST hour <  10  →  blocked  (until 10 AM)
10 <= hour < 20 →  allowed
```

### Restricted login set
Defined as a module-level `frozenset` (`RESTRICTED_LOGINS`) holding lowercase login names.  
Comparison is case-insensitive.

---

## Customisation

### Change the restricted users
Edit `models/res_users.py`:
```python
RESTRICTED_LOGINS = {'yash', 'amit', 'rahul', 'venu'}
```

### Change the time window
```python
RESTRICT_START_HOUR = 20   # 8 PM IST
RESTRICT_END_HOUR   = 10   # 10 AM IST
```

### Change the timezone
```python
IST = pytz.timezone('Asia/Kolkata')   # replace with any tz string
```

---

## Compatibility
- **Odoo:** 19.0  
- **Python:** 3.10+  
- **pytz:** any version (ships with Odoo)
