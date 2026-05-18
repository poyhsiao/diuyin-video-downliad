#!/bin/bash
# 自動更新 CHANGELOG.md

TYPE=$1
VERSION=$(cat .version)
TODAY=$(date +%Y-%m-%d)
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "initial")

# 讀取當前 CHANGELOG 內容
TEMP_CHANGELOG=$(mktemp)

cat > $TEMP_CHANGELOG << EOF
# Changelog

All notable changes to this project will be documented in this file.

## [$VERSION] — $TODAY

### Added
$(git log --oneline -10 | grep -E "feat:|add:" | sed 's/^/- /' || echo "- Initial release")
EOF

# 合併現有 CHANGELOG
tail -n +4 CHANGELOG.md >> $TEMP_CHANGELOG
mv $TEMP_CHANGELOG CHANGELOG.md

echo "CHANGELOG.md updated for $VERSION"
