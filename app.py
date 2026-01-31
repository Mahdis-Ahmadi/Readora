import streamlit as st
import pandas as pd
import numpy as np
import pickle
import os
import sqlite3
from PIL import Image, ImageDraw

# Page Config
st.set_page_config(page_title="Readora Online Bookshop", page_icon="📚", layout="wide")

# Helper for placeholder image
def get_placeholder_image(text="No Image"):
    img = Image.new('RGB', (120, 180), color=(200, 200, 200))
    d = ImageDraw.Draw(img)
    d.text((30, 80), text, fill=(0, 0, 0))
    return img

# Load Models (Cached)
@st.cache_resource
def load_models():
    if not os.path.exists('models/nmf_model.pkl'):
        return None, None, None
        
    with open('models/nmf_model.pkl', 'rb') as f:
        model_data = pickle.load(f)
    with open('models/mappings.pkl', 'rb') as f:
        mappings = pickle.load(f)
    books = pd.read_pickle('models/books_metadata.pkl')
    return model_data, mappings, books

model_data, mappings, books_df = load_models()

if model_data is None:
    st.error("Model not found. Please train the model first.")
    st.stop()

user_features = model_data['user_features']
item_features = model_data['item_features']
user_to_index = mappings['user_to_index']
index_to_book = mappings['index_to_book']
book_to_index = mappings['book_to_index']

# Sample Users
sample_users = {
    "User A (11676)": 11676,
    "User B (198711)": 198711,
    "User C (153662)": 153662,
    "User D (98391)": 98391,
    "User E (35859)": 35859,
    "User F (212898)": 212898
}

# Sidebar
st.sidebar.title("Login")
selected_user_label = st.sidebar.selectbox("Select User", list(sample_users.keys()))
current_user_id = sample_users[selected_user_label]

st.sidebar.markdown("---")
# Removed "Search" from navigation
page = st.sidebar.radio("Navigation", ["Home", "Recommendations", "My Ratings"])

# Initialize session state for book selection
if 'selected_isbn' not in st.session_state:
    st.session_state.selected_isbn = None

def select_book(isbn):
    st.session_state.selected_isbn = isbn

def clear_selection():
    st.session_state.selected_isbn = None

# Helper to get book details
def get_book_details(isbn):
    book = books_df[books_df['ISBN'] == isbn]
    if not book.empty:
        return book.iloc[0]
    return None

def get_avg_rating(isbn):
    # This is expensive if we do it every time, but for single book detail it's fine.
    # Ideally we should have this precomputed.
    # Let's check if it's in the popular books csv, otherwise query DB.
    try:
        conn = sqlite3.connect('database/user_rate_book.db')
        query = f"SELECT AVG(`Book-Rating`) as avg_rating FROM Ratings WHERE ISBN='{isbn}'"
        df = pd.read_sql(query, conn)
        conn.close()
        if not df.empty and pd.notna(df.iloc[0]['avg_rating']):
            return df.iloc[0]['avg_rating']
    except:
        pass
    return 0.0

# View: Book Detail
if st.session_state.selected_isbn:
    st.button("← Back to Home", on_click=clear_selection)
    
    book = get_book_details(st.session_state.selected_isbn)
    if book is not None:
        c1, c2 = st.columns([1, 3])
        with c1:
            if pd.notna(book['Image-URL-M']):
                st.image(book['Image-URL-M'], width=200)
            else:
                st.image(get_placeholder_image(str(book['Book-Title'])[:10]), width=200)
        with c2:
            st.title(book['Book-Title'])
            st.subheader(f"By {book['Book-Author']}")
            
            avg_r = get_avg_rating(book['ISBN'])
            st.metric("Average Rating", f"{avg_r:.2f} / 10")
            
            st.markdown("### Description")
            # Generate description
            publisher = book['Publisher'] if 'Publisher' in book and pd.notna(book['Publisher']) else "Unknown Publisher"
            year = book['Year-Of-Publication'] if 'Year-Of-Publication' in book and pd.notna(book['Year-Of-Publication']) else "Unknown Year"
            
            desc = f"""
            **{book['Book-Title']}** is a compelling work by **{book['Book-Author']}**. 
            This edition was published by *{publisher}* in {year}. 
            
            Join the community of readers who have rated this book! 
            With an average rating of **{avg_r:.2f}**, it has sparked conversations and captured imaginations.
            Dive into this literary journey today.
            """
            st.markdown(desc)
            
            st.caption(f"ISBN: {book['ISBN']}")
            
    else:
        st.error("Book details not found.")

