# 📤 GITHUB UPLOAD GUIDE

## Step 1: Create GitHub Repository

1. Go to **https://github.com/new**
2. Repository name: **`free-game-checker`**
3. Description: `Never miss a free game again! Monitors game stores and emails when paid games become free.`
4. **Public** ✅
5. **DO NOT** add README (we have our own)
6. Click **"Create repository"**

---

## Step 2: Upload Main Files (10 files)

1. Click **"Add file"** → **"Upload files"**
2. **Drag these 10 files:**
   - app.py
   - web.py
   - install.sh
   - proxmox-lxc-setup.sh
   - requirements.txt
   - README.md
   - QUICKSTART.md
   - LICENSE
   - .gitignore
   - UPLOAD_GUIDE.md (this file)
3. **Commit changes**

---

## Step 3: Create templates/ Folder

1. Click **"Add file"** → **"Create new file"**
2. File name: **`templates/base.html`**
3. Copy/paste contents of `base.html`
4. Click **"Commit new file"**

5. Repeat for:
   - **`templates/index.html`**
   - **`templates/settings.html`**

---

## ✅ Verify Upload

Your repository should show:

```
free-game-checker/
├── .gitignore
├── LICENSE
├── QUICKSTART.md
├── README.md
├── UPLOAD_GUIDE.md
├── app.py
├── install.sh
├── proxmox-lxc-setup.sh
├── requirements.txt
├── web.py
└── templates/
    ├── base.html
    ├── index.html
    └── settings.html
```

**Total: 10 files + 3 templates = 13 items**

---

## 🚀 Ready to Install!

Once uploaded, anyone (including you) can install with:

```bash
# On Proxmox host:
rm -f proxmox-lxc-setup.sh*
wget https://raw.githubusercontent.com/MatDaBoss/free-game-checker/main/proxmox-lxc-setup.sh
chmod +x proxmox-lxc-setup.sh
./proxmox-lxc-setup.sh
```

---

## 🌐 Repository URL

```
https://github.com/MatDaBoss/free-game-checker
```

---

## 💡 Tips

- **Make sure repository is PUBLIC** - required for wget to work
- **Don't add GitHub's default README** - we have our own
- **Upload templates individually** - file-by-file in templates/ folder
- **.gitignore file** - Create directly on GitHub if upload skips it

---

## 🎉 What Users Get

After running the install script:
- ✅ Auto-detected container ID
- ✅ Complete installation
- ✅ Web interface running
- ✅ Ready to use immediately - NO coding required!
- ✅ Just open URL and browse games

---

**Upload complete? Test the installation on your Proxmox!** 🚀
