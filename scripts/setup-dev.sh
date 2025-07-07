#!/usr/bin/env bash
# Development environment setup script for Trapper Keeper MCP

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check Python version
check_python() {
    info "Checking Python version..."
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed. Please install Python 3.8 or higher."
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_VERSION="3.8"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        error "Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    fi
    
    success "Python $PYTHON_VERSION found"
}

# Create virtual environment
create_venv() {
    info "Creating virtual environment..."
    if [ -d "venv" ]; then
        warning "Virtual environment already exists. Skipping creation."
    else
        python3 -m venv venv
        success "Virtual environment created"
    fi
}

# Activate virtual environment
activate_venv() {
    info "Activating virtual environment..."
    # shellcheck disable=SC1091
    source venv/bin/activate
    success "Virtual environment activated"
}

# Upgrade pip and install tools
upgrade_pip() {
    info "Upgrading pip and installing build tools..."
    pip install --upgrade pip setuptools wheel
    success "Pip and build tools upgraded"
}

# Install dependencies
install_deps() {
    info "Installing development dependencies..."
    pip install -e ".[dev,test,docs]"
    success "Dependencies installed"
}

# Setup pre-commit hooks
setup_hooks() {
    info "Setting up pre-commit hooks..."
    pre-commit install
    pre-commit install --hook-type commit-msg
    pre-commit install --hook-type pre-push
    success "Pre-commit hooks installed"
}

# Create necessary directories
create_dirs() {
    info "Creating necessary directories..."
    mkdir -p data logs .trapper-keeper
    success "Directories created"
}

# Copy example files
copy_examples() {
    info "Setting up configuration files..."
    if [ ! -f .env ]; then
        cp .env.example .env
        warning "Created .env file from .env.example. Please update with your API keys."
    else
        info ".env file already exists"
    fi
}

# Run initial checks
run_checks() {
    info "Running initial checks..."
    
    # Format check
    info "Checking code formatting..."
    if black --check src tests &> /dev/null; then
        success "Code formatting is correct"
    else
        warning "Code formatting issues detected. Run 'make format' to fix."
    fi
    
    # Lint check
    info "Running linter..."
    if ruff check src tests &> /dev/null; then
        success "No linting issues found"
    else
        warning "Linting issues detected. Run 'make lint' to see details."
    fi
    
    # Type check
    info "Running type checker..."
    if mypy src &> /dev/null; then
        success "No type errors found"
    else
        warning "Type errors detected. Run 'make type-check' to see details."
    fi
}

# Main execution
main() {
    echo "======================================"
    echo "Trapper Keeper MCP Development Setup"
    echo "======================================"
    echo
    
    check_python
    create_venv
    activate_venv
    upgrade_pip
    install_deps
    setup_hooks
    create_dirs
    copy_examples
    run_checks
    
    echo
    echo "======================================"
    success "Development environment setup complete!"
    echo
    echo "Next steps:"
    echo "1. Update .env with your API keys"
    echo "2. Run 'make test' to ensure everything is working"
    echo "3. Run 'make help' to see available commands"
    echo
    echo "To activate the virtual environment in the future:"
    echo "  source venv/bin/activate"
    echo "======================================"
}

# Run main function
main "$@"