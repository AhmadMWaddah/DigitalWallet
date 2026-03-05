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

# Delete local and remote phase branch (Remote-First Workflow cleanup)
echo "Cleaning up phase branch..."
git branch -d "$BRANCH_NAME"
git push origin --delete "$BRANCH_NAME" 2>/dev/null || echo "  (Remote branch already deleted)"

echo "✓ Successfully merged Phase $PHASE_NUMBER ($BRANCH_NAME) into master"
echo "✓ Remote-First Workflow cleanup complete"
