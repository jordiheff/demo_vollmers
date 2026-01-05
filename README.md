# Nutrition Label Generator - Demo Package

Build a plug-and-play Windows demo using GitHub Actions.

## Setup Instructions (One-Time)

### Step 1: Create a GitHub Repository

1. Go to https://github.com/new
2. Name it something like `nutrition-label-demo`
3. Keep it **Private** (your API keys will be in secrets)
4. Click "Create repository"

### Step 2: Add Your API Keys as Secrets

1. In your new repo, go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add these two secrets:

   | Name | Value |
   |------|-------|
   | `OPENAI_API_KEY` | Your OpenAI API key |
   | `USDA_API_KEY` | Your USDA API key (optional) |

### Step 3: Push This Code

Run these commands in Terminal:

```bash
cd /Users/jojiheff/Documents/demo_nutrition_label_maker

git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/nutrition-label-demo.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

### Step 4: Download the Built App

1. Go to your repo on GitHub
2. Click the **Actions** tab
3. Click on the latest workflow run
4. Scroll down to **Artifacts**
5. Download `NutritionLabelGenerator-Windows`
6. Unzip it - this is what you send to your friend!

---

## For Your Friend

They just need to:
1. Unzip the folder
2. Double-click `NutritionLabelGenerator.exe`
3. Browser opens automatically
4. Close the console window to quit

That's it! No installation, no Python, no setup.

---

## Re-Building

Whenever you push changes to the repo, GitHub automatically rebuilds the app. You can also manually trigger a build:

1. Go to **Actions** tab
2. Click **Build Windows Demo**
3. Click **Run workflow**

---

## Files in This Package

```
demo_nutrition_label_maker/
├── .github/workflows/    # GitHub Actions build config
├── backend/              # Python backend
├── frontend/             # React frontend
├── launcher.py           # App entry point
├── nutrition_label.spec  # PyInstaller config
└── README.md             # This file
```

## Security Notes

- Your API keys are stored as GitHub Secrets (not in code)
- The built app contains your API keys in `.env`
- Only share the built zip with trusted people
- Consider setting billing alerts on your OpenAI account
