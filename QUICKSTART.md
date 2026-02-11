# 🚀 QUICK START - 5 Minutes to Free Games!

## Step 1: Run On Proxmox (3 minutes)

```bash
# SSH into your Proxmox host
ssh root@YOUR_PROXMOX_IP

# Clean old files (IMPORTANT!)
rm -f proxmox-lxc-setup.sh*

# Download setup script
wget https://raw.githubusercontent.com/MatDaBoss/free-game-checker/main/proxmox-lxc-setup.sh

# Make executable and run
chmod +x proxmox-lxc-setup.sh
./proxmox-lxc-setup.sh

# Press 'y' when prompted
```

**Script automatically:**
- Finds next free container ID
- Creates LXC container
- Downloads Free Game Checker from GitHub
- Installs everything
- Starts web interface

**Output shows:**
```
🌐 Access Free Game Checker:
   http://192.168.1.50:5000
```

---

## Step 2: Start Using It! (Immediate)

1. **Open the URL** in your browser
2. **Browse free games** - works instantly!
3. **No setup required** to view games

---

## Step 3: Configure Email (Optional - 2 minutes)

Only when you want email notifications:

1. Click **"Settings"**
2. Enter Gmail app password: `zgqw lvns lpex qscv`
3. Click **"Save Email Configuration"**
4. Scroll down, add your email
5. Click **"Send Test Email"**
6. Enable automatic checks:
   ```bash
   pct exec CONTAINER_ID -- systemctl start free-game-checker
   ```

---

## ✅ Done!

**You can now:**
- 🎮 Browse current free games anytime
- 📧 Receive weekly email updates (if configured)
- 🖥️ See PC, Xbox, Switch, and Android games
- 🎯 Only see games that were paid → now FREE

---

## 🔧 Quick Commands

```bash
# View logs
tail -f /var/log/free-game-checker.log

# Restart web interface
systemctl restart free-game-checker-web

# Enter container
pct enter CONTAINER_ID

# Manual game check
python3 /opt/free-game-checker/app.py check-now
```

---

## 🆘 Problems?

**Can't access web interface?**
```bash
systemctl status free-game-checker-web
systemctl restart free-game-checker-web
```

**No games showing?**
- Click "Check for Games Now"
- Wait 1-2 minutes
- Refresh page

**Want to update?**
```bash
rm -f proxmox-lxc-setup.sh*
wget https://raw.githubusercontent.com/MatDaBoss/free-game-checker/main/proxmox-lxc-setup.sh
# Run setup again
```

---

## 💡 Pro Tips

- **No coding required** - everything is automatic
- **Web interface is instant** - browse games immediately
- **Email is optional** - configure only when ready
- **Updates are easy** - just re-run the setup script

---

**That's it! Enjoy your free games!** 🎮🎉

Repository: https://github.com/MatDaBoss/free-game-checker
