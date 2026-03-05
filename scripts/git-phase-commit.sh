#!/bin/bash
# Git Phase Commit Script
# Usage: ./scripts/git-phase-commit.sh <phase_number> "<title>" "<description>"

set -e

# -- Configuration Section

# Check arguments
if [ $# -lt 3 ]; then
    echo "Usage: $0 <phase_number> \"<title>\" \"<description>\""
    echo "Example: $0 4 \"Custom User Model\" \"Implemented email-based auth with user_type field\""
    exit 1
fi

PHASE_NUMBER=$1
TITLE=$2
DESCRIPTION=$3

# -- Determine Branch Name (8-Phase Structure)

case "$PHASE_NUMBER" in
    1) BRANCH_NAME="phase-setup-automation" ;;
    2) BRANCH_NAME="phase-identity-auth" ;;
    3) BRANCH_NAME="phase-frontend-core" ;;
    4) BRANCH_NAME="phase-wallet-engine" ;;
    5) BRANCH_NAME="phase-dashboard-htmx" ;;
    6) BRANCH_NAME="phase-async-reporting" ;;
    7) BRANCH_NAME="phase-staff-analytics" ;;
    8) BRANCH_NAME="phase-qa-deployment" ;;
    *)
        echo "Error: Invalid phase number. Must be between 1 and 8."
        exit 1
        ;;
esac

# -- Branch Management

# Create and checkout phase branch if it doesn't exist
if ! git show-ref --verify --quiet refs/heads/"$BRANCH_NAME"; then
    echo "Creating branch: $BRANCH_NAME"
    git checkout -b "$BRANCH_NAME"
else
    echo "Switching to existing branch: $BRANCH_NAME"
    git checkout "$BRANCH_NAME"
fi

# -- Stage & Commit

# Stage all changes
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "⚠ No changes to commit. Working tree is clean."
    echo "✓ Phase $PHASE_NUMBER branch is ready: $BRANCH_NAME"
    exit 0
fi

# Commit with title and description
git commit -m "Phase $PHASE_NUMBER: $TITLE" -m "$DESCRIPTION"

# Push to remote (Remote-First Workflow)
git push -u origin "$BRANCH_NAME"

echo "✓ Successfully committed Phase $PHASE_NUMBER to branch: $BRANCH_NAME"
echo "✓ Branch pushed to origin (Remote-First Workflow)"
