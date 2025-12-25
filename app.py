
import pandas as pd
import pickle
import gzip
from flask import Flask, render_template,request

def get_recommendations(title, cosine_sim):
    global result
    title=title.replace(' ','').lower()
    try:
        idx = indices[title]
    except KeyError:
        return None, None
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:11]
    movie_indices = [i[0] for i in sim_scores]
    result =  netflix_overall['title'].iloc[movie_indices]
    result = result.to_frame()
    result = result.reset_index()
    del result['index']
    
    # Get details of the searched movie
    movie_details = netflix_overall.iloc[idx]
    
    return result, movie_details

# Load the model and data from compressed pickle file
with gzip.open("model.pkl.gz",'rb') as file:
    model_data = pickle.load(file)
    cosine_sim2 = model_data['cosine_sim']
    indices = model_data['indices']
    netflix_overall = model_data['netflix_data']



app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/about',methods=['POST'])
def getvalue():
    try:
        moviename = request.form['moviename'].strip()
        if not moviename:
            return render_template('index.html', error=True, movie_name="", error_msg="Please enter a movie name")
        
        result, movie_details = get_recommendations(moviename, cosine_sim2)
        if result is None:
            return render_template('index.html', error=True, movie_name=moviename, error_msg=f"Movie '{moviename}' not found. Please try another title.")
        
        df = result
        df = df.rename(columns={'title': 'Recommended Title of Movies & Shows to watch on Netflix'})
        
        # Convert movie details to dictionary
        details = {
            'type': movie_details.get('type', 'N/A') if isinstance(movie_details, dict) else movie_details['type'] if 'type' in movie_details else 'N/A',
            'title': movie_details.get('title', 'N/A') if isinstance(movie_details, dict) else movie_details['title'] if 'title' in movie_details else 'N/A',
            'director': movie_details.get('director', 'N/A') if isinstance(movie_details, dict) else movie_details['director'] if 'director' in movie_details else 'N/A',
            'cast': movie_details.get('cast', 'N/A') if isinstance(movie_details, dict) else movie_details['cast'] if 'cast' in movie_details else 'N/A',
            'country': movie_details.get('country', 'N/A') if isinstance(movie_details, dict) else movie_details['country'] if 'country' in movie_details else 'N/A',
            'date_added': movie_details.get('date_added', 'N/A') if isinstance(movie_details, dict) else movie_details['date_added'] if 'date_added' in movie_details else 'N/A',
            'release_year': movie_details.get('release_year', 'N/A') if isinstance(movie_details, dict) else movie_details['release_year'] if 'release_year' in movie_details else 'N/A',
            'rating': movie_details.get('rating', 'N/A') if isinstance(movie_details, dict) else movie_details['rating'] if 'rating' in movie_details else 'N/A',
            'duration': movie_details.get('duration', 'N/A') if isinstance(movie_details, dict) else movie_details['duration'] if 'duration' in movie_details else 'N/A',
            'listed_in': movie_details.get('listed_in', 'N/A') if isinstance(movie_details, dict) else movie_details['listed_in'] if 'listed_in' in movie_details else 'N/A',
            'description': movie_details.get('description', 'N/A') if isinstance(movie_details, dict) else movie_details['description'] if 'description' in movie_details else 'N/A'
        }
        
        return render_template('result.html', tables=[df.to_html(classes='data', index=False)], titles=df.columns.values, movie_details=details)
    
    except Exception as e:
        return render_template('index.html', error=True, movie_name=request.form.get('moviename', ''), error_msg=f"Error: {str(e)}")

if __name__ == '__main__':
    app.run(debug=False)
