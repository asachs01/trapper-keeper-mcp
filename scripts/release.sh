#!/usr/bin/env bash
# Release script for Trapper Keeper MCP

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Get current version
get_current_version() {
    git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0"
}

# Validate version format
validate_version() {
    local version=$1
    if ! [[ "$version" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*)?$ ]]; then
        error "Invalid version format. Expected: v1.2.3 or v1.2.3-rc.1"
    fi
}

# Check for uncommitted changes
check_git_status() {
    if ! git diff --quiet || ! git diff --cached --quiet; then
        error "There are uncommitted changes. Please commit or stash them first."
    fi
}

# Update CHANGELOG
update_changelog() {
    local version=$1
    local date=$(date +%Y-%m-%d)
    
    info "Updating CHANGELOG.md..."
    
    if ! grep -q "## \[$version\]" CHANGELOG.md 2>/dev/null; then
        # Create temporary file with new version entry
        {
            echo "# Changelog"
            echo
            echo "## [$version] - $date"
            echo
            echo "### Added"
            echo "- "
            echo
            echo "### Changed"
            echo "- "
            echo
            echo "### Fixed"
            echo "- "
            echo
            # Append rest of changelog
            tail -n +2 CHANGELOG.md 2>/dev/null || true
        } > CHANGELOG.tmp
        
        mv CHANGELOG.tmp CHANGELOG.md
        warning "Please update CHANGELOG.md with release notes"
        ${EDITOR:-vi} CHANGELOG.md
    fi
}

# Run tests
run_tests() {
    info "Running tests..."
    make test || error "Tests failed"
    success "All tests passed"
}

# Run checks
run_checks() {
    info "Running quality checks..."
    make check || error "Quality checks failed"
    success "All checks passed"
}

# Build distribution
build_dist() {
    info "Building distribution packages..."
    make build || error "Build failed"
    success "Distribution packages built"
}

# Create git tag
create_tag() {
    local version=$1
    info "Creating git tag $version..."
    
    git add -A
    git commit -m "Release $version" || true
    git tag -a "$version" -m "Release $version"
    success "Tag $version created"
}

# Push to remote
push_release() {
    local version=$1
    info "Pushing to remote..."
    
    git push origin main
    git push origin "$version"
    success "Pushed to remote"
}

# Main release flow
main() {
    echo "======================================"
    echo "Trapper Keeper MCP Release Script"
    echo "======================================"
    echo
    
    # Check prerequisites
    check_git_status
    
    # Get version
    CURRENT_VERSION=$(get_current_version)
    info "Current version: $CURRENT_VERSION"
    
    # Prompt for new version
    read -rp "Enter new version (e.g., v1.2.3): " NEW_VERSION
    validate_version "$NEW_VERSION"
    
    # Confirmation
    echo
    warning "This will create a new release: $NEW_VERSION"
    read -rp "Continue? (y/N): " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        info "Release cancelled"
        exit 0
    fi
    
    # Release steps
    update_changelog "$NEW_VERSION"
    run_tests
    run_checks
    build_dist
    create_tag "$NEW_VERSION"
    
    # Final confirmation before push
    echo
    warning "Ready to push release $NEW_VERSION to remote"
    read -rp "Push to remote? (y/N): " PUSH_CONFIRM
    if [[ "$PUSH_CONFIRM" =~ ^[Yy]$ ]]; then
        push_release "$NEW_VERSION"
    else
        info "Release created locally. Push manually when ready:"
        info "  git push origin main"
        info "  git push origin $NEW_VERSION"
    fi
    
    echo
    echo "======================================"
    success "Release $NEW_VERSION completed!"
    echo
    echo "Next steps:"
    echo "1. Wait for CI/CD to complete"
    echo "2. Check the GitHub release page"
    echo "3. Verify package on PyPI"
    echo "4. Update documentation if needed"
    echo "======================================"
}

# Run main function
main "$@"