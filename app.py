"""
Netflix Movie Recommendation System - Flask Application
Recommends movies based on content similarity
"""

import pandas as pd
import pickle
import gzip
import gc
import numpy as np
from flask import Flask, render_template, request, jsonify, make_response
import os
import sys
import logging
import signal
import threading
import time
from functools import lru_cache
from datetime import datetime

# Configure optimized logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)
logger.info(f"Starting Netflix Recommendation System v2.0 - {datetime.now()}")

# Global variables for optimized model management
_model_data = None
_model_loading = False
_model_lock = threading.Lock()  # Thread safety
_app_startup_time = time.time()

# Production configuration
MAX_MODEL_SIZE_MB = 50
MODEL_LOAD_TIMEOUT = int(os.environ.get('MODEL_LOAD_TIMEOUT', 120))
CACHE_SIZE = 128  # Cache recent searches

def load_model_data():
    """Lazy load model data with enhanced error handling and memory management"""
    global _model_data, _model_loading
    
    if _model_data is not None:
        return _model_data
    
    # Prevent concurrent loading attempts
    if _model_loading:
        logger.info("Model loading already in progress, waiting...")
        import time
        for _ in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            if _model_data is not None:
                return _model_data
        logger.error("Model loading timeout")
        return None
    
    _model_loading = True
    
    try:
        # Get absolute path to model file
        app_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(app_dir, 'model.pkl.gz')
        
        logger.info(f"Loading model from: {model_path}")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"App directory: {app_dir}")
        
        if not os.path.exists(model_path):
            logger.error(f"Model file not found: {model_path}")
            try:
                files_in_dir = os.listdir(app_dir)
                logger.error(f"Files in directory: {files_in_dir}")
                # Look for any .pkl or .gz files
                model_files = [f for f in files_in_dir if f.endswith(('.pkl', '.pkl.gz', '.gz'))]
                logger.error(f"Model-related files found: {model_files}")
            except Exception as list_error:
                logger.error(f"Error listing directory: {list_error}")
            return None
        
        # Check file size and accessibility
        try:
            file_size_mb = os.path.getsize(model_path) / (1024 * 1024)
            logger.info(f"Model file size: {file_size_mb:.2f} MB")
            
            if file_size_mb > MAX_MODEL_SIZE_MB:
                logger.error(f"Model file too large: {file_size_mb:.2f} MB (max: {MAX_MODEL_SIZE_MB} MB)")
                return None
                
            # Check file permissions
            if not os.access(model_path, os.R_OK):
                logger.error(f"No read permission for model file: {model_path}")
                return None
                
        except Exception as size_error:
            logger.error(f"Error checking model file: {size_error}")
            return None
        
        # Load the model with timeout protection
        logger.info("Starting model loading...")
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Model loading exceeded {MODEL_LOAD_TIMEOUT} seconds")
        
        # Set up timeout (Unix-like systems)
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(MODEL_LOAD_TIMEOUT)
        except (AttributeError, ValueError):
            # Windows doesn't support SIGALRM
            logger.info("Timeout protection not available on this platform")
        
        try:
            with gzip.open(model_path, 'rb') as file:
                _model_data = pickle.load(file)
        finally:
            try:
                signal.alarm(0)  # Disable the alarm
            except (AttributeError, ValueError):
                pass
        
        # Validate loaded data
        if _model_data is None:
            logger.error("Loaded model data is None")
            return None
            
        if not isinstance(_model_data, dict):
            logger.error(f"Invalid model data type: {type(_model_data)}")
            return None
            
        required_keys = ['cosine_sim', 'netflix_data', 'indices']
        missing_keys = [key for key in required_keys if key not in _model_data]
        if missing_keys:
            logger.error(f"Missing required keys in model: {missing_keys}")
            return None
        
        logger.info("Model loaded successfully!")
        logger.info(f"Model keys: {list(_model_data.keys())}")
        
        # Log model details with error handling
        try:
            logger.info(f"Cosine matrix dtype: {_model_data['cosine_sim'].dtype}")
            logger.info(f"Cosine matrix shape: {_model_data['cosine_sim'].shape}")
            logger.info(f"Dataset shape: {_model_data['netflix_data'].shape}")
            logger.info(f"Number of titles: {len(_model_data['indices'])}")
        except Exception as detail_error:
            logger.warning(f"Error logging model details: {detail_error}")
        
        # Force garbage collection
        gc.collect()
        logger.info("Model loading completed with garbage collection")
        
        return _model_data
        
    except TimeoutError as e:
        logger.error(f"Model loading timeout: {e}")
        _model_data = None
        return None
    except MemoryError as e:
        logger.error(f"Memory error loading model: {e}")
        logger.error("Try reducing model size or upgrading server resources")
        _model_data = None
        return None
    except Exception as e:
        logger.error(f"Error loading model: {type(e).__name__}: {e}", exc_info=True)
        _model_data = None
        return None
    finally:
        _model_loading = False


@lru_cache(maxsize=CACHE_SIZE)
def cached_get_recommendations(title_lower):
    """Cached recommendation function for performance"""
    # Call the actual recommendation function
    model_data = load_model_data()
    if model_data is None:
        return None, None
    
    cosine_sim = model_data['cosine_sim']
    return get_recommendations_internal(title_lower, cosine_sim)


def get_recommendations_internal(title, cosine_sim):
    """Internal recommendation function (called by cached version)"""
    model_data = load_model_data()
    if model_data is None:
        logger.error("Model data not available")
        return None, None
    
    try:
        indices = model_data['indices']
        netflix_overall = model_data['netflix_data']
        
        logger.info(f"Searching for: '{title}'")
        
        # Try different title matching strategies
        title_clean = title.replace(' ', '').lower()
        idx = None
        matched_title = None
        
        # Strategy 1: Exact match without spaces
        if title_clean in indices:
            idx = indices[title_clean]
            matched_title = "exact match (no spaces)"
            logger.info(f"Found: {matched_title}")
        
        # Strategy 2: Exact match with spaces (lowercase)
        elif title.lower() in indices:
            idx = indices[title.lower()]
            matched_title = "exact match (with spaces)"
            logger.info(f"Found: {matched_title}")
        
        # Strategy 3: Partial/fuzzy match in dataframe
        else:
            mask = netflix_overall['title'].str.lower().str.contains(
                title.lower(), case=False, na=False, regex=False
            )
            if mask.any():
                # Get the first match
                matched_idx = netflix_overall[mask].index[0]
                idx = matched_idx
                matched_title = "fuzzy match in dataframe"
                logger.info(f"Found: {matched_title} - Index: {idx}")
            else:
                logger.warning(f"Title '{title}' not found in any format")
                return None, None
        
        if idx is None:
            logger.error("Could not find title index")
            return None, None
        
        # Get cosine similarity scores
        logger.info(f"Getting recommendations for index {idx}")
        sim_scores = list(enumerate(cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        # Get top 10 (excluding the movie itself at index 0)
        sim_scores = sim_scores[1:11]
        movie_indices = [int(i[0]) for i in sim_scores]
        
        logger.info(f"Got {len(movie_indices)} recommendations")
        
        # Get recommendation titles
        recommendations = netflix_overall['title'].iloc[movie_indices]
        result_df = recommendations.to_frame()
        result_df = result_df.reset_index()
        
        if 'index' in result_df.columns:
            del result_df['index']
        
        # Get searched movie details
        movie_details = netflix_overall.iloc[idx]
        
        logger.info("Successfully generated recommendations")
        return result_df, movie_details
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}", exc_info=True)
        return None, None


def get_recommendations(title, cosine_sim=None):
    """Public API for getting recommendations with caching"""
    # Use cached version for better performance
    title_lower = title.lower().strip()
    return cached_get_recommendations(title_lower)


# Initialize Flask app
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configure Flask
app.config['ENV'] = 'production'
app.config['DEBUG'] = False
app.config['JSON_SORT_KEYS'] = False

logger.info(f"Flask app initialized - Working directory: {os.getcwd()}")
logger.info(f"Templates folder: {app.template_folder}")
logger.info(f"Static folder: {app.static_folder}")


@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')


@app.route('/health')
def health_check():
    """Comprehensive health check endpoint for production monitoring"""
    try:
        uptime = time.time() - _app_startup_time
        
        # Basic health info
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': round(uptime, 2),
            'uptime_human': f"{int(uptime//3600)}h {int((uptime%3600)//60)}m {int(uptime%60)}s",
            'model_status': 'unknown',
            'model_available': False,
            'cache_info': {
                'hits': 0,
                'misses': 0,
                'maxsize': CACHE_SIZE,
                'currsize': 0
            }
        }
        
        # Check model availability (quick test)
        try:
            model_data = load_model_data()
            if model_data is not None:
                health_data.update({
                    'model_status': 'loaded',
                    'model_available': True,
                    'dataset_size': len(model_data['netflix_data']) if 'netflix_data' in model_data else 0,
                    'matrix_shape': list(model_data['cosine_sim'].shape) if 'cosine_sim' in model_data else [],
                    'total_indices': len(model_data['indices']) if 'indices' in model_data else 0
                })
            else:
                health_data.update({
                    'model_status': 'failed_to_load',
                    'model_available': False
                })
        except Exception as model_error:
            health_data.update({
                'model_status': 'error',
                'model_available': False,
                'model_error': str(model_error)
            })
        
        # Cache statistics
        try:
            cache_info = cached_get_recommendations.cache_info()
            health_data['cache_info'] = {
                'hits': cache_info.hits,
                'misses': cache_info.misses,
                'maxsize': cache_info.maxsize,
                'currsize': cache_info.currsize,
                'hit_rate': round(cache_info.hits / (cache_info.hits + cache_info.misses) * 100, 2) if (cache_info.hits + cache_info.misses) > 0 else 0
            }
        except Exception:
            pass
        
        # System resources (if available)
        try:
            import psutil
            memory = psutil.virtual_memory()
            health_data['system'] = {
                'memory_percent': memory.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'cpu_percent': psutil.cpu_percent(interval=None)
            }
        except (ImportError, Exception):
            health_data['system'] = {'status': 'monitoring_unavailable'}
        
        status_code = 200 if health_data['model_available'] else 503
        response = make_response(jsonify(health_data), status_code)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        error_response = {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'model_available': False
        }
        return make_response(jsonify(error_response), 500)


