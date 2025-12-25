"""
Netflix Movie Recommendation System - Flask Application
Recommends movies based on content similarity
"""

import pandas as pd
import pickle
import gzip
import gc
import numpy as np
from flask import Flask, render_template, request
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Global variables for lazy loading
_model_data = None

def load_model_data():
    """Lazy load model data to save memory on startup"""
    global _model_data
    
    if _model_data is not None:
        return _model_data
    
    try:
        # Get absolute path to model file
        app_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(app_dir, 'model.pkl.gz')
        
        logger.info(f"Loading model from: {model_path}")
        
        if not os.path.exists(model_path):
            logger.error(f"Model file not found: {model_path}")
            logger.error(f"Files in directory: {os.listdir(app_dir)}")
            return None
        
        file_size_mb = os.path.getsize(model_path) / (1024 * 1024)
        logger.info(f"Model file size: {file_size_mb:.2f} MB")
        
        with gzip.open(model_path, 'rb') as file:
            _model_data = pickle.load(file)
        
        logger.info("Model loaded successfully!")
        logger.info(f"Model keys: {list(_model_data.keys())}")
        logger.info(f"Cosine matrix dtype: {_model_data['cosine_sim'].dtype}")
        logger.info(f"Cosine matrix shape: {_model_data['cosine_sim'].shape}")
        logger.info(f"Dataset shape: {_model_data['netflix_data'].shape}")
        logger.info(f"Number of titles: {len(_model_data['indices'])}")
        
        gc.collect()
        logger.info("Garbage collection completed")
        
        return _model_data
        
    except Exception as e:
        logger.error(f"Error loading model: {type(e).__name__}: {e}", exc_info=True)
        _model_data = None
        return None


def get_recommendations(title, cosine_sim):
    """Get movie recommendations based on cosine similarity"""
    
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
        
        # Load model and get recommendations
        model_data = load_model_data()
        if model_data is None:
            logger.error("Model failed to load")
            return render_template('index.html',
                                 error=True,
                                 movie_name=moviename,
                                 error_msg="System error: Could not load recommendation model. Please try again later.")
        
        cosine_sim = model_data['cosine_sim']
        result_df, movie_details = get_recommendations(moviename, cosine_sim)
        
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
    app.run(debug=False, host='0.0.0.0', port=port)
