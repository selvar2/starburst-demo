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

---
---

# Version 2: StarQuery AI — Your Data Chatbot
## What We Built — April 14-15, 2026
### A plain-English guide to the new chatbot interface

---

## What This Does

We built a **chat window** where you can ask questions about your data in plain English. Think of it like texting a really smart assistant who knows everything about your database.

You type something like:
- "Show all tables"
- "How many rows are in the demo table?"
- "Show me sales by region"

And it:
- Finds the data for you
- Shows it in a nice table
- Draws a chart (bar, pie, line)
- Lets you download the results (Excel, PDF, CSV, etc.)

---

## What You Need

- A web browser (Chrome, Firefox, Edge — any will work)
- The server must be running (someone starts it for you, or you run one command)
- Your Starburst Galaxy account credentials (already saved in a settings file)

---

## Step-by-Step: How to Use StarQuery AI

### 1. Open the App

Open your browser and go to:
```
http://localhost:8000
```

You will see a dark-themed chat screen with "Welcome to StarQuery AI" in the middle.

### 2. Look at the Left Sidebar

On the left side, you'll see a **Schema Browser**. This shows all your databases and tables — like a folder tree:

```
mcp2ohio
  ├── information_schema
  ├── system
  └── test_writes
      ├── demo
      ├── employees
      ├── products
      ├── sales_by_region
      └── web_analytics
```

You can **click any table name** to automatically load its data.

There's also a **refresh button (↻)** next to "Schema Browser" — click it if you think the list is outdated.

### 3. Ask a Question

Type your question in the text box at the bottom. Here are things you can ask:

**Simple questions (plain English):**
- `show all tables`
- `describe demo`
- `show all data from demo`
- `count rows in demo`

**Questions about specific databases:**
- `show all data from roles, roles is part of information_schema schema and part of mcp2ohio catalog`

**Direct SQL (if you know SQL):**
- `SELECT region, SUM(revenue) FROM mcp2ohio.test_writes.sales_by_region GROUP BY region`

Press **Enter** to send. The app will show you:
1. The SQL it wrote for you
2. A table with the results
3. A chart (if the data is suitable)
4. Download buttons

### 4. Read the Results

Each response from the AI shows:

- **SQL Query** — click to expand and see the actual database query
- **Row count** — a green badge showing how many rows came back
- **Data table** — your results in a clean table format
- **Chart** — a bar chart, pie chart, or line chart drawn automatically
- **Download buttons** — CSV, Excel, HTML, PDF, JPEG

### 5. Use the Suggestion Chips

After every answer, you'll see **clickable buttons** at the bottom with follow-up questions. For example, after showing all tables, you might see:

- "DESCRIBE mcp2ohio.test_writes.demo"
- "SELECT * FROM mcp2ohio.test_writes.demo LIMIT 100"

**Just click one** — no need to type anything!

### 6. Download Your Results

Below every table, you'll see five buttons:

| Button | What You Get |
|--------|-------------|
| **CSV** | A spreadsheet file you can open in Excel |
| **Excel** | An Excel file (.xlsx) |
| **HTML** | A web page with your table |
| **PDF** | A PDF document with the table and chart |
| **JPEG** | A picture of the results |

Click any button and the file will download automatically.

### 7. Change the Chart

On the right side (click the chart icon ↗ at the top right if hidden), you can:

- Pick a chart type: **Bar**, **Pie**, **Line**, or **Area**
- Choose which columns go on each axis
- Pick a color theme
- Click **Generate Chart** to redraw

### 8. Switch Between Dark and Light Mode

At the bottom left, there's a **Dark/Light toggle**. Click it to switch the look.

---

## What You Should See

### When You First Open the App:
- A welcome screen with four clickable buttons
- The sidebar showing your databases and tables
- A text box saying "Ask about your data..."

### After You Ask a Question:
- Your question appears on the right (purple bubble)
- The answer appears on the left with a table and chart
- Suggestion buttons appear below the answer

### Sample Results:

**Query:** `SELECT region, SUM(revenue) FROM mcp2ohio.test_writes.sales_by_region GROUP BY region`

**You see:**
- A table with 5 regions and their total revenue
- A bar chart with colored bars for each region
- Download buttons below the table

---

## If Something Goes Wrong

### "Loading schema..." stays forever
- The database might be waking up (it sleeps after 5 minutes of no use)
- Wait 30 seconds and refresh the page
- Click the refresh button (↻) next to Schema Browser

### Red error message appears
- Read the error — it usually tells you what's wrong
- Common: "Table does not exist" — check the table name spelling
- Try clicking a table from the sidebar instead of typing

### The page won't load at all
- Make sure the server is running
- Ask someone to start it with: `python -m uvicorn app_jwt:app --port 8000`

### Chart looks wrong or doesn't appear
- Not all data can make charts — you need at least one text column and one number column
- Try a GROUP BY query for better charts

### Download doesn't work
- PDF and JPEG are captured from the screen — wait for the chart to fully load first
- CSV and Excel always work

---

## New Tables You Can Explore

We added four tables with sample data so you can try different charts:

| Table | What's Inside | Try This |
|-------|-------------|----------|
| **sales_by_region** | Sales data for 5 regions, 4 quarters | "SELECT region, SUM(revenue) FROM mcp2ohio.test_writes.sales_by_region GROUP BY region" |
| **employees** | 20 employees with salary and department | "SELECT department, AVG(salary) FROM mcp2ohio.test_writes.employees GROUP BY department" |
| **web_analytics** | Website visitor data by page and month | "SELECT page, SUM(visitors) FROM mcp2ohio.test_writes.web_analytics GROUP BY page" |
| **products** | 15 tech products with prices and ratings | "SELECT category, AVG(rating) FROM mcp2ohio.test_writes.products GROUP BY category" |

---

## No More Browser Popups!

In version 1, a login window popped up in your browser every time. That's gone now. The app logs in automatically behind the scenes. You just open the page and start asking questions.

---

## Simple Summary

- **Open** `http://localhost:8000` in your browser
- **Type** a question or **click** a table in the sidebar
- **See** your results as a table and chart
- **Download** as Excel, CSV, PDF, or picture
- **Click suggestion chips** for quick follow-up queries
- **No login popups** — everything works automatically

---

## Changes Saved To

- **Branch:** `dev3`
- **Repository:** `selvar2/starburst-demo`
- **Date:** April 14-15, 2026
