#!/bin/bash
# Setup script for Background Generator

echo "🎨 Setting up Background Generator..."
echo "=================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment."
        echo "Try installing python3-venv: sudo apt install python3-venv"
        exit 1
    fi
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "⬇️ Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies."
    echo "Try installing manually: pip install openai pandas requests pillow python-dotenv"
    exit 1
fi

echo "✅ Dependencies installed successfully!"

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OpenAI API key not found in environment variables."
    echo "Please set your API key:"
    echo "  export OPENAI_API_KEY='your-api-key-here'"
    echo "Or create a .env file with:"
    echo "  OPENAI_API_KEY=your-api-key-here"
fi

echo ""
echo "🎉 Setup completed!"
echo ""
echo "Usage examples:"
echo "  # Single logo"
echo "  python background_generator.py --logo 'https://logo.clearbit.com/apple.com' --name 'Apple'"
echo ""
echo "  # Batch processing"
echo "  python background_generator.py --csv sample_logos.csv"
echo ""
echo "  # Run examples"
echo "  python example_usage.py"
echo ""
echo "For more information, see BACKGROUND_GENERATOR_README.md"