# Netflix Recommendation System - Deployment Troubleshooting

##🚨 Common Deployment Issues on Render

### Issue: "Could not load recommendation model"

**Symptoms:**
- App works fine locally
- Shows "Movie/Show Not Found!" error on Render
- Error message: "System error: Could not load recommendation model"

**Root Causes:**
1. **Memory Constraints**: The 18MB model requires ~150MB RAM to load
2. **File Access Issues**: Model file not accessible in container
3. **Timeout Issues**: Model loading takes too long on startup

## 🔧 Solutions Implemented

### 1. Enhanced Error Handling
- Detailed logging for model loading process
- Better error messages with specific failure reasons
- Health check endpoint at `/health`

### 2. Memory Optimization
- Single Gunicorn worker to reduce memory usage
- Lazy loading of model data
- Garbage collection after model loading
- Memory usage monitoring

### 3. Deployment Configuration
- Increased timeout to 180 seconds
- Added startup validation script
- Better resource allocation with paid plan

### 4. Validation Tools
- `test_model.py`: Local model validation script
- `start.sh`: Pre-deployment validation
- Health check endpoint for monitoring

## 🧪 Testing Your Deployment

### Local Testing:
```bash
# Test model loading
python test_model.py

# Test app locally
python app.py

# Check health endpoint
curl http://localhost:5000/health
```

### After Deployment:
```bash
# Check if model loads
curl https://your-app.onrender.com/health

# Test with a movie
curl -X POST https://your-app.onrender.com/about \
  -d "moviename=Inception" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

## ⚠️ If Still Failing

### Option 1: Use Free Plan with Optimizations
1. Remove `plan: starter` from `render.yaml`
2. The app will use the free tier (512MB RAM)
3. Model should still fit, but may be slower

### Option 2: Reduce Model Size
If the current model is too large:
1. Consider reducing the dataset size
2. Use more aggressive compression
3. Store model in external storage (e.g., S3) and download on startup

### Option 3: Check Render Logs
1. Go to your Render dashboard
2. Click on your service
3. Check the "Logs" tab for detailed error messages
4. Look for memory errors or timeout issues

## 📊 Resource Usage

| Component | Size | Memory | Impact |
|-----------|------|--------|---------|
| Model File | 18MB | 150MB | High |
| Flask App | - | 50MB | Medium |
| Dependencies | - | 80MB | Medium |
| **Total** | - | **280MB** | Should work on paid plan |

## 🚀 Deployment Steps

1. **Commit all changes**:
   ```bash
   git add .
   git commit -m "Fix deployment issues with enhanced error handling"
   git push
   ```

2. **Deploy on Render**:
   - Go to Render dashboard
   - Click "Manual Deploy" or push to trigger auto-deploy
   - Monitor logs for startup process

3. **Verify deployment**:
   - Check `/health` endpoint
   - Test with a movie search
   - Monitor memory usage in Render dashboard

## 🔍 Debugging Commands

```bash
# Check model file in deployment
ls -la model.pkl.gz

# Check memory usage
python -c "import psutil; print(f'Available: {psutil.virtual_memory().available/1024**3:.2f}GB')"

# Test model loading specifically
python -c "
import pickle, gzip
try:
    with gzip.open('model.pkl.gz', 'rb') as f:
        data = pickle.load(f)
    print('✅ Model loads OK')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

## 📞 Support

If you continue to have issues:
1. Check the Render logs for specific error messages
2. Verify your plan has enough resources
3. Consider using the model validation script before deployment
4. Monitor the health check endpoint after deployment