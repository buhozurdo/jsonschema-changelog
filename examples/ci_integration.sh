#!/bin/bash
# CI Integration Example for jsonschema-changelog
#
# This script demonstrates how to integrate schema validation
# into your CI/CD pipeline (GitHub Actions, GitLab CI, etc.)
#
# Usage:
#   ./ci_integration.sh old_schema.json new_schema.json

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================="
echo "JSON Schema Change Validation"
echo "============================================="
echo ""

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <old_schema.json> <new_schema.json>"
    exit 1
fi

OLD_SCHEMA=$1
NEW_SCHEMA=$2

# Verify files exist
if [ ! -f "$OLD_SCHEMA" ]; then
    echo -e "${RED}Error: Old schema file not found: $OLD_SCHEMA${NC}"
    exit 1
fi

if [ ! -f "$NEW_SCHEMA" ]; then
    echo -e "${RED}Error: New schema file not found: $NEW_SCHEMA${NC}"
    exit 1
fi

echo "Comparing schemas:"
echo "  Old: $OLD_SCHEMA"
echo "  New: $NEW_SCHEMA"
echo ""

# Step 1: Show diff summary
echo "Step 1: Detecting changes..."
echo "-------------------------------------------"
jsonschema-changelog diff "$OLD_SCHEMA" "$NEW_SCHEMA" --format text 2>&1 || true
echo ""

# Step 2: Validate compatibility
echo "Step 2: Validating backward compatibility..."
echo "-------------------------------------------"

if jsonschema-changelog validate "$OLD_SCHEMA" "$NEW_SCHEMA" --fail-on-breaking 2>&1; then
    echo -e "${GREEN}✅ Schema changes are backward compatible${NC}"
    COMPATIBLE=true
else
    echo -e "${RED}❌ Schema changes break backward compatibility${NC}"
    COMPATIBLE=false
fi
echo ""

# Step 3: Generate changelog
echo "Step 3: Generating changelog..."
echo "-------------------------------------------"
jsonschema-changelog changelog "$OLD_SCHEMA" "$NEW_SCHEMA" \
    --format markdown \
    --title "Schema Changes" \
    --output SCHEMA_CHANGELOG.md 2>&1 || true

echo "Changelog saved to SCHEMA_CHANGELOG.md"
echo ""

# Step 4: Generate migration script (if breaking changes)
if [ "$COMPATIBLE" = false ]; then
    echo "Step 4: Generating migration script..."
    echo "-------------------------------------------"
    jsonschema-changelog migrate "$OLD_SCHEMA" "$NEW_SCHEMA" \
        --language python \
        --output migrate_schema.py 2>&1 || true
    
    echo "Migration script saved to migrate_schema.py"
    echo -e "${YELLOW}⚠️  Review the migration script before applying${NC}"
    echo ""
fi

# Step 5: Export JSON report for CI artifacts
echo "Step 5: Generating JSON report..."
echo "-------------------------------------------"
jsonschema-changelog validate "$OLD_SCHEMA" "$NEW_SCHEMA" \
    --format json \
    --no-fail-on-breaking \
    --output schema_validation_report.json 2>&1 || true

echo "JSON report saved to schema_validation_report.json"
echo ""

# Final summary
echo "============================================="
echo "Summary"
echo "============================================="
if [ "$COMPATIBLE" = true ]; then
    echo -e "${GREEN}Schema update is safe to deploy!${NC}"
    echo ""
    echo "Generated files:"
    echo "  - SCHEMA_CHANGELOG.md (changelog)"
    echo "  - schema_validation_report.json (CI report)"
    exit 0
else
    echo -e "${RED}Schema update has breaking changes!${NC}"
    echo ""
    echo "Generated files:"
    echo "  - SCHEMA_CHANGELOG.md (changelog)"
    echo "  - migrate_schema.py (migration script)"
    echo "  - schema_validation_report.json (CI report)"
    echo ""
    echo "Actions required:"
    echo "  1. Review the breaking changes in SCHEMA_CHANGELOG.md"
    echo "  2. Review and customize migrate_schema.py"
    echo "  3. Test migration on staging data"
    echo "  4. Coordinate deployment with data migration"
    exit 1
fi
