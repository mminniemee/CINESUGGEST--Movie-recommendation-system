import streamlit as st
import pandas as pd
from joblib import load
import requests
import sqlite3
import ast
import uuid
from googleapiclient.discovery import build

st.set_page_config(
    page_icon="🌟",
)

st.markdown(
    """
    <style>
    
    /* Sidebar background color */
    section[data-testid="stSidebar"] {
        background-color:#D01334;
        color:#f7f2f3;  

    }

    section[data-testid="stSidebar"] * {
        color: white;
    }

    /* Specific adjustments for sliders and dropdown labels in the sidebar */
    section[data-testid="stSidebar"] label {
        color: white; /* Ensures labels within sidebar widgets are white */
    }
    
    .stSelectbox {
        color: #FFFFFF;  /* Text color */
    }
    h1, h2, h3, h4, h5, h6 {
            color: #FFFFFF;  # Bright white color for all headers (including title)
        }
    .css-1d391kg {
            color: #FFFFFF;  # Bright white color for sidebar text
        }

    div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
        color: #FFFFFF;
    }

    div[data-testid="stTextInput"] label,
    div[data-testid="stSelectbox"] label {
        color: white; /* Change to desired color */
        font-weight: bold;
    }
    .stApp {
        color:#FFFFFF;
        background-color: #0F0B14;  
    }

    /* Sidebar Slider customization */
    .stSidebar.stSlider>div>div>input[type="range"] {
            background: #0d0d0d;  /* Change slider color to white */
            border-radius: 5px;
            height: 8px;  /* Adjust slider height */
        }
    
    /* Container background color */
    .custom-container {
        background-color: #D01334;
        padding: 10px;
        border-radius: 10px;
        color: #FFFFFF;
    }
    header[data-testid="stHeader"] {
        background-color: #0F0B14;
        }
    

    /* Button styling */
    .stButton>button {
        color: #F1F2F7;  /* Button text color */
        background-color: #262425;  /* Button background color */
        border-radius: 5px;  /* Rounded corners */
        border: none;  /* Remove border */
        padding: 8px 20px;  /* Padding for button */
        font-size: 16px;  /* Font size for button text */
    }

    /* Button hover effect */
    .stButton>button:hover {
        color: white;  /* Button text color */
        background-color: #D62639;  /* Darker shade for hover effect */
        transition: 0.3s;  /* Smooth transition for hover */
    }

    div[data-baseweb="select"] > div {
        background-color: #D62639;  /* Inner background color of dropdown */
        color: white;  /* Text color */
    }

    .special-button button {
        background-color: #FF3D5A;  /* Unique color for this button */
        color: white;
        border-radius: 5px;
        font-size: 16px;
    }

    .stRadio>div>label {
            color: #0F0B14;  /* Change radio button text color to white */
        }

    </style>
    """,
    unsafe_allow_html=True
)
# Load similarity data and dataset
sparse_cosine_sim = load('C:\\Users\\Admin\\Desktop\\college\\Movie\\sparse_cosine_sim.joblib')
@st.cache_data
def load_data():
    # Load the dataset only once and reuse it across reruns
    data = pd.read_csv('C:\\Users\\Admin\\Desktop\\college\\Movie\\final_dataset.csv', usecols=['movieId','genres','primaryTitle','startYear','actors','directors'])
    return data

# Use the cached function to load the data
data2 = load_data()

# Preprocess 'directors' column to convert string representation of list to actual list
data2['directors'] = data2['directors'].apply(lambda x: ast.literal_eval(x)[0] if pd.notnull(x) else '')

# Preprocess 'actors' column to convert comma-separated string to list
data2['actors'] = data2['actors'].apply(lambda x: [actor.strip() for actor in x.split(',')] if pd.notnull(x) else [])

# Initialize session state for user and page
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# Function to change pages
def set_page(page_name):
    st.session_state.page = page_name

# Sidebar Navigation Buttons


# Database connection
def get_db_connection():
    conn = sqlite3.connect('movie.db')
    conn.row_factory = sqlite3.Row
    return conn

