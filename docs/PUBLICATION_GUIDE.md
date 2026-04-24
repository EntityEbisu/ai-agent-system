# GitHub Publication & Git Strategy Guide

## 1. Repository Setup

### Public vs. Private Documentation
* **Keep Public**:
    * `README.md`, `QUICK_START.md`, `IaC_DOCUMENTATION.md`
    * `CONTRIBUTING.md`, `LICENSE`, `CHANGELOG.md`
    * `docs/PRESENTATION_OUTLINE.md`, `docs/DEMO_STORYBOARD.md`
    * Architecture diagrams in `docs/diagrams/`
* **Keep Private/Remove**:
    * `.env` (contains real API keys)
    * `logs/` (may contain user data)
    * `data/sqlite/*.db` (contains session history)
    * `data/chroma_db/` (contains vector data)
    * `.continue/` (local IDE configurations)
    * Any internal assignment briefs or sensitive company-specific PDFs.

## 2. Robust .gitignore Template
Ensure your `.gitignore` includes the following:

```gitignore
# IDEs
.vscode/
.idea/
.continue/

# Environments
.env
venv/
__pycache__/

# Logs & Data
logs/*.log
data/sqlite/*.db
data/chroma_db/
!data/docs/.gitkeep

# OS files
.DS_Store
```

## 3. Semantic Versioning Strategy
We follow [SemVer 2.0.0](https://semver.org/):
* **v1.0.0**: Initial release (CORE SYSTEM COMPLETE).
* **v1.1.0**: Minor features (e.g., improved RAG chunking).
* **v2.0.0**: Breaking changes (e.g., migrating from in-memory to Redis).

## 4. GitHub Creation & Initial Commit Instructions

### Step 1: Initialize Git
```bash
git init
```

### Step 2: Final Sanity Check
Check for sensitive data before adding files:
```bash
grep -r "sk-" .
```

### Step 3: Add and Commit
```bash
git add .
git commit -m "chore: initial commit - core agent system v1.0.0"
```

### Step 4: Push to GitHub
1. Create a new repository on GitHub.
2. Link and push:
```bash
git remote add origin https://github.com/your-username/ai-agent-system.git
git branch -M main
git push -u origin main
```

## 5. Deployment with GitHub Pages

## 6. Detailed Push Instructions & GitHub Pages Setup

### Pushing the Code to GitHub
1. **Ensure a clean working tree**
   ```bash
   git status
   # Should show no uncommitted changes
   ```
2. **Add all project files**
   ```bash
   git add .
   ```
3. **Commit with a clear message**
   ```bash
   git commit -m "chore: prepare repository for publication"
   ```
4. **Create a remote repository (if not already created)**
   - Go to https://github.com/new and create a repository named `ai-agent-system`.
   - Do **not** initialize with a README, .gitignore, or license (we already have them).
5. **Add the remote and push**
   ```bash
   git remote add origin https://github.com/<YOUR_USERNAME>/ai-agent-system.git
   git branch -M main
   git push -u origin main
   ```
6. **Verify on GitHub**
   Open `https://github.com/<YOUR_USERNAME>/ai-agent-system` and confirm all files appear.

### Setting Up GitHub Pages for Documentation
1. **Enable Pages**
   - Navigate to **Settings > Pages** in your repository.
   - Under **Source**, select **Deploy from a branch**.
   - Choose **main** branch and the **/docs** folder.
   - Click **Save**. GitHub will provide a URL like `https://<YOUR_USERNAME>.github.io/ai-agent-system/`.
2. **Optional: Automate Docs Deployment**
   - The workflow defined in section 5 will automatically build and publish docs on each push to `main`.
3. **Verify the site**
   - Visit the provided URL and ensure the markdown files render correctly.

You now have a fully version‑controlled repository on GitHub with optional public documentation via GitHub Pages.

## 7. Detailed Step-by-Step Instructions for Pushing the Code to GitHub

Follow these exact commands in your terminal from the project root:

1. **Verify a clean working tree**
   ```bash
   git status
   # Ensure it reports "nothing to commit, working tree clean"
   ```
2. **Add all project files**
   ```bash
   git add .
   ```
3. **Commit with a descriptive message**
   ```bash
   git commit -m "chore: prepare repository for publication"
   ```
4. **Create the remote repository on GitHub**
   - Open a browser to https://github.com/new
   - Fill in the repository name (e.g., `ai-agent-system`), choose Public or Private, **do not** initialize with a README, .gitignore, or license.
   - Click **Create repository**.
5. **Add the remote and push**
   ```bash
   git remote add origin https://github.com/<YOUR_USERNAME>/ai-agent-system.git
   git branch -M main
   git push -u origin main
   ```
6. **Verify the push**
   Open `https://github.com/<YOUR_USERNAME>/ai-agent-system` in a browser and confirm all files are present.

## 8. Setting Up GitHub Pages (Optional Documentation Site)

If you want to host the `docs/` folder as a static site:

1. In the GitHub repository, go to **Settings → Pages**.
2. Under **Source**, select **Deploy from a branch**.
3. Choose the **main** branch and the **/docs** folder.
4. Click **Save**. GitHub will provide a URL like `https://<YOUR_USERNAME>.github.io/ai-agent-system/`.
5. (Optional) Enable the documentation workflow from section 5 to automatically rebuild the site on each push.

You now have a complete, reproducible process for publishing the code and its documentation.

### Detailed GitHub Publication Steps

#### 1. Create a New Repository on GitHub
```bash
# Open your browser and go to https://github.com/new
# Fill in:
#   Repository name: ai-agent-system
#   Description: (optional)
#   Public/Private: Public (or Private if you prefer)
#   Initialize with a README: No (we already have one)
# Click **Create repository**
```

#### 2. Add Remote and Push Local Code
```bash
# In your local project root
git remote add origin https://github.com/<YOUR_USERNAME>/ai-agent-system.git
git branch -M main
git push -u origin main
```

#### 3. Verify Repository Contents
- Browse to `https://github.com/<YOUR_USERNAME>/ai-agent-system`
- Ensure all project files are present, `.gitignore` excludes secrets, and the `README.md` renders correctly.

#### 4. Set Up Branch Protection (optional but recommended)
```bash
# In GitHub repo > Settings > Branches > Add rule
#   Branch name pattern: main
#   Require pull request reviews before merging
#   Require status checks (e.g., CI workflow)
#   Include administrators: optional
```

#### 5. Enable GitHub Pages (for documentation)
1. Go to **Settings > Pages**.
2. Under **Source**, select **Deploy from a branch**.
3. Choose **main** branch and **/docs** folder.
4. Click **Save**. GitHub will provide a URL like `https://<YOUR_USERNAME>.github.io/ai-agent-system/`.
5. Verify the site loads; it will render the markdown files in `docs/`.

#### 6. Automate Documentation Deployment (optional)
Add a GitHub Actions workflow to build and publish docs with MkDocs or similar.
```yaml
name: Docs
on:
  push:
    branches: [main]
    paths: ["docs/**"]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - run: pip install mkdocs mkdocs-material
      - run: mkdocs build
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./site
```

#### 7. Final Clean‑up
- Remove any leftover local branches: `git branch -d <branch>`
- Ensure `.env` and other secrets are listed in `.gitignore`.
- Tag the release:
```bash
git tag -a v1.0.0 -m "Initial production release"
git push origin v1.0.0
```

You now have a fully version‑controlled, publicly accessible repository with optional GitHub Pages documentation.
If you want to host documentation:
1. Go to **Settings > Pages**.
2. Select **Source: Deploy from a branch**.
3. Select **main branch /docs folder** (if applicable) or use a tool like MkDocs.
