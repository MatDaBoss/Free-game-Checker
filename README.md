# 🎮 Free Game Checker

**Never miss a free game again!** Automatically monitors game stores and emails you when paid games become free.

---

## ✨ Features

### 🖥️ Multi-Platform Support
- **PC** - Epic Games, Steam, GOG, Humble Bundle, Itch.io
- **Xbox** - Xbox Store (Games with Gold)
- **Nintendo Switch** - Nintendo eShop promotions
- **Android** - Google Play Games

### 🎯 Smart Filtering
- ✅ Only games that **were paid** and are **now FREE**
- ❌ NO free-to-play games (always been free)
- ❌ NO demos or trials  
- ❌ NO subscription-required games

### 📧 Beautiful Email Notifications
- Platform icons (🖥️ PC / 🎮 Xbox / 🕹️ Switch / 📱 Android)
- Game cover images
- "Was $X.XX → FREE" pricing
- Expiry dates
- Direct "Claim Now" links

### 🌐 Web Dashboard
- View all current free games
- Platform badges and icons
- One-click game checking
- Test email sending
- Easy configuration

---

## 🚀 Quick Start (Proxmox LXC)

### Automated Installation (5 minutes)

```bash
# On your Proxmox host:

# Step 1: Clean old files
rm -f proxmox-lxc-setup.sh*

# Step 2: Download latest
wget https://raw.githubusercontent.com/MatDaBoss/free-game-checker/main/proxmox-lxc-setup.sh

# Step 3: Run
chmod +x proxmox-lxc-setup.sh
./proxmox-lxc-setup.sh
```

**The script will:**
- ✅ Auto-detect next available container ID
- ✅ Create Ubuntu 22.04 LXC container
- ✅ Download and install Free Game Checker from GitHub
- ✅ Start web interface automatically
- ✅ Display access URL

**Output:**
```
🌐 Access Free Game Checker:
   http://192.168.1.50:5000

💡 The web interface is ready to use NOW!
   Browse games without any configuration!
```

---

## 🌐 Using Free Game Checker

### Immediate Access (No Setup Required!)

1. **Open the URL** shown after installation
2. **Browse current free games** right away!
3. **No configuration needed** to view games

### Optional: Configure Email Notifications

When you're ready to receive emails:

1. **Click "Settings"**
2. **Enter Gmail app password:** `zgqw lvns lpex qscv`
3. **Add email recipients**
4. **Click "Send Test Email"**
5. **Enable automatic checking:**
   ```bash
   pct exec CONTAINER_ID -- systemctl start free-game-checker
   ```

---

## 🎯 Monitored Stores

| Platform | Store | Status | Notes |
|----------|-------|--------|-------|
| 🖥️ PC | Epic Games Store | ✅ Excellent | Weekly free games |
| 🖥️ PC | Steam | ✅ Good | Free promotions & weekends |
| 🖥️ PC | GOG | ⚠️ Rare | Occasional freebies |
| 🖥️ PC | Humble Bundle | ⚠️ Rare | Special promotions |
| 🖥️ PC | Itch.io | ✅ Good | Free indie games |
| 🎮 Xbox | Xbox Store | ✅ Good | Games with Gold |
| 🕹️ Switch | Nintendo eShop | ⚠️ Rare | Special promotions |
| 📱 Android | Google Play | ⚠️ Rare | Occasional deals |

---

## 📋 Requirements

- **Hardware**: 1 CPU core, 512MB RAM, 8GB disk
- **OS**: Proxmox (any version with LXC support)
- **Network**: Internet access
- **Email** (optional): Gmail account with app password

---

## 🔧 Gmail App Password Setup

Only needed for email notifications:

1. Go to Google Account → Security
2. Enable 2-Factor Authentication
3. Search for "App Passwords"
4. Create password for "Mail"
5. Copy the 16-character password
6. Paste into web interface settings

---

## 📊 Default Schedule

- **Day**: Friday
- **Time**: 09:00 AM
- **Email**: Sent if games found

---

## 🛠️ Useful Commands

```bash
# View web service status
systemctl status free-game-checker-web

# View scheduler status  
systemctl status free-game-checker

# Check logs
tail -f /var/log/free-game-checker.log

# Manual game check
python3 /opt/free-game-checker/app.py check-now

# Restart services
systemctl restart free-game-checker
systemctl restart free-game-checker-web

# Enter container (from Proxmox host)
pct enter CONTAINER_ID
```

---

## 🎨 Platform Display Order

Games are always sorted:
1. 🖥️ **PC games** (alphabetically by store)
2. 🎮 **Xbox games**
3. 🕹️ **Nintendo Switch games**
4. 📱 **Android games**

---

## 📁 File Structure

```
/opt/free-game-checker/          # Application
  ├── app.py                      # Main scraper & emailer
  ├── web.py                      # Flask web interface
  ├── templates/                  # HTML templates
  └── requirements.txt            # Dependencies

/etc/free-game-checker/          # Configuration
  └── config.json                # Settings

/var/lib/free-game-checker/      # Data
  └── games.db                   # Database

/var/log/                        # Logs
  └── free-game-checker.log      # App logs
```

---

## 🆘 Troubleshooting

### Web Interface Not Accessible
```bash
systemctl status free-game-checker-web
systemctl restart free-game-checker-web
```

### No Games Showing
- Click "Check for Games Now"
- Wait 1-2 minutes
- Refresh page

### Email Not Sending
- Verify Gmail app password
- Check spam folder
- View logs for errors

### Update to Latest Version
```bash
# Clean old setup files
rm -f proxmox-lxc-setup.sh*

# Download latest
wget https://raw.githubusercontent.com/MatDaBoss/free-game-checker/main/proxmox-lxc-setup.sh

# Create fresh container or update existing one
```

---

## 🔄 Updates

### Update Application
```bash
cd /opt/free-game-checker
git pull
systemctl restart free-game-checker
systemctl restart free-game-checker-web
```

### Fresh Database
```bash
rm /var/lib/free-game-checker/games.db
systemctl restart free-game-checker-web
```

---

## 📜 License

MIT License - Free to use and modify

---

## 🙏 Credits

Created with ❤️ for gamers who love free games!

Repository: https://github.com/MatDaBoss/free-game-checker

---

**Enjoy your free games!** 🎮🎉