# Main Content Views (Only if no book is selected)
elif page == "Home":
    st.title("Welcome to Readora Bookshop 📚")
    st.write(f"Logged in as **{selected_user_label}**")
    
    # Search Box in Home Page
    st.markdown("### 🔍 Search Books")
    search_query = st.text_input("Enter book title or author to search", key="home_search")
    
    if search_query:
        st.subheader("Search Results")
        results = books_df[
            books_df['Book-Title'].str.contains(search_query, case=False, na=False) | 
            books_df['Book-Author'].str.contains(search_query, case=False, na=False)
        ].head(20)
        
        if not results.empty:
            for idx, book in results.iterrows():
                with st.container():
                    c1, c2, c3 = st.columns([1, 4, 2])
                    with c1:
                        if pd.notna(book['Image-URL-M']):
                            st.image(book['Image-URL-M'], width=60)
                        else:
                            st.image(get_placeholder_image("No Img"), width=60)
                    with c2:
                        st.markdown(f"**{book['Book-Title']}**")
                        st.caption(f"By {book['Book-Author']}")
                    with c3:
                        if st.button("View Details", key=f"search_btn_{book['ISBN']}"):
                            select_book(book['ISBN'])
                            st.rerun()
        else:
            st.warning("No books found matching your query.")
        
        st.markdown("---")

    # Placeholder Amazon-like Banner
    st.markdown("""
    <div style="background-color: #232f3e; padding: 20px; border-radius: 5px; color: white; text-align: center; margin-bottom: 20px;">
        <h2>Summer Reading Sale</h2>
        <p>Get up to 50% off on bestsellers</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("Popular Books")
    try:
        popular = pd.read_csv('reports/popular_books_weighted.csv').head(10)
        
        cols = st.columns(5)
        for idx, row in popular.iterrows():
            col = cols[idx % 5]
            with col:
                # Image
                if pd.notna(row['Image-URL-M']):
                    st.image(row['Image-URL-M'], use_container_width=True)
                else:
                    st.image(get_placeholder_image(), use_container_width=True)
                
                # Title & Author
                title = str(row['Book-Title']) if pd.notna(row['Book-Title']) else "Unknown Title"
                st.markdown(f"**{title[:40]}...**")
                
                author = str(row['Book-Author']) if pd.notna(row['Book-Author']) else "Unknown Author"
                st.caption(f"{author}")
                
                # View Details Button
                if st.button("View Details", key=f"pop_btn_{row['ISBN']}"):
                    select_book(str(row['ISBN']))
                    st.rerun()
                    
    except Exception as e:
        st.error(f"Could not load popular books: {e}")

elif page == "Recommendations":
    st.title("Recommended for You")
    
    if current_user_id in user_to_index:
        u_idx = user_to_index[current_user_id]
        
        user_vector = user_features[u_idx, :]
        predicted_ratings = np.dot(user_vector, item_features)
        
        top_indices = predicted_ratings.argsort()[::-1]
        
        conn = sqlite3.connect('database/user_rate_book.db')
        rated_books = pd.read_sql(f"SELECT ISBN FROM Ratings WHERE `User-ID`={current_user_id}", conn)['ISBN'].astype(str).values
        conn.close()
        
        recommendations = []
        count = 0
        for idx in top_indices:
            isbn = index_to_book[idx]
            if isbn not in rated_books:
                book = get_book_details(isbn)
                if book is not None:
                    recommendations.append(book)
                    count += 1
                if count >= 10:
                    break
        
        # Display
        cols = st.columns(5)
        for i, book in enumerate(recommendations):
            col = cols[i % 5]
            with col:
                if pd.notna(book['Image-URL-M']):
                    st.image(book['Image-URL-M'], use_container_width=True)
                else:
                    st.image(get_placeholder_image(), use_container_width=True)
                
                title = str(book['Book-Title']) if pd.notna(book['Book-Title']) else "Unknown Title"
                st.markdown(f"**{title}**")
                
                author = str(book['Book-Author']) if pd.notna(book['Book-Author']) else "Unknown Author"
                st.caption(f"{author}")
                
                if st.button("View Details", key=f"rec_btn_{book['ISBN']}"):
                    select_book(book['ISBN'])
                    st.rerun()
                
    else:
        st.warning("User not found in training data (cold start or filtered out). Showing popular books.")
        try:
            popular = pd.read_csv('reports/popular_books_weighted.csv').head(10)
            cols = st.columns(5)
            for idx, row in popular.iterrows():
                col = cols[idx % 5]
                with col:
                    if pd.notna(row['Image-URL-M']):
                        st.image(row['Image-URL-M'], use_container_width=True)
                    else:
                        st.image(get_placeholder_image(), use_container_width=True)
                        
                    st.markdown(f"**{row['Book-Title'][:40]}...**")
                    st.caption(f"{row['Book-Author']}")
                    
                    if st.button("View Details", key=f"cold_btn_{row['ISBN']}"):
                        select_book(str(row['ISBN']))
                        st.rerun()
        except:
            st.write("No popular books available.")

elif page == "My Ratings":
    st.title("My Ratings Analysis")
    
    conn = sqlite3.connect('database/user_rate_book.db')
    my_ratings = pd.read_sql(f"SELECT * FROM Ratings WHERE `User-ID`={current_user_id}", conn)
    conn.close()
    
    if not my_ratings.empty:
        my_ratings['Book-Rating'] = pd.to_numeric(my_ratings['Book-Rating'], errors='coerce')
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Ratings", len(my_ratings))
        with col2:
            st.metric("Average Rating", f"{my_ratings['Book-Rating'].mean():.2f}")
        
        st.divider()
        st.subheader("Books you rated highly (9-10)")
        high_rated = my_ratings[my_ratings['Book-Rating'] >= 9]
        
        if not high_rated.empty:
            for idx, row in high_rated.iterrows():
                book = get_book_details(str(row['ISBN']))
                if book is not None:
                    with st.container():
                        c1, c2, c3 = st.columns([1, 5, 1])
                        with c1:
                            if pd.notna(book['Image-URL-M']):
                                st.image(book['Image-URL-M'], width=60)
                        with c2:
                            st.write(f"**{book['Book-Title']}** - ⭐ {row['Book-Rating']}")
                            st.caption(f"Author: {book['Book-Author']}")
                        with c3:
                            if st.button("Details", key=f"my_btn_{row['ISBN']}"):
                                select_book(str(row['ISBN']))
                                st.rerun()
        else:
            st.info("No highly rated books found.")
            
        # Plot distribution
        st.divider()
        st.subheader("Rating Distribution")
        rating_counts = my_ratings['Book-Rating'].value_counts().sort_index()
        st.bar_chart(rating_counts)
        
    else:
        st.info("You haven't rated any books yet.")
