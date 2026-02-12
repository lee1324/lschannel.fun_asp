#!/bin/bash

# Script to check existence of all files referenced in db.json files
# Usage: ./check_resources.sh [base_path]
# Default base_path is wwwroot/multimedia

BASE_PATH="${1:-wwwroot/multimedia}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$SCRIPT_DIR/$BASE_PATH"

if [ ! -d "$BASE_DIR" ]; then
    echo "Error: Directory $BASE_DIR does not exist"
    exit 1
fi

ERRORS=0
WARNINGS=0
TOTAL_FILES=0
CHECKED_FILES=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Checking resources in $BASE_DIR"
echo "=================================="
echo ""

# Function to check if file exists
check_file() {
    local file_path="$1"
    local db_path="$2"
    local file_type="$3"
    
    TOTAL_FILES=$((TOTAL_FILES + 1))
    
    if [ -f "$file_path" ]; then
        CHECKED_FILES=$((CHECKED_FILES + 1))
        return 0
    else
        echo -e "${RED}✗ MISSING${NC} [$file_type] $file_path (referenced in $db_path)"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check lsLearns db.json
check_lslearns() {
    local lang="$1"
    local db_file="$BASE_DIR/lsLearns/$lang/db.json"
    
    if [ ! -f "$db_file" ]; then
        echo -e "${YELLOW}⚠ WARNING${NC} db.json not found: $db_file"
        WARNINGS=$((WARNINGS + 1))
        return
    fi
    
    echo "Checking lsLearns/$lang/db.json..."
    
    # Extract filenames from db.json
    # Try using jq if available, otherwise use python for proper JSON parsing
    local filenames=""
    if command -v jq &> /dev/null; then
        filenames=$(jq -r '.list[]?.filename // empty' "$db_file" 2>/dev/null)
    elif command -v python3 &> /dev/null; then
        filenames=$(python3 -c "import json, sys; data = json.load(open('$db_file', encoding='utf-8')); [print(item.get('filename', '')) for item in data.get('list', []) if item.get('filename')]" 2>/dev/null)
    else
        # Fallback: use grep/sed (may not handle unicode properly)
        filenames=$(cat "$db_file" | grep -o '"filename"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"filename"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' | sed 's/\\"/"/g' | sed 's/\\u\([0-9a-fA-F]\{4\}\)/\\u\1/g')
    fi
    
    while IFS= read -r filename; do
        if [ -z "$filename" ]; then
            continue
        fi
        
        # Check video file
        local base=$(echo "$filename" | sed 's/\.[^.]*$//')
        local video_path="$BASE_DIR/lsLearns/$lang/videos/$filename"
        local cover_path="$BASE_DIR/lsLearns/$lang/covers_generated/${base}_cover.png"
        
        # For en, also check fallback to cn
        if [ "$lang" = "en" ]; then
            if [ ! -f "$video_path" ]; then
                local cn_video_path="$BASE_DIR/lsLearns/cn/videos/$filename"
                if [ -f "$cn_video_path" ]; then
                    echo -e "${YELLOW}⚠ FALLBACK${NC} Video $filename not in en/videos/, but found in cn/videos/"
                    WARNINGS=$((WARNINGS + 1))
                else
                    check_file "$video_path" "$db_file" "video"
                fi
            else
                check_file "$video_path" "$db_file" "video"
            fi
        else
            check_file "$video_path" "$db_file" "video"
        fi
        
        # Check cover (optional, so warning not error)
        if [ ! -f "$cover_path" ]; then
            echo -e "${YELLOW}⚠ MISSING COVER${NC} $cover_path (referenced in $db_file)"
            WARNINGS=$((WARNINGS + 1))
        else
            CHECKED_FILES=$((CHECKED_FILES + 1))
        fi
    done <<< "$filenames"
    
    echo ""
}

# Function to check music db.json
check_music() {
    local db_file="$BASE_DIR/music/db.json"
    
    if [ ! -f "$db_file" ]; then
        echo -e "${YELLOW}⚠ WARNING${NC} db.json not found: $db_file"
        WARNINGS=$((WARNINGS + 1))
        return
    fi
    
    echo "Checking music/db.json..."
    
    # Extract filenames from db.json
    local filenames=""
    if command -v jq &> /dev/null; then
        filenames=$(jq -r '.list[]?.filename // empty' "$db_file" 2>/dev/null)
    elif command -v python3 &> /dev/null; then
        filenames=$(python3 -c "import json, sys; data = json.load(open('$db_file', encoding='utf-8')); [print(item.get('filename', '')) for item in data.get('list', []) if item.get('filename')]" 2>/dev/null)
    else
        filenames=$(cat "$db_file" | grep -o '"filename"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"filename"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' | sed 's/\\"/"/g')
    fi
    
    while IFS= read -r filename; do
        if [ -z "$filename" ]; then
            continue
        fi
        
        local base=$(echo "$filename" | sed 's/\.[^.]*$//')
        local video_path="$BASE_DIR/music/videos/$filename"
        local cover_path="$BASE_DIR/music/covers_generated/${base}_cover.png"
        
        check_file "$video_path" "$db_file" "video"
        
        # Check cover (optional)
        if [ ! -f "$cover_path" ]; then
            echo -e "${YELLOW}⚠ MISSING COVER${NC} $cover_path (referenced in $db_file)"
            WARNINGS=$((WARNINGS + 1))
        else
            CHECKED_FILES=$((CHECKED_FILES + 1))
        fi
    done <<< "$filenames"
    
    echo ""
}

# Function to check paintings db.json
check_paintings() {
    local db_file="$BASE_DIR/paintings/db.json"
    
    if [ ! -f "$db_file" ]; then
        echo -e "${YELLOW}⚠ WARNING${NC} db.json not found: $db_file"
        WARNINGS=$((WARNINGS + 1))
        return
    fi
    
    echo "Checking paintings/db.json..."
    
    # Extract filenames from db.json
    local filenames=""
    if command -v jq &> /dev/null; then
        filenames=$(jq -r '.list[]?.filename // empty' "$db_file" 2>/dev/null)
    elif command -v python3 &> /dev/null; then
        filenames=$(python3 -c "import json, sys; data = json.load(open('$db_file', encoding='utf-8')); [print(item.get('filename', '')) for item in data.get('list', []) if item.get('filename')]" 2>/dev/null)
    else
        filenames=$(cat "$db_file" | grep -o '"filename"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"filename"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' | sed 's/\\"/"/g')
    fi
    
    while IFS= read -r filename; do
        if [ -z "$filename" ]; then
            continue
        fi
        
        local base=$(echo "$filename" | sed 's/\.[^.]*$//')
        local image_path="$BASE_DIR/paintings/images/$filename"
        local cover_path="$BASE_DIR/paintings/covers_generated/${base}_cover.png"
        
        check_file "$image_path" "$db_file" "image"
        
        # Check cover (optional)
        if [ ! -f "$cover_path" ]; then
            echo -e "${YELLOW}⚠ MISSING COVER${NC} $cover_path (referenced in $db_file)"
            WARNINGS=$((WARNINGS + 1))
        else
            CHECKED_FILES=$((CHECKED_FILES + 1))
        fi
    done <<< "$filenames"
    
    echo ""
}

# Function to check downloads db.json
check_downloads() {
    local db_file="$BASE_DIR/downloads/db.json"
    
    if [ ! -f "$db_file" ]; then
        echo -e "${YELLOW}⚠ WARNING${NC} db.json not found: $db_file"
        WARNINGS=$((WARNINGS + 1))
        return
    fi
    
    echo "Checking downloads/db.json..."
    
    # Extract filenames from db.json
    local filenames=""
    if command -v jq &> /dev/null; then
        filenames=$(jq -r '.list[]?.filename // empty' "$db_file" 2>/dev/null)
    elif command -v python3 &> /dev/null; then
        filenames=$(python3 -c "import json, sys; data = json.load(open('$db_file', encoding='utf-8')); [print(item.get('filename', '')) for item in data.get('list', []) if item.get('filename')]" 2>/dev/null)
    else
        filenames=$(cat "$db_file" | grep -o '"filename"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"filename"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' | sed 's/\\"/"/g')
    fi
    
    while IFS= read -r filename; do
        if [ -z "$filename" ]; then
            continue
        fi
        
        local file_path="$BASE_DIR/downloads/$filename"
        check_file "$file_path" "$db_file" "download"
    done <<< "$filenames"
    
    echo ""
}

# Main execution
check_lslearns "cn"
check_lslearns "en"
check_music
check_paintings
check_downloads

# Summary
echo "=================================="
echo "Summary:"
echo -e "  Total files checked: ${GREEN}$TOTAL_FILES${NC}"
echo -e "  Files found: ${GREEN}$CHECKED_FILES${NC}"
if [ $ERRORS -gt 0 ]; then
    echo -e "  Errors (missing files): ${RED}$ERRORS${NC}"
else
    echo -e "  Errors (missing files): ${GREEN}$ERRORS${NC}"
fi
if [ $WARNINGS -gt 0 ]; then
    echo -e "  Warnings (missing covers/fallbacks): ${YELLOW}$WARNINGS${NC}"
else
    echo -e "  Warnings (missing covers/fallbacks): ${GREEN}$WARNINGS${NC}"
fi

if [ $ERRORS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All required files exist!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}✗ Some files are missing!${NC}"
    exit 1
fi
