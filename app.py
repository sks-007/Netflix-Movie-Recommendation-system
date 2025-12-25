
import pandas as pd
import pickle
import gzip
import gc
import numpy as np
from flask import Flask, render_template, request
import os

# Global variables for lazy loading
_model_data = None

def load_model_data():
    """Lazy load model data to save memory on startup"""
    global _model_data
    if _model_data is None:
        try:
            model_path = os.path.join(os.path.dirname(__file__), 'model.pkl.gz')
            print(f"Attempting to load model from: {model_path}")
            print(f"File exists: {os.path.exists(model_path)}")
            
            with gzip.open(model_path, 'rb') as file:
                _model_data = pickle.load(file)
            
            print(f"Model loaded successfully!")
            print(f"Model keys: {list(_model_data.keys())}")
            
            # Force garbage collection after loading
            gc.collect()
        except Exception as e:
            print(f"Error loading model: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            _model_data = None
            return None
    
    return _model_data

def get_recommendations(title, cosine_sim):
    """Get movie recommendations based on cosine similarity"""
    global result
    
    # Load model data
    model_data = load_model_data()
    if model_data is None:
        return None, None
    
    indices = model_data['indices']
    netflix_overall = model_data['netflix_data']
    
    # Try different title formats to match with indices
    title_clean = title.replace(' ', '').lower()
    
    idx = None
    
    # Try exact match without spaces
    if title_clean in indices:
        idx = indices[title_clean]
    # Try with original spaces but lowercase
    elif title.lower() in indices:
        idx = indices[title.lower()]
    # Try searching in the dataframe for partial matches
    else:
        # Search for the title in the dataframe (case-insensitive)
        mask = netflix_overall['title'].str.lower().str.contains(title.lower(), case=False, na=False)
        if mask.any():
            idx = netflix_overall[mask].index[0]
        else:
            return None, None
    
    try:
        # Get cosine similarity scores for this movie
        sim_scores = list(enumerate(cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:11]
        movie_indices = [i[0] for i in sim_scores]
        
        result = netflix_overall['title'].iloc[movie_indices]
        result = result.to_frame()
        result = result.reset_index()
        del result['index']
        
        # Get details of the searched movie
        movie_details = netflix_overall.iloc[idx]
        
        return result, movie_details
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        import traceback
        traceback.print_exc()
        return None, None

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/about', methods=['POST'])
def getvalue():
    try:
        moviename = request.form['moviename'].strip()
        if not moviename:
            return render_template('index.html', error=True, movie_name="", error_msg="Please enter a movie name")
        
        model_data = load_model_data()
        if model_data is None:
            return render_template('index.html', error=True, movie_name=moviename, error_msg="Model loading error. Please try again later.")
        
        cosine_sim2 = model_data['cosine_sim']
        result, movie_details = get_recommendations(moviename, cosine_sim2)
        
        if result is None or movie_details is None:
            return render_template('index.html', error=True, movie_name=moviename, error_msg=f"'{moviename}' not found. Please check spelling or try another title.")
        
        df = result
        df = df.rename(columns={'title': 'Recommended Title of Movies & Shows to watch on Netflix'})
        
        # Convert movie details to dictionary - handle Series objects
        try:
            if hasattr(movie_details, 'to_dict'):
                details_dict = movie_details.to_dict()
            else:
                details_dict = dict(movie_details)
            
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
            print(f"Error converting movie details: {e}")
            details = {
                'type': 'N/A', 'title': moviename, 'director': 'N/A', 'cast': 'N/A',
                'country': 'N/A', 'date_added': 'N/A', 'release_year': 'N/A', 'rating': 'N/A',
                'duration': 'N/A', 'listed_in': 'N/A', 'description': 'N/A'
            }
        
        return render_template('result.html', tables=[df.to_html(classes='data', index=False)], titles=df.columns.values, movie_details=details)
    
    except Exception as e:
        print(f"Error in getvalue: {e}")
        import traceback
        traceback.print_exc()
        return render_template('index.html', error=True, movie_name=request.form.get('moviename', ''), error_msg=f"An error occurred: {str(e)}")

if __name__ == '__main__':
    app.run(debug=False)