@app.route('/metrics')
def metrics():
    """Prometheus-style metrics endpoint"""
    try:
        uptime = time.time() - _app_startup_time
        model_data = load_model_data()
        
        metrics_data = [
            f'app_uptime_seconds {uptime:.2f}',
            f'model_available {{model="netflix"}} {1 if model_data else 0}',
        ]
        
        if model_data:
            metrics_data.extend([
                f'dataset_size {{model="netflix"}} {len(model_data["netflix_data"])}',
                f'cosine_matrix_size {{model="netflix"}} {model_data["cosine_sim"].shape[0]}'
            ])
        
        try:
            cache_info = cached_get_recommendations.cache_info()
            metrics_data.extend([
                f'cache_hits_total {{cache="recommendations"}} {cache_info.hits}',
                f'cache_misses_total {{cache="recommendations"}} {cache_info.misses}',
                f'cache_size {{cache="recommendations"}} {cache_info.currsize}'
            ])
        except Exception:
            pass
        
        response = make_response('\n'.join(metrics_data) + '\n', 200)
        response.headers['Content-Type'] = 'text/plain; version=0.0.4'
        return response
        
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        return make_response('# Error generating metrics\n', 500)


@app.route('/about', methods=['POST'])
def getvalue():
    """Search and recommendation route"""
    try:
        moviename = request.form.get('moviename', '').strip()
        
        if not moviename:
            logger.warning("Empty movie name provided")
            return render_template('index.html', 
                                 error=True, 
                                 movie_name="", 
                                 error_msg="Please enter a movie/show name")
        
        logger.info(f"Processing search request for: {moviename}")
        
        # Load model and get recommendations with enhanced error handling
        model_data = load_model_data()
        if model_data is None:
            logger.error("Model failed to load - providing detailed error message")
            
            # Try to provide more specific error information
            error_details = []
            app_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(app_dir, 'model.pkl.gz')
            
            if not os.path.exists(model_path):
                error_details.append("Model file not found in deployment")
            else:
                try:
                    file_size = os.path.getsize(model_path) / (1024 * 1024)
                    error_details.append(f"Model file exists ({file_size:.1f}MB) but failed to load")
                except:
                    error_details.append("Model file exists but cannot read size")
            
            logger.error(f"Error details: {'; '.join(error_details)}")
            
            return render_template('index.html',
                                 error=True,
                                 movie_name=moviename,
                                 error_msg="System error: Could not load recommendation model. Please try again later.")
        
        # Get recommendations using the new cached API
        result_df, movie_details = get_recommendations(moviename)
        
        if result_df is None or movie_details is None:
            logger.warning(f"No recommendations found for: {moviename}")
            return render_template('index.html',
                                 error=True,
                                 movie_name=moviename,
                                 error_msg=f"Sorry, '{moviename}' not found. Please check spelling and try another title.")
        
        # Prepare dataframe
        df = result_df.copy()
        df = df.rename(columns={'title': 'Recommended Titles'})
        
        # Prepare movie details
        try:
            details_dict = movie_details.to_dict() if hasattr(movie_details, 'to_dict') else dict(movie_details)
            details = {
                'type': str(details_dict.get('type', 'N/A')),
                'title': str(details_dict.get('title', 'N/A')),
                'director': str(details_dict.get('director', 'N/A')),
                'cast': str(details_dict.get('cast', 'N/A')),
                'country': str(details_dict.get('country', 'N/A')),
                'date_added': str(details_dict.get('date_added', 'N/A')),
                'release_year': str(details_dict.get('release_year', 'N/A')),
                'rating': str(details_dict.get('rating', 'N/A')),
                'duration': str(details_dict.get('duration', 'N/A')),
                'listed_in': str(details_dict.get('listed_in', 'N/A')),
                'description': str(details_dict.get('description', 'N/A'))
            }
        except Exception as e:
            logger.error(f"Error processing movie details: {e}", exc_info=True)
            details = {k: 'N/A' for k in ['type', 'title', 'director', 'cast', 'country', 
                                          'date_added', 'release_year', 'rating', 'duration', 
                                          'listed_in', 'description']}
        
        logger.info(f"Returning results page for: {moviename}")
        return render_template('result.html',
                             tables=[df.to_html(classes='data table table-striped', index=False)],
                             titles=df.columns.values,
                             movie_details=details)
    
    except Exception as e:
        logger.error(f"Error in search route: {e}", exc_info=True)
        return render_template('index.html',
                             error=True,
                             movie_name=request.form.get('moviename', ''),
                             error_msg=f"An error occurred: {str(e)}")


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.warning(f"404 error: {error}")
    return render_template('index.html',
                         error=True,
                         error_msg="Page not found"), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {error}", exc_info=True)
    return render_template('index.html',
                         error=True,
                         error_msg="Server error occurred. Please try again later."), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting app on port {port}")
    
    # Pre-load model in development for faster testing
    if os.environ.get('FLASK_ENV') != 'production':
        logger.info("Pre-loading model for development...")
        model_data = load_model_data()
        if model_data:
            logger.info("Model pre-loaded successfully")
        else:
            logger.warning("Model pre-loading failed")
    
    app.run(debug=False, host='0.0.0.0', port=port)
