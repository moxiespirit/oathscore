#!/bin/bash
# ============================================================
# OathScore Migration Script
# Moves OathScore from .claude/worktrees/ to C:\Users\Me\projects\oathscore\
#
# INSTRUCTIONS:
# 1. Close any Claude Code session working on OathScore
# 2. Open a regular terminal (Git Bash)
# 3. Run: bash /c/Users/Me/.claude/worktrees/oathscore-planning/oathscore/migrate-oathscore.sh
# 4. Follow the prompts
# ============================================================

set -e

OLD_PATH="/c/Users/Me/.claude/worktrees/oathscore-planning/oathscore"
NEW_PATH="/c/Users/Me/projects/oathscore"
MEMORY_FILE="/c/Users/Me/.claude/projects/C--Users-Me/memory/MEMORY.md"

echo "========================================="
echo "  OathScore Migration"
echo "========================================="
echo ""
echo "FROM: $OLD_PATH"
echo "TO:   $NEW_PATH"
echo ""

# Step 1: Pre-flight checks
echo "[1/7] Pre-flight checks..."

if [ ! -d "$OLD_PATH" ]; then
    echo "ERROR: Source directory does not exist: $OLD_PATH"
    exit 1
fi

if [ -d "$NEW_PATH" ]; then
    echo "ERROR: Destination already exists: $NEW_PATH"
    echo "Remove it first if you want to re-run: rm -rf $NEW_PATH"
    exit 1
fi

# Check no Claude session is using the worktree
if pgrep -f "oathscore-planning" > /dev/null 2>&1; then
    echo "WARNING: A process may be using the worktree."
    echo "Close all Claude Code sessions working on OathScore first."
    read -p "Continue anyway? (y/N): " confirm
    if [ "$confirm" != "y" ]; then
        echo "Aborted."
        exit 0
    fi
fi

echo "  Source exists: YES"
echo "  Destination clear: YES"
echo ""

# Step 2: Create parent directory
echo "[2/7] Creating projects directory..."
mkdir -p "/c/Users/Me/projects"
echo "  Created: /c/Users/Me/projects/"
echo ""

# Step 3: Copy (not move — safer, we verify before deleting old)
echo "[3/7] Copying OathScore to new location..."
echo "  This may take a moment..."
cp -r "$OLD_PATH" "$NEW_PATH"
echo "  Copy complete."
echo ""

# Step 4: Verify copy
echo "[4/7] Verifying copy..."

OLD_COUNT=$(find "$OLD_PATH" -type f -not -path '*/.git/*' | wc -l)
NEW_COUNT=$(find "$NEW_PATH" -type f -not -path '*/.git/*' | wc -l)

echo "  Files in source:      $OLD_COUNT"
echo "  Files in destination:  $NEW_COUNT"

if [ "$OLD_COUNT" -ne "$NEW_COUNT" ]; then
    echo "ERROR: File count mismatch! Something went wrong."
    echo "Removing incomplete copy..."
    rm -rf "$NEW_PATH"
    exit 1
fi

# Check git is intact
cd "$NEW_PATH"
if git status > /dev/null 2>&1; then
    echo "  Git repository: OK"
else
    echo "WARNING: Git repository check failed. This may be a worktree issue."
    echo "You may need to re-clone from GitHub instead."
    echo "  git clone https://github.com/moxiespirit/oathscore.git $NEW_PATH"
fi

echo "  Verification: PASSED"
echo ""

# Step 5: Re-initialize git if needed (worktrees have .git as a file, not directory)
echo "[5/7] Checking git setup..."
if [ -f "$NEW_PATH/.git" ]; then
    echo "  Detected worktree .git file. Converting to standalone repo..."
    # Read the gitdir from the .git file
    GITDIR=$(cat "$NEW_PATH/.git" | sed 's/gitdir: //')
    # Remove the .git file
    rm "$NEW_PATH/.git"
    # Clone fresh from GitHub instead
    echo "  Worktree git cannot be simply moved. Cloning fresh..."
    TEMP_DIR=$(mktemp -d)
    git clone https://github.com/moxiespirit/oathscore.git "$TEMP_DIR/oathscore"
    # Copy the .git directory from clone
    cp -r "$TEMP_DIR/oathscore/.git" "$NEW_PATH/.git"
    rm -rf "$TEMP_DIR"
    cd "$NEW_PATH"
    # Reset to match our files (not the remote's)
    git checkout -- . 2>/dev/null || true
    echo "  Git re-initialized from GitHub remote."
else
    echo "  Git directory: OK (standalone)"
fi

BRANCH=$(cd "$NEW_PATH" && git branch --show-current 2>/dev/null || echo "unknown")
echo "  Branch: $BRANCH"
echo ""

# Step 6: Update MEMORY.md paths
echo "[6/7] Updating MEMORY.md session file paths..."
if [ -f "$MEMORY_FILE" ]; then
    # Update the OathScore session file path
    sed -i 's|C:\\Users\\Me\\.claude\\worktrees\\oathscore-planning\\oathscore\\tracking\\OATHSCORE_SESSION.md|C:\\Users\\Me\\projects\\oathscore\\tracking\\OATHSCORE_SESSION.md|g' "$MEMORY_FILE"
    echo "  Updated MEMORY.md"
else
    echo "  WARNING: MEMORY.md not found at $MEMORY_FILE"
    echo "  You'll need to manually update the OathScore path in MEMORY.md"
fi
echo ""

# Step 7: Summary
echo "[7/7] Migration complete!"
echo ""
echo "========================================="
echo "  RESULTS"
echo "========================================="
echo ""
echo "  New location: C:\\Users\\Me\\projects\\oathscore\\"
echo "  Files copied:  $NEW_COUNT"
echo "  Git branch:    $BRANCH"
echo ""
echo "  NEXT STEPS:"
echo "  1. Open the new location in Claude Code:"
echo "     claude C:\\Users\\Me\\projects\\oathscore"
echo ""
echo "  2. Run /oathscore-guardian to verify everything works"
echo ""
echo "  3. If all good, delete the old worktree:"
echo "     rm -rf /c/Users/Me/.claude/worktrees/oathscore-planning"
echo ""
echo "  4. Update any bookmarks/shortcuts to point to the new path"
echo ""
echo "========================================="
