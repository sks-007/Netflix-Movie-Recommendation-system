#!/bin/bash
# Pre-deployment validation script for Render

echo "🚀 Netflix Recommendation System - Deployment Setup"
echo "=================================================="

# Check Python version
echo "🐍 Python Version:"
python --version

# Check available memory
echo "💾 Available Memory:"
python -c "import psutil; print(f'{psutil.virtual_memory().available / (1024**3):.2f} GB available')" 2>/dev/null || echo "Memory info not available"

# Check disk space
echo "💿 Disk Space:"
df -h . | tail -1 | awk '{print $4 " available"}'

# Validate model file
echo "📋 Model File Validation:"
if [ -f "model.pkl.gz" ]; then
    echo "✅ Model file exists"
    SIZE=$(stat -f%z model.pkl.gz 2>/dev/null || stat -c%s model.pkl.gz)
    SIZE_MB=$((SIZE / 1024 / 1024))
    echo "📏 Model size: ${SIZE_MB}MB"
    
    if [ $SIZE_MB -gt 50 ]; then
        echo "⚠️  Large model file detected - may affect startup time"
    fi
else
    echo "❌ Model file missing!"
    echo "📁 Files in directory:"
    ls -la
    exit 1
fi

# Test model loading
echo "🧪 Testing Model Loading:"
python -c "
import pickle, gzip, sys
try:
    with gzip.open('model.pkl.gz', 'rb') as f:
        data = pickle.load(f)
    print('✅ Model loads successfully')
    print(f'📊 Dataset size: {len(data[\"netflix_data\"])}')
    print(f'🔗 Matrix shape: {data[\"cosine_sim\"].shape}')
except Exception as e:
    print(f'❌ Model loading failed: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ Pre-deployment validation passed!"
else
    echo "❌ Pre-deployment validation failed!"
    exit 1
fi

echo "🎬 Starting application..."

# Install requirements and start the app
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# Run the application
exec gunicorn --workers 1 --timeout 180 --max-requests 100 --bind 0.0.0.0:$PORT app:app