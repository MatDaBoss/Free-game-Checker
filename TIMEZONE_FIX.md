# ⏰ TIMEZONE FIX - Email Scheduling Issue

## 🔍 THE PROBLEM:

**You didn't get an email Friday 9:00 AM Brisbane time.**

This is because the container is likely running on **UTC time** (Coordinated Universal Time), not Brisbane time.

---

## 🌏 TIMEZONE INFO:

**Your Location:** Brisbane, Queensland, Australia
**Your Timezone:** AEST (Australian Eastern Standard Time)
**UTC Offset:** UTC+10 (no daylight saving in Queensland)

**Time Conversion:**
- 9:00 AM Brisbane = 11:00 PM previous day UTC
- 9:00 AM UTC = 7:00 PM Brisbane

---

## ✅ IMMEDIATE FIX (For Existing Container):

### Step 1: Check Current Container Time
```bash
pct enter CONTAINER_ID
date
timedatectl
```

**If it shows UTC**, that's the problem!

### Step 2: Set Timezone to Brisbane
```bash
# Still inside container
timedatectl set-timezone Australia/Brisbane

# Verify it worked
date
# Should now show AEST time

# Restart scheduler service
systemctl restart free-game-checker

# Exit container
exit
```

### Step 3: Verify Schedule
```bash
# Check logs to see when next run is scheduled
pct exec CONTAINER_ID -- tail -20 /var/log/free-game-checker.log
```

---

## ✅ FUTURE FIX (New Installations):

I've updated `proxmox-lxc-setup.sh` to automatically set Brisbane timezone during installation.

**Updated Script Now:**
1. Installs `tzdata` package
2. Sets timezone to `Australia/Brisbane`
3. No manual configuration needed!

---

## 🔍 TROUBLESHOOTING:

### Check If Scheduler Is Running:
```bash
pct exec CONTAINER_ID -- systemctl status free-game-checker
```

**Should show:** `active (running)`

### Check Schedule Configuration:
```bash
pct exec CONTAINER_ID -- cat /etc/free-game-checker/config.json
```

**Should show:**
```json
{
    "schedule_day": "friday",
    "schedule_time": "09:00",
    ...
}
```

### View Scheduler Logs:
```bash
pct exec CONTAINER_ID -- journalctl -u free-game-checker -f
```

**Should show:** "Scheduled to run every Friday at 09:00"

### Manual Test Email:
```bash
# Enter container
pct enter CONTAINER_ID

# Run check manually
cd /opt/free-game-checker
source venv/bin/activate
python3 app.py check-now

# Exit
exit
```

---

## 📅 SCHEDULE EXAMPLES:

### Current Setting (Default):
- **Day:** Friday
- **Time:** 09:00 AM
- **Timezone:** Brisbane (after fix)

### To Change Schedule:
1. Go to web interface
2. Click **Settings**
3. Scroll to **Schedule Configuration**
4. Change day/time
5. Click **Save**
6. Restart scheduler: `systemctl restart free-game-checker`

---

## 🎯 WHAT HAPPENS AFTER FIX:

**Before Fix:**
```
Container time: UTC
Schedule: Friday 9:00 AM
Actual run: Friday 9:00 AM UTC = Friday 7:00 PM Brisbane ❌
```

**After Fix:**
```
Container time: AEST (Brisbane)
Schedule: Friday 9:00 AM
Actual run: Friday 9:00 AM Brisbane ✅
```

---

## 💡 WHY THIS HAPPENED:

1. Linux containers default to **UTC timezone**
2. Python's `schedule` library uses **system time**
3. No timezone was set during installation
4. Schedule ran at "9 AM" but in UTC, not Brisbane

---

## ✅ COMPLETE FIX PROCEDURE:

```bash
# 1. Check current time
pct enter CONTAINER_ID
date

# 2. Set Brisbane timezone
timedatectl set-timezone Australia/Brisbane

# 3. Verify
date
# Should show: Fri Feb 14 09:00:00 AEST 2026

# 4. Restart scheduler
systemctl restart free-game-checker

# 5. Check it's running
systemctl status free-game-checker

# 6. Check logs
tail -20 /var/log/free-game-checker.log

# 7. Exit
exit
```

---

## 📧 TEST IT NOW:

**Option 1: Wait Until Next Friday 9 AM**

**Option 2: Change Schedule to Test Now**
1. Web interface → Settings
2. Change time to current time + 2 minutes
3. Save
4. Restart scheduler: `systemctl restart free-game-checker`
5. Wait 2 minutes
6. Check email!
7. Change back to 09:00

**Option 3: Manual Test**
```bash
pct exec CONTAINER_ID -- bash -c "cd /opt/free-game-checker && source venv/bin/activate && python3 app.py check-now"
```

---

## 🔔 REMEMBER:

After setting timezone:
- ✅ Scheduler will use Brisbane time
- ✅ Logs will show Brisbane time
- ✅ Emails will arrive at correct time

---

**Run the fix commands above to set Brisbane timezone!** ⏰
