#!/bin/bash
# Git Phase Merge Script
# Usage: ./scripts/git-phase-merge.sh <phase_number>

set -e

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <phase_number>"
    echo "Example: $0 1"
    exit 1
fi

PHASE_NUMBER=$1

# Determine branch name based on phase number
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

# Checkout master and pull latest
echo "Switching to master branch..."
git checkout master
git pull origin master

# Merge phase branch
echo "Merging $BRANCH_NAME into master..."
git merge "$BRANCH_NAME" -m "Merge Phase $PHASE_NUMBER: Completed and verified"

# Push master to remote
echo "Pushing master to remote..."
git push origin master

# Delete local and remote phase branch
echo "Cleaning up phase branch..."
git branch -d "$BRANCH_NAME"
git push origin --delete "$BRANCH_NAME" || true

echo "✓ Successfully merged Phase $PHASE_NUMBER ($BRANCH_NAME) into master"
