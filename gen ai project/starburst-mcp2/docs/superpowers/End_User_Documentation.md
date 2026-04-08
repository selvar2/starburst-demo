# Simple Guide: Starburst MCP Server Setup
## What We Did Today — April 8, 2026
### A plain-English walkthrough of today's coding session

---

## What This Does

Think of the **Starburst MCP Server** as a smart assistant that talks to a big cloud database (Starburst Galaxy) on your behalf. When you ask Claude a question about your data, this server goes and fetches the answer from the database.

Today, we fixed three things:

1. **Made it work everywhere** — not just on one specific Windows computer
2. **Made it set itself up automatically** — no manual steps needed
3. **Stopped an annoying popup** — a login screen was appearing every single time you asked a question

---

## What You Need

- A **GitHub Codespaces** account (or a computer with Python installed)
- Access to the `starburst-demo` repository
- Your Starburst Galaxy login credentials (already saved in a private file)

---

## Step-by-Step: What Happened Today

### 1. We Made the Server Work on Any Computer

**Before:** The server only worked on one specific Windows laptop. It was like writing directions that say "turn left at John's blue house" — useless if you're in a different city.

**After:** The server now works on any computer — Windows, Mac, Linux, or GitHub Codespaces. It's like writing directions that say "turn left at the first traffic light" — works everywhere.

---

### 2. We Made Everything Start Automatically

When you open the project in GitHub Codespaces, two things now happen automatically:

**First time setup (happens once):**
- Installs all the software the server needs
- Checks that everything installed correctly
- Verifies the server can start up

**Every time you open the project:**
- Checks what kind of computer you're on
- Makes sure all software is still working
- Tests the connection to the database
- Shows you a summary of what's connected

You don't need to do anything — it all happens by itself.

---

### 3. We Fixed the Annoying Login Popup

**The problem:**
Every time you asked Claude to look at your data, a popup appeared in the browser:

> "Third party application access — A third party application would like to access your Galaxy account..."

You had to click "Continue" every single time. During a demo with clients, this looked unprofessional and slowed everything down.

**What was happening:**
The server was trying to log in using a method that requires you to click a button in your browser — every single time, for every single question.

**The fix:**
We switched to a different login method that uses a saved username and password. Now the server logs in silently in the background. No popups. No clicking. No interruptions.

---

### 4. We Tested Everything

We ran a full test to make sure the server can:

| What We Tested | Did It Work? |
|----------------|-------------|
| See all databases | Yes — found 7 |
| See all folders in a database | Yes — found 3 |
| See all tables | Yes — found the "demo" table |
| See what columns a table has | Yes — id, name, amount |
| Read data from a table | Yes |
| Add a new row | Yes |
| Change a row | Yes |
| Delete a row | Yes |
| Run 4 questions in a row without popup | Yes — zero popups |

---

## What You Should See

When the project starts up in Codespaces, you should see something like this in the terminal:

```
============================================
  Starburst MCP: postStartCommand (start)
============================================
[ENV] GitHub Codespaces
[OK] Python 3.12.1
[OK] Core dependencies available
[OK] .env file found
  STARBURST_HOST = datateam-free-cluster.trino.galaxy.starburst.io
  STARBURST_PORT = 443
  STARBURST_CATALOG = mcp2ohio
  Auth: BasicAuth
[OK] server.py found
[OK] MCP server responds: starburst-rw v1.27.0
============================================
  All checks passed — MCP server ready
============================================
```

If you see "All checks passed" — everything is working.

---

## Current Data in the Demo Table

After today's session, the `demo` table has:

| id | name  | amount |
|----|-------|--------|
| 1  | hello | 150.0  |
| 2  | test2 | 200.0  |

---

## If Something Goes Wrong

### "Server not found" or "server.py not found"
- Make sure you're in the `starburst-demo` project folder
- Try closing and reopening Codespaces

### "Missing dependencies"
- The system should fix this automatically on restart
- If it doesn't, type this in the terminal:
  ```
  bash .devcontainer/setup.sh
  ```

### "Cannot connect to Starburst"
- Check that the `.env` file exists in the `gen ai project/starburst-mcp2/` folder
- The `.env` file contains your login information — it may need to be recreated after a full rebuild

### "OAuth popup still appearing"
- This should no longer happen after today's fix
- If it does, make sure you pulled the latest code from the `dev1` branch

### The project was rebuilt and everything is gone
- Your code is safe — it's saved in GitHub
- But the `.env` file (with your login info) is private and NOT saved in GitHub
- You'll need to recreate it — ask your team lead for the credentials

---

## Simple Summary

| What | Before | After |
|------|--------|-------|
| Works on | One Windows laptop only | Any computer or Codespace |
| Setup | Manual — many steps | Automatic — zero steps |
| Login popup | Every single question | Never — completely silent |
| Connection | New login per question | Reuses one connection (faster) |
| Dependencies | Might be outdated | Fresh install every time |

**Bottom line:** The Starburst MCP server now works everywhere, sets itself up, and never shows a login popup during demos. You just open the project and start asking questions about your data.

---

## Changes Saved To

- **Branch:** `dev1`
- **Repository:** `selvar2/starburst-demo`
- **Date:** April 8, 2026
