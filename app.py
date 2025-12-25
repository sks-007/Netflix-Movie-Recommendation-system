
import pandas as pd
import pickle
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

# Load the model and data from pickle file
with open("model.pkl",'rb') as file:
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
    moviename = request.form['moviename']
    result, movie_details = get_recommendations(moviename,cosine_sim2)
    if result is None:
        return render_template('index.html', error=True, movie_name=request.form['moviename'])
    df=result
    df = df.rename(columns={'title': 'Recommended Title of Movies & Shows to watch on Netflix'})
    
    # Convert movie details to dictionary
    details = {
        'type': movie_details.get('type', 'N/A'),
        'title': movie_details.get('title', 'N/A'),
        'director': movie_details.get('director', 'N/A'),
        'cast': movie_details.get('cast', 'N/A'),
        'country': movie_details.get('country', 'N/A'),
        'date_added': movie_details.get('date_added', 'N/A'),
        'release_year': movie_details.get('release_year', 'N/A'),
        'rating': movie_details.get('rating', 'N/A'),
        'duration': movie_details.get('duration', 'N/A'),
        'listed_in': movie_details.get('listed_in', 'N/A'),
        'description': movie_details.get('description', 'N/A')
    }
    
    return render_template('result.html',  tables=[df.to_html(classes='data', index=False)], titles=df.columns.values, movie_details=details)

if __name__ == '__main__':
    app.run(debug=False)
