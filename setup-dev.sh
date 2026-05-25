#!/bin/bash
# Development environment setup script for Helga
# This script sets up a complete development environment with all modern tooling

set -e  # Exit on error

echo "🚀 Setting up Helga development environment..."
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"

# Check if Python 3.8+ is available
if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
    echo "❌ Error: Python 3.8 or higher is required"
    exit 1
fi
echo "   ✅ Python version is compatible"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "   ✅ Virtual environment created"
else
    echo "📦 Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "   ✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel > /dev/null
echo "   ✅ pip upgraded"
echo ""

# Install package in editable mode with dev dependencies
echo "📚 Installing Helga with development dependencies..."
pip install -e .[dev] > /dev/null
echo "   ✅ Helga installed in editable mode"
echo ""

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
pre-commit install > /dev/null
echo "   ✅ Pre-commit hooks installed"
echo ""

# Run pre-commit on all files (optional, can be slow)
read -p "🔍 Run pre-commit checks on all files? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   Running pre-commit checks..."
    pre-commit run --all-files || true
    echo "   ✅ Pre-commit checks complete"
fi
echo ""

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "🐳 Docker detected"
    if command -v docker-compose &> /dev/null; then
        echo "   ✅ Docker Compose available"
        read -p "   Start Docker services? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "   Starting Docker services..."
            docker-compose up -d
            echo "   ✅ Docker services started"
            echo "   📝 IRC server: localhost:6667"
            echo "   📝 MongoDB: localhost:27017"
        fi
    else
        echo "   ⚠️  Docker Compose not found"
    fi
else
    echo "🐳 Docker not detected (optional)"
fi
echo ""

# Run tests
read -p "🧪 Run tests? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   Running tests..."
    pytest -v
    echo "   ✅ Tests complete"
fi
echo ""

# Summary
echo "✨ Development environment setup complete!"
echo ""
echo "📖 Next steps:"
echo "   1. Activate the virtual environment: source venv/bin/activate"
echo "   2. Run tests: pytest"
echo "   3. Check code quality: pre-commit run --all-files"
echo "   4. Start coding! See CONTRIBUTING.md for guidelines"
echo ""
echo "📚 Documentation:"
echo "   - CONTRIBUTING.md - Contribution guidelines"
echo "   - MODERNIZATION.md - Modernization details"
echo "   - README.rst - Project overview"
echo ""
echo "🔗 Useful commands:"
echo "   pytest                    # Run tests"
echo "   pytest --cov=helga       # Run tests with coverage"
echo "   black helga              # Format code"
echo "   ruff check helga         # Lint code"
echo "   mypy helga               # Type check"
echo "   pre-commit run --all-files  # Run all checks"
echo "   docker-compose up        # Start services"
echo ""
echo "Happy coding! 🎉"

# Made with Bob
