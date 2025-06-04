# Git Setup and Sync Instructions

## Step 1: Create GitHub Repository

1. Go to https://github.com and create a new repository
2. Name it `multi-agent-invoice-processing` (or your preferred name)
3. Make it public or private as needed
4. Don't initialize with README (we already have one)

## Step 2: Connect to GitHub

From the project directory, run these commands:

```bash
# Add all files to staging
git add .

# Make initial commit
git commit -m "Initial commit: Multi-agent invoice processing system with LangGraph"

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git

# Push to GitHub
git push -u origin main
```

## Step 3: Clone to Your Local System

On your Windows machine:

```cmd
# Clone the repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
cd YOUR_REPOSITORY_NAME

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements-local.txt

# Set up environment variable
set OPENAI_API_KEY=your_api_key_here

# Create required folders
mkdir sessions
mkdir output

# Run the application
streamlit run app.py --server.port 5000
```

## Step 4: Regular Git Workflow

### Making Changes
```bash
# Check status
git status

# Add specific files or all changes
git add filename.py
# or
git add .

# Commit changes
git commit -m "Description of changes"

# Push to GitHub
git push
```

### Pulling Updates
```bash
# Pull latest changes from GitHub
git pull origin main
```

## Step 5: Environment Variables Setup

Create a `.env` file locally (not tracked by Git):
```
OPENAI_API_KEY=your_actual_api_key_here
```

## Project Structure Ready for Git

Your repository will contain:
- All Python agent files
- Configuration files
- Documentation
- Streamlit setup
- Proper .gitignore to exclude sensitive data
- Requirements file for easy setup

The `sessions/` and `output/` folders will be created automatically when you run the application.