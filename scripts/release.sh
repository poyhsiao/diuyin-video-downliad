#!/bin/bash
set -e

echo "=== Release Preparation ==="

# 分析 commits
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")
COMMITS=$(git log $LAST_TAG..HEAD --oneline 2>/dev/null | wc -l | tr -d ' ')

echo "Last tag: $LAST_TAG"
echo "Commits since last tag: $COMMITS"

if [ "$COMMITS" -eq 0 ] || [ "$COMMITS" = "0" ]; then
  echo "No commits since last tag, skipping release"
  exit 0
fi

echo ""
echo "Recent commits:"
git log $LAST_TAG..HEAD --oneline | head -10

echo ""
echo "Select version bump:"
echo "  [p] patch (default)"
echo "  [m] minor"  
echo "  [M] major"
read -p "Choice (p): " choice

case $choice in
  m|M) TYPE=$choice ;;
  *) TYPE="p" ;;
esac

if [ "$TYPE" = "M" ]; then
  BUMP_TYPE="major"
elif [ "$TYPE" = "m" ]; then
  BUMP_TYPE="minor"
else
  BUMP_TYPE="patch"
fi

echo ""
echo "Bumping $BUMP_TYPE version..."

# 執行版本升級
./scripts/version-bump.sh $BUMP_TYPE
./scripts/changelog.sh $BUMP_TYPE

VERSION=$(cat .version)

# Git commit
git add -A
git commit -m "release: v$VERSION"

# Git tag
git tag -a "v$VERSION" -m "v$VERSION"

# Git push
echo ""
echo "Pushing to remote..."
git push origin main --tags

# GitHub Release
echo ""
echo "Creating GitHub release..."
gh release create "v$VERSION" \
  --title "v$VERSION" \
  --notes "See CHANGELOG.md for details"

echo ""
echo "=== Release v$VERSION Complete ==="
