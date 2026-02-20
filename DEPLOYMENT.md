# Netflix Recommendation System - Production Deployment Guide

## 🚀 Quick Deployment to Render

### Prerequisites
1. **GitHub Repository**: https://github.com/sks-007/Netflix-Movie-Recommendation-system
2. **Render Account**: Sign up at https://render.com

### One-Click Deploy
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Manual Deployment Steps

#### 1. Connect Repository
- Go to [Render Dashboard](https://render.com/dashboard)
- Click "New +" → "Web Service"
- Connect your GitHub: `sks-007/Netflix-Movie-Recommendation-system`
- Branch: `master`

#### 2. Configuration (Auto-configured via render.yaml)
- **Name**: `netflix-recommendation`
- **Runtime**: `Python 3.11`
- **Build Command**: Auto-configured
- **Start Command**: `bash start.sh`
- **Plan**: Starter ($7/month for optimal performance)

#### 3. Environment Variables (Auto-set)
All environment variables are pre-configured in `render.yaml`:
- `PYTHONUNBUFFERED=1`
- `FLASK_ENV=production`
- `GUNICORN_TIMEOUT=300`
- `MODEL_LOAD_TIMEOUT=120`
- `WEB_CONCURRENCY=1`

#### 4. Monitor Deployment
- Watch build logs for: `✅ Model validation PASSED`
- Monitor startup logs for: `✅ Model loaded successfully`
- Check health endpoint: `https://your-app.onrender.com/health`

---

## 🏗️ Production Features

### Performance Optimizations
- **Caching**: LRU cache for 128 recent searches
- **Memory Management**: Single worker, optimized model loading
- **Health Monitoring**: `/health` and `/metrics` endpoints
- **Error Handling**: Comprehensive error tracking and recovery

### Monitoring Endpoints

#### Health Check
```bash
GET /health
```
**Response**:
```json
{
  "status": "healthy",
  "model_available": true,
  "uptime_seconds": 3600,
  "dataset_size": 6234,
  "cache_info": {
    "hits": 45,
    "misses": 12,
    "hit_rate": 78.95
  }
}
```

#### Metrics (Prometheus Format)
```bash
GET /metrics
```
**Response**:
```
app_uptime_seconds 3600.00
model_available{model="netflix"} 1
dataset_size{model="netflix"} 6234
cache_hits_total{cache="recommendations"} 45
```

### Production Specifications
- **Model Size**: 18.21 MB (compressed) → ~150 MB (memory)
- **Dataset**: 6,234 Netflix titles
- **Memory Usage**: ~280 MB total
- **Startup Time**: 30-60 seconds (first request)
- **Response Time**: <2 seconds (cached), <10 seconds (new searches)

---

## 🧪 Testing Your Deployment

### Local Testing
```bash
# Validate model
python test_model.py

# Test startup
bash start.sh

# Test health endpoint
curl http://localhost:8000/health
```

### Production Testing
```bash
# Health check
curl https://your-app.onrender.com/health

# Movie search
curl -X POST https://your-app.onrender.com/about \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "moviename=Inception"
```

### Sample Movie Searches
Try these popular titles:
- **Inception** - Christopher Nolan's sci-fi thriller
- **Stranger Things** - Popular Netflix series  
- **Avatar** - James Cameron's epic
- **The Godfather** - Classic crime drama
- **Interstellar** - Space exploration drama

---

## 📊 Performance Benchmarks

### Resource Usage (Production)
| Component | Memory | CPU | Disk |
|-----------|--------|-----|------|
| Flask App | 80 MB | 5% | - |
| Model Data | 150 MB | - | 18 MB |
| Dependencies | 50 MB | 5% | 200 MB |
| **Total** | **280 MB** | **10%** | **220 MB** |

### Response Times
| Operation | Cold Start | Warm (Cached) | Notes |
|-----------|------------|---------------|--------|
| Health Check | 50ms | 10ms | Always fast |
| Model Loading | 30-60s | - | First request only |
| Movie Search | 8-15s | 1-3s | Depends on similarity calculation |
| Cached Search | - | 100ms | LRU cache hit |

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Model Loading Fails
**Symptoms**: Health endpoint returns `model_available: false`
**Solutions**:
- Check Render logs for memory errors
- Verify model file size (should be 18.21 MB)
- Consider upgrading to Starter plan ($7/month)

#### 2. Timeout Errors
**Symptoms**: 504 Gateway Timeout on first request
**Solutions**:
- Wait 60 seconds for model loading
- Check `/health` endpoint status
- Review build logs for errors

#### 3. Memory Errors
**Symptoms**: App crashes or restarts frequently
**Solutions**:
- Use Starter plan for 1GB RAM
- Monitor `/metrics` endpoint
- Check for memory leaks in logs

### Debug Commands
```bash
# View deployment logs
render logs -s your-service-name

# Force redeploy
render deploy -s your-service-name

# Check service status
render services list
```

### Log Analysis
Look for these success indicators:
- `✅ Model validation PASSED`
- `✅ Model loaded successfully`
- `🚀 Starting Gunicorn server`
- `model_available: true` in health check

---

## 🔄 Updates & Maintenance

### Deploying Updates
1. Push changes to GitHub
2. Render auto-deploys from `master` branch
3. Monitor deployment in Render dashboard
4. Verify health endpoints post-deployment

### Cache Management
- Cache automatically expires old entries
- View cache statistics at `/health`
- Cache hit rate should be >70% for optimal performance

### Model Updates
To update the recommendation model:
1. Replace `model.pkl.gz` in repository
2. Run `python test_model.py` locally
3. Commit and push changes
4. Monitor deployment logs

---

## 📞 Support & Resources

### Links
- **Live Demo**: https://your-app.onrender.com
- **GitHub**: https://github.com/sks-007/Netflix-Movie-Recommendation-system
- **Health Check**: https://your-app.onrender.com/health
- **Metrics**: https://your-app.onrender.com/metrics

### Documentation
- [Render Docs](https://render.com/docs)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/settings.html)

### Configuration Files
- `render.yaml` - Render deployment configuration
- `start.sh` - Production startup script
- `test_model.py` - Model validation script
- `requirements.txt` - Python dependencies

---

## 🎯 Production Checklist

✅ **Pre-Deployment**:
- [ ] Model file exists and loads (`python test_model.py`)
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Environment variables configured
- [ ] Repository cleaned of large unnecessary files

✅ **Deployment**:
- [ ] Connected to GitHub repository
- [ ] Selected `master` branch
- [ ] Used Starter plan for optimal performance
- [ ] Environment variables auto-configured

✅ **Post-Deployment**:
- [ ] Health endpoint returns 200 (`/health`)
- [ ] Model shows as available
- [ ] Successfully process movie searches
- [ ] Monitor performance metrics (`/metrics`)

---

*🎬 Built with ❤️ for Netflix movie lovers worldwide. Enjoy discovering your next binge-watch!*