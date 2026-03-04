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

# -- Determine Branch Name

if [ "$PHASE_NUMBER" -ge 1 ] && [ "$PHASE_NUMBER" -le 3 ]; then
    BRANCH_NAME="phase-setup-automation"
elif [ "$PHASE_NUMBER" -ge 4 ] && [ "$PHASE_NUMBER" -le 6 ]; then
    BRANCH_NAME="phase-identity-auth"
elif [ "$PHASE_NUMBER" -ge 7 ] && [ "$PHASE_NUMBER" -le 8 ]; then
    BRANCH_NAME="phase-frontend-core"
elif [ "$PHASE_NUMBER" -ge 9 ] && [ "$PHASE_NUMBER" -le 10 ]; then
    BRANCH_NAME="phase-wallet-engine"
elif [ "$PHASE_NUMBER" -ge 11 ] && [ "$PHASE_NUMBER" -le 12 ]; then
    BRANCH_NAME="phase-dashboard-htmx"
elif [ "$PHASE_NUMBER" -ge 13 ] && [ "$PHASE_NUMBER" -le 14 ]; then
    BRANCH_NAME="phase-async-reporting"
elif [ "$PHASE_NUMBER" -ge 15 ] && [ "$PHASE_NUMBER" -le 16 ]; then
    BRANCH_NAME="phase-staff-analytics"
elif [ "$PHASE_NUMBER" -ge 17 ] && [ "$PHASE_NUMBER" -le 18 ]; then
    BRANCH_NAME="phase-qa-deployment"
else
    echo "Error: Invalid phase number. Must be between 1 and 18."
    exit 1
fi

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

# Push to remote
git push -u origin "$BRANCH_NAME"

echo "✓ Successfully committed Phase $PHASE_NUMBER to branch: $BRANCH_NAME"