# User management functions
def create_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (user_name, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_name = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

# Add movie to favorites
def add_to_favorites(user_id, movie_id, title):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO favourites (user_id, movie_id, movie_title) VALUES (?, ?, ?)", (user_id, movie_id, title))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"An error occurred: {e}")
        return False
    finally:
        conn.close()

# Add movie to watchlist
def add_to_watchlist(user_id, movie_id, title):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO watchlist (user_id, movie_id, movie_title) VALUES (?, ?, ?)", (user_id, movie_id, title))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"An error occurred: {e}")
        return False
    finally:
        conn.close()

# Retrieve favorites and watchlist for user
def get_favorites(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT movie_id, movie_title FROM favourites WHERE user_id = ?", (user_id,))
    favorites = cursor.fetchall()
    conn.close()
    return favorites

def get_watchlist(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT movie_id, movie_title FROM watchlist WHERE user_id = ?", (user_id,))
    watchlist = cursor.fetchall()
    conn.close()
    return watchlist

def get_youtube_trailer(movie_title, year):
    api_key = "AIzaSyBhulZyKJIBadDyBA_BPV5U8LjuwSjrH3I"  # Replace with your YouTube API key
    youtube = build("youtube", "v3", developerKey=api_key)

    # Search query
    query = f"{movie_title} {year} trailer"

    # Search request
    request = youtube.search().list(
        part="snippet",
        q=query,
        maxResults=1,
        type="video"
    )
    response = request.execute()

    # Debugging: Check the response
    print(f"API Response: {response}")
    # Extract trailer link
    if response["items"]:
        video_id = response["items"][0]["id"]["videoId"]
        trailer_url = f"https://www.youtube.com/watch?v={video_id}"
        return trailer_url
    else:
        return None
    
# OMDb API function for movie posters
def get_movie_poster_omdb(title, year=None):
    api_key = "44b3405b"  # Replace with your OMDb API key
    url = f"http://www.omdbapi.com/?t={title}&y={year}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    if data.get("Response") == "True" and data.get("Poster") != "N/A":
        return data["Poster"]
    return None

def remove_from_favourites(user_id, movie_id):
    # Connect to the database
    conn = sqlite3.connect("movie.db")
    cursor = conn.cursor()
    
    # Execute SQL command to delete the movie from favourites
    cursor.execute("DELETE FROM favourites WHERE user_id = ? AND movie_id = ?", (user_id, movie_id))
    
    # Commit and close the connection
    conn.commit()
    conn.close()

def remove_from_watchlist(user_id, movie_id):
    # Connect to the database
    conn = sqlite3.connect("movie.db")
    cursor = conn.cursor()
    
    # Execute SQL command to delete the movie from watchlist
    cursor.execute("DELETE FROM watchlist WHERE user_id = ? AND movie_id = ?", (user_id, movie_id))
    
    # Commit and close the connection
    conn.commit()
    conn.close()

# Search by Actor Function
def search_by_actor(actor_name):
    # Filter movies that have the actor
    filtered_movies = data2[data2['actors'].apply(lambda x: actor_name in x)]
    recommendations = []
    for _, row in filtered_movies.iterrows():
        movie_title = row['primaryTitle']
        movie_year = row['startYear']
        movie_id = row['movieId']
        poster_url = get_movie_poster_omdb(movie_title, movie_year)
        recommendations.append({
            "movie_id": movie_id,
            "title": movie_title,
            "year": movie_year,
            "genre": row['genres'],
            "poster": poster_url
        })
    return recommendations

# Search by Director Function
def search_by_director(director_name):
    # Filter movies that have the director
    filtered_movies = data2[data2['directors'] == director_name]
    recommendations = []
    for _, row in filtered_movies.iterrows():
        movie_title = row['primaryTitle']
        movie_year = row['startYear']
        movie_id = row['movieId']
        poster_url = get_movie_poster_omdb(movie_title, movie_year)
        recommendations.append({
            "movie_id": movie_id,
            "title": movie_title,
            "year": movie_year,
            "genre": row['genres'],
            "poster": poster_url
        })
    return recommendations

def animated_title(text, tag="h1"):
        unique_id = str(uuid.uuid4()).replace("-", "")
        animation_name = f"fadeIn_{unique_id}"  # Unique animation name

        st.markdown(
        f"""
        <style>
        @keyframes {animation_name} {{
            0% {{ opacity: 0; transform: translateY(-20px); }}
            100% {{ opacity: 1; transform: translateY(0); }}
        }}
        .animated-title-{unique_id} {{
            font-size: 2.5rem;
            font-weight: bold;
            text-align: center;
            animation: {animation_name} 1.0s ease-in-out;
        }}
        </style>
        <{tag} class="animated-title-{unique_id}">{text}</{tag}>
        """,
        unsafe_allow_html=True,
    )
        

# Recommendation Function
def get_recommendations(title, top_n=10):
    try:
        # Find the index of the given movie title
        idx = data2[data2['primaryTitle'].str.lower() == title.lower()].index[0]
        
        # Get similarity scores for the movie as a dense array for processing
        sim_scores = sparse_cosine_sim[idx].toarray().flatten()
        
        # Pair each score with its index
        sim_scores = list(enumerate(sim_scores))
        
        # Sort based on similarity scores in descending order
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        # Get indices of the top similar movies
        sim_indices = [i[0] for i in sim_scores[1:top_n+1]]
        
        # Retrieve recommended movies
        recommended_movies = data2.iloc[sim_indices]

        # Apply year filtering and optional genre filtering
        filtered_recommendations = recommended_movies[
            recommended_movies["startYear"].between(*selected_year)
        ]
        if selected_genre != "None":
            filtered_recommendations = filtered_recommendations[
                filtered_recommendations["genres"].str.contains(selected_genre, case=False)
            ]
        
        input_movie = data2.iloc[idx]
        input_movie_details = {
            "movie_id": input_movie['movieId'],
            "title": input_movie['primaryTitle'],
            "year": input_movie['startYear'],
            "genre": input_movie['genres'],
            "poster": get_movie_poster_omdb(input_movie['primaryTitle'], input_movie['startYear']),
            "trailer": get_youtube_trailer(input_movie['primaryTitle'], input_movie['startYear']) 
            }
        
        # Fetch posters and create a list of dictionaries for each recommendation
        recommendations = [input_movie_details]
        # Fetch posters and create a list of dictionaries for each recommendation
        for _, row in filtered_recommendations.iterrows():
            trailer_url = get_youtube_trailer(row['primaryTitle'], row['startYear'])
            movie_title = row['primaryTitle']
            movie_year = row['startYear']
            movie_id = row['movieId']  # Ensure 'movieId' exists in your dataset
            poster_url = get_movie_poster_omdb(movie_title, movie_year)
            recommendations.append({
                "movie_id": movie_id,
                "title": movie_title,
                "year": movie_year,
                "genre": row['genres'],
                "poster": poster_url,
                "trailer": trailer_url
            })
        
        return recommendations
    
    except IndexError:
        st.write("Movie not found in the dataset.")
        return []


# Account Section 
if st.session_state.user is None:
    
    animated_title("CineSuggest- Movie Recommender")
    st.write("Please log in or create a new account.")
    
    # Login Form
    option = st.radio("Select an option", ("Login", "Create Account"))
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if option == "Login":
        if st.button("Login"):
            user = authenticate_user(username, password)
            if user:
                st.session_state.user = {"user_name": user["user_name"], "user_id": user["user_id"]}
                #st.success("Logged in successfully!")

            else:
                st.error("Invalid username or password.")
    
    elif option == "Create Account":
        if st.button("Create Account"):
            success = create_user(username, password)
            if success:
                st.success("Account created! Please log in.")
            else:
                st.error("Username already exists.")
    
else:
    # After successful login, show sidebar with user name
    st.sidebar.title("Menu")
    if st.sidebar.button("Home", use_container_width=True):
        set_page("home")
    if st.sidebar.button("Search through Specific Actors", use_container_width=True):
        set_page("search_actor")
    if st.sidebar.button("Search through Specific Directors", use_container_width=True):
        set_page("search_director")
    if st.sidebar.button("Your Favorites", use_container_width=True):
        set_page("favorites")
    if st.sidebar.button("Your Watchlist", use_container_width=True):
        set_page("watchlist")


# Sidebar Filters (only visible on Home page)
    if st.session_state.page == "home":
        st.sidebar.header("Filter Options")
        selected_year = st.sidebar.slider("Filter by Year", 1950, 2024, (2000, 2024))
        selected_genre = st.sidebar.selectbox("Select Genre", ["None"] + list(data2["genres"].unique()))
    else:
        # Initialize filters to None or default if not on home
        selected_year = (1950, 2024)
        selected_genre = "None"
    st.sidebar.write(f"Welcome, {st.session_state.user['user_name']}!")
    if st.sidebar.button("Logout"):
        st.session_state.user = None

# Main Content Based on Page Selection
    if "load_state" not in st.session_state:
        st.session_state.load_state= False

    if st.session_state.page == "home":
        animated_title("CineSuggest- Movie Recommender")
        st.write("Get personalized movie recommendations based on genres and year.")

        selected_movie = st.selectbox("Select a movie to get recommendations", data2['primaryTitle'].unique())

        st.markdown('<div class="special-button">', unsafe_allow_html=True)
        if st.button("Recommend") or st.session_state.load_state:
            st.session_state.load_state = True
            st.markdown('</div>', unsafe_allow_html=True)
            with st.spinner("Fetching recommendations..."):
                recommendations = get_recommendations(selected_movie)
            if recommendations:
                st.write("Recommended Movies:")
                for movie in recommendations:
                    col1, col2 = st.columns([1, 3])  # Columns for poster and details
                    with col1:
                        if movie["poster"]:
                            st.image(movie["poster"], width=120)
                    with col2:
                        st.markdown(f"**{movie['title']} ({movie['year']})** - Genre: {movie['genre']}")
                    
                        # Trailer link check
                        trailer_url = movie.get("trailer", None)
                        if trailer_url:
                            st.markdown(f"[Watch Trailer]({trailer_url})", unsafe_allow_html=True)
                        else:
                            st.write("Trailer not available.")
                    
                        # Add to Favorites and Watchlist buttons
                        if st.session_state.user:
                            user_id = st.session_state.user['user_id']
                            if st.button(f"Add to Favorites: {movie['title']}", key=f"fav_{movie['movie_id']}"):
                                if add_to_favorites(user_id, movie['movie_id'], movie['title']):
                                    st.success(f"{movie['title']} added to Favorites.")
                            if st.button(f"Add to Watchlist: {movie['title']}", key=f"watch_{movie['movie_id']}"):
                                if add_to_watchlist(user_id, movie['movie_id'], movie['title']):
                                    st.success(f"{movie['title']} added to Watchlist.")
                        else:
                            st.write("Login to add movies to your favorites or watchlist.")
            else:
                st.write("No recommendations found.")

    elif st.session_state.page == "favorites":
        animated_title("Your Favorites")
        if st.session_state.user:
            user_id = st.session_state.user['user_id']
            favorites = get_favorites(user_id)
            if favorites:
                for fav in favorites:
                    # Retrieve movie details from dataset
                    movie = data2[data2['movieId'] == fav["movie_id"]].iloc[0]
                    col1, col2 = st.columns([1, 3])  # Columns for poster and details
                    with col1:
                        poster = get_movie_poster_omdb(fav["movie_title"], movie["startYear"])
                        if poster:
                            st.image(poster, width=100)
                    with col2:
                        st.markdown(f"**{fav['movie_title']} ({movie['startYear']})** - Genre: {movie['genres']}")
                        if st.button("Remove from Favourites", key=f"remove_fav_{fav['movie_id']}"):
                            remove_from_favourites(user_id, fav['movie_id'])
                            st.success("Movie removed from favourites successfully!")
            else:
                st.write("You have no favorite movies yet.")
        else:
            st.write("Please log in to view your favorites.")

    elif st.session_state.page == "watchlist":
        animated_title("Your Watchlist")
        if st.session_state.user:
            user_id = st.session_state.user['user_id']
            watchlist = get_watchlist(user_id)
            if watchlist:
                for movie in watchlist:
                    # Retrieve movie details from dataset
                    movie_data = data2[data2['movieId'] == movie["movie_id"]].iloc[0]
                    col1, col2 = st.columns([1, 3])  # Columns for poster and details
                    with col1:
                        poster = get_movie_poster_omdb(movie["movie_title"], movie_data["startYear"])
                        if poster:
                            st.image(poster, width=100)
                    with col2:
                        st.markdown(f"**{movie['movie_title']} ({movie_data['startYear']})** - Genre: {movie_data['genres']}")
                        if st.button("Remove from Watchlist", key=f"remove_watch_{movie['movie_id']}"):
                            remove_from_watchlist(user_id, movie['movie_id'])
                            st.success("Movie removed from watchlist successfully!")
            else:
                st.write("You have no movies in your watchlist yet.")
        else:
            st.write("Please log in to view your watchlist.")

    elif st.session_state.page == "search_actor":
        animated_title("Search Movies by Actor")
        if st.session_state.user:
            # Extract unique actors
            all_actors = set(actor for actors in data2['actors'] for actor in actors)
            all_actors = ["Select an Actor"] + sorted(all_actors)
            selected_actor = st.selectbox("Select an Actor", all_actors)
            if  (st.button("Search") or st.session_state.load_state) and selected_actor != "Select an Actor":
                st.session_state.load_state= True
                actor_movies = search_by_actor(selected_actor)
                if selected_actor != "Select an Actor":
                    with st.spinner("Fetching recommendations..."):
                        actor_movies = search_by_actor(selected_actor)
                    if actor_movies:
                        st.write(f"Movies featuring **{selected_actor}**:")
                        for movie in actor_movies:
                            col1, col2 = st.columns([1, 3])  # Columns for poster and details
                            with col1:
                                if movie["poster"]:
                                    st.image(movie["poster"], width=100)
                            with col2:
                                st.markdown(f"**{movie['title']} ({movie['year']})** - Genre: {movie['genre']}")
                                if st.session_state.user:
                                    user_id = st.session_state.user['user_id']
                                    if st.button(f"Add to Favorites: {movie['title']}", key=f"fav_{movie['movie_id']}"):
                                        if add_to_favorites(user_id, movie['movie_id'], movie['title']):
                                            st.success(f"{movie['title']} added to Favorites.")
                                    if st.button(f"Add to Watchlist: {movie['title']}", key=f"watch_{movie['movie_id']}"):
                                        if add_to_watchlist(user_id, movie['movie_id'], movie['title']):
                                            st.success(f"{movie['title']} added to Watchlist.")
                    else:
                        st.write(f"No movies found featuring **{selected_actor}**.")
        else:
            st.write("Please log in to search movies by actors.")

    elif st.session_state.page == "search_director":
        animated_title("Search Movies by Director")
        if st.session_state.user:
            # Extract unique directors
            all_directors = sorted(data2['directors'].unique())
            all_directors = ["Select a Director"] + all_directors
            selected_director = st.selectbox("Select a Director", all_directors)

            if (st.button("Search") or st.session_state.load_state) and selected_director != "Select a Director" :
                st.session_state.load_state= True
                director_movies = search_by_director(selected_director)
                if selected_director != "Select a Director":
                    with st.spinner("Fetching recommendations..."):
                        director_movies = search_by_director(selected_director)
                    if director_movies:
                        st.write(f"Movies directed by **{selected_director}**:")
                        for movie in director_movies:
                            col1, col2 = st.columns([1, 3])  # Columns for poster and details
                            with col1:
                                if movie["poster"]:
                                    st.image(movie["poster"], width=100)
                            with col2:
                                st.markdown(f"**{movie['title']} ({movie['year']})** - Genre: {movie['genre']}")
                                if st.session_state.user:
                                    user_id = st.session_state.user['user_id']
                                    if st.button(f"Add to Favorites: {movie['title']}", key=f"fav_{movie['movie_id']}"):
                                        if add_to_favorites(user_id, movie['movie_id'], movie['title']):
                                            st.success(f"{movie['title']} added to Favorites.")
                                    if st.button(f"Add to Watchlist: {movie['title']}", key=f"watch_{movie['movie_id']}"):
                                        if add_to_watchlist(user_id, movie['movie_id'], movie['title']):
                                            st.success(f"{movie['title']} added to Watchlist.")
                    else:
                        st.write(f"No movies found directed by **{selected_director}**.")
        else:
            st.write("Please log in to search movies by directors.")
