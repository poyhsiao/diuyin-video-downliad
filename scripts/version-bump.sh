#!/bin/bash
# 根據類型升級版本號

TYPE=$1
CURRENT=$(grep 'version = ' pyproject.toml | sed 's/version = "//g;s/"//' | tr -d ' ')

IFS='.' read -ra VER <<< "$CURRENT"
MAJOR=${VER[0]}
MINOR=${VER[1]}
PATCH=${VER[2]}

case $TYPE in
  major) ((MAJOR++)); MINOR=0; PATCH=0 ;;
  minor) ((MINOR++)); PATCH=0 ;;
  patch) ((PATCH++)) ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
echo $NEW_VERSION > .version

# 更新 pyproject.toml
sed -i '' "s/version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml

echo "Version bumped: $CURRENT -> $NEW_VERSION"
