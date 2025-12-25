# Netflix Recommendation System 

A content-based recommendation system built with Flask that suggests similar movies and TV shows based on user input. The system analyzes Netflix content using machine learning algorithms to provide personalized recommendations.

##  Features

- **Content-Based Filtering**: Uses cosine similarity to recommend similar titles based on multiple features
- **Detailed Movie Information**: Displays comprehensive details about the searched movie/show including cast, director, genre, rating, and description
- **Top 10 Recommendations**: Provides 10 similar titles based on the search query
- **User-Friendly Interface**: Clean and intuitive web interface with responsive design
- **Error Handling**: Graceful handling of invalid or non-existent titles with helpful feedback
- **Real-Time Search**: Instant recommendations upon submission

##  Technology Stack

### Backend
- **Python 3.x**
- **Flask**: Web framework for building the application
- **Pandas**: Data manipulation and analysis
- **Scikit-learn**: Machine learning library for recommendation algorithm
  - `CountVectorizer`: For text feature extraction
  - `cosine_similarity`: For computing similarity between items

### Frontend
- **HTML5**: Structure and content
- **CSS3**: Styling and responsive design
- **Jinja2**: Template engine for dynamic content rendering

### Dataset
- **netflix_titles.csv**: Contains Netflix movies and TV shows data with the following fields:
- **Source of Data** : https://www.kaggle.com/datasets/shivamb/netflix-shows
  - show_id, type, title, director, cast, country, date_added, release_year, rating, duration, listed_in, description

##  How It Works

### Recommendation Algorithm

1. **Data Preprocessing**:
   - Loads Netflix dataset from CSV file
   - Fills missing values with empty strings
   - Cleans text data by converting to lowercase and removing spaces

2. **Feature Engineering**:
   - Creates a "soup" by combining multiple features:
     - Title
     - Director
     - Cast
     - Genre (listed_in)
     - Description

3. **Vectorization**:
   - Uses `CountVectorizer` with English stop words to convert text into numerical vectors
   - Creates a count matrix from the combined features

4. **Similarity Calculation**:
   - Computes cosine similarity between all items in the dataset
   - Generates a similarity matrix for all movies/shows

5. **Recommendation Generation**:
   - Finds the index of the searched title
   - Retrieves similarity scores for all other items
   - Sorts by similarity score in descending order
   - Returns top 10 most similar titles

## Project Structure

```
Netflix-Recommendation-System/
│
├── app.py                          # Main Flask application
├── netflix_titles.csv              # Netflix dataset
├── Content Based NRC.ipynb         # Jupyter notebook with algorithm exploration
├── README.md                       # Project documentation
│
├── templates/                      # HTML templates
│   ├── index.html                  # Home page with search form
│   ├── result.html                 # Results page with recommendations
│   └── result.html.bak             # Backup file
│
└── static/                         # Static files
    ├── stylesheets/
    │   ├── style.css               # Styling for home page
    │   ├── result.css              # Styling for results page
    │   ├── result.css.bak          # Backup file
    └── images/
        └── netflix.webp            # Netflix logo/image
```

##  Usage

1. **Open the Application**: Navigate to `http://127.0.0.1:5000/` in your web browser

2. **Search for a Title**: Enter the exact name of a Netflix movie or TV show (e.g., "Stranger Things", "Breaking Bad", "The Crown")

3. **View Details**: The results page shows:
   - Complete details of the searched title
   - Type (Movie/TV Show)
   - Director and cast information
   - Release year and rating
   - Genre and description
   - 10 recommended similar titles

4. **Get More Recommendations**: Click "Search Again" to find recommendations for another title

##  Example

**Input**: "Stranger Things"

**Output**: 
- Displays full details of Stranger Things (cast, director, genre, description, etc.)
- Recommends 10 similar titles such as:
  - Dark
  - The Umbrella Academy
  - Locke & Key
  - The OA
  - And more...

##  Key Functions

### `clean_data(x)`
Cleans text data by converting to lowercase and removing spaces.

### `create_soup(x)`
Combines multiple features (title, director, cast, genre, description) into a single string for analysis.

### `get_recommendations(title, cosine_sim)`
Main recommendation function that:
- Finds the title in the dataset
- Calculates similarity scores
- Returns top 10 recommendations and movie details
- Handles errors for non-existent titles

##  Known Limitations

- Requires exact title match (case-insensitive, spaces removed)
- Dataset is static and needs manual updates for new Netflix content
- Recommendations are based solely on content features, not user ratings or viewing history
- Performance may vary with very large datasets

**Note**: This is an educational project and is not affiliated with or endorsed by Netflix, Inc.



