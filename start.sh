#!/bin/bash
# Optimized Render deployment startup script

set -euo pipefail  # Exit on any error

echo "🚀 Netflix Recommendation System - Production Startup"
echo "=================================================="
echo "📅 Timestamp: $(date)"
echo "🌍 Environment: ${FLASK_ENV:-production}"
echo "💻 Platform: $(uname -a)"
echo

# System diagnostics
echo "📊 System Resources:"
echo "🐍 Python: $(python --version)"
echo "💾 Memory: $(python -c "import psutil; mem=psutil.virtual_memory(); print(f'{mem.available/1024**3:.1f}GB available / {mem.total/1024**3:.1f}GB total ({mem.percent:.1f}% used)')" 2>/dev/null || echo 'Memory info unavailable')"
echo "💿 Disk: $(df -h . | tail -1 | awk '{print $4 " available / " $2 " total"}')"
echo "🔧 CPU Cores: $(nproc 2>/dev/null || echo '1')"
echo

# Model file validation
echo "📋 Model Validation:"
if [ ! -f "model.pkl.gz" ]; then
    echo "❌ FATAL: Model file missing!"
    echo "📁 Directory contents:"
    ls -la
    exit 1
fi

# Check model file size and permissions
SIZE=$(stat -c%s model.pkl.gz 2>/dev/null || stat -f%z model.pkl.gz 2>/dev/null || echo "0")
SIZE_MB=$((SIZE / 1024 / 1024))
echo "✅ Model file found: ${SIZE_MB}MB"

if [ $SIZE_MB -eq 0 ]; then
    echo "❌ FATAL: Model file is empty or unreadable"
    exit 1
fi

if [ ! -r "model.pkl.gz" ]; then
    echo "❌ FATAL: No read permission for model file"
    exit 1
fi

# Pre-flight model loading test
echo "🧪 Model Loading Test:"
python -c "
import pickle, gzip, sys, traceback, gc, time
start_time = time.time()
try:
    print('📖 Loading model...')
    with gzip.open('model.pkl.gz', 'rb') as f:
        data = pickle.load(f)
    
    # Validate model structure
    required_keys = ['cosine_sim', 'netflix_data', 'indices']
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise ValueError(f'Missing keys: {missing}')
    
    load_time = time.time() - start_time
    print(f'✅ Model loaded successfully in {load_time:.2f}s')
    print(f'📊 Dataset: {len(data[\"netflix_data\"])} movies')
    print(f'🔗 Matrix: {data[\"cosine_sim\"].shape[0]} x {data[\"cosine_sim\"].shape[1]}')
    print(f'📇 Indices: {len(data[\"indices\"])} titles')
    
    # Free memory
    del data
    gc.collect()
    print('🧹 Memory cleaned up')
    
except Exception as e:
    print(f'❌ Model loading failed: {type(e).__name__}: {e}')
    traceback.print_exc()
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ FATAL: Model validation failed"
    exit 1
fi

echo
echo "✅ All pre-flight checks passed!"
echo "🚀 Starting Gunicorn server..."
echo

# Gunicorn configuration
export GUNICORN_CMD_ARGS="\
    --workers ${WEB_CONCURRENCY:-1} \
    --worker-class sync \
    --timeout ${GUNICORN_TIMEOUT:-300} \
    --graceful-timeout ${GUNICORN_GRACEFUL_TIMEOUT:-60} \
    --max-requests ${GUNICORN_MAX_REQUESTS:-50} \
    --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-10} \
    --worker-tmp-dir /dev/shm \
    --bind 0.0.0.0:${PORT:-8000} \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output"

# Start the application
exec gunicorn app:app