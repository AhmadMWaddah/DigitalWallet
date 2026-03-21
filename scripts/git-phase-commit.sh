#!/bin/bash
# Git Phase Commit Script (v2.2 - Multi-Agent Identity Support)
# Usage: ./scripts/git-phase-commit.sh <phase_number> "<title>" "<description>" [role]

set -e

# -- Configuration Section

# Check arguments
if [ $# -lt 3 ]; then
    echo "Usage: $0 <phase_number> \"<title>\" \"<description>\" [role]"
    echo "Roles: dev (Qwen-Coder), consult (Gemini-CLI), review (OpenAI-Codex), mgr (Ahmad)"
    exit 1
fi

PHASE_NUMBER=$1
TITLE=$2
DESCRIPTION=$3
ROLE=${4:-"mgr"} # Default to Manager

# -- Identity Mapping (@ai.local)

case "$ROLE" in
    "dev")
        AUTHOR_NAME="Qwen-Coder"
        AUTHOR_EMAIL="qwen-coder@ai.local"
        AUTHOR_URL="https://github.com/qwencoder"
        ;;
    "consult")
        AUTHOR_NAME="Gemini-CLI"
        AUTHOR_EMAIL="gemini-cli@ai.local"
        AUTHOR_URL="https://github.com/google-gemini/gemini-cli"
        ;;
    "review")
        AUTHOR_NAME="OpenAI-Codex"
        AUTHOR_EMAIL="openai-codex@ai.local"
        AUTHOR_URL="https://github.com/openai/codex"
        ;;
    "mgr"|*)
        AUTHOR_NAME=$(git config user.name)
        AUTHOR_EMAIL=$(git config user.email)
        AUTHOR_URL="Project Manager"
        ;;
esac

# -- Determine Branch Name

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

if ! git show-ref --verify --quiet refs/heads/"$BRANCH_NAME"; then
    echo "Creating branch: $BRANCH_NAME"
    git checkout -b "$BRANCH_NAME"
else
    git checkout "$BRANCH_NAME"
fi

# -- Stage & Commit

git add .

if git diff --staged --quiet; then
    echo "⚠ No changes to commit."
    exit 0
fi

# Commit with identity overrides
echo "Committing as $AUTHOR_NAME <$AUTHOR_EMAIL>..."

git -c user.name="$AUTHOR_NAME" -c user.email="$AUTHOR_EMAIL" commit \
    -m "Phase $PHASE_NUMBER: $TITLE" \
    -m "$DESCRIPTION" \
    -m "Identity: $AUTHOR_URL"

# Push to remote
git push -u origin "$BRANCH_NAME"

echo "✓ Successfully committed to $BRANCH_NAME as $AUTHOR_NAME"
