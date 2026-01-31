import sqlite3
import pandas as pd
import numpy as np
import scipy.sparse as sparse
from sklearn.decomposition import NMF
import pickle
import os

# Connect to database
print("Loading data for training...")
db_path = 'database/user_rate_book.db'
conn = sqlite3.connect(db_path)
ratings = pd.read_sql("SELECT * FROM Ratings", conn)
books = pd.read_sql("SELECT ISBN, `Book-Title`, `Book-Author`, `Image-URL-M` FROM Books", conn)
conn.close()

# Data Cleaning
ratings['Book-Rating'] = pd.to_numeric(ratings['Book-Rating'], errors='coerce')
ratings = ratings.dropna(subset=['Book-Rating'])
ratings['ISBN'] = ratings['ISBN'].astype(str)
books['ISBN'] = books['ISBN'].astype(str)

# Filter out books and users to reduce sparsity
min_book_ratings = 10
book_rating_counts = ratings.groupby('ISBN')['Book-Rating'].count()
valid_books = book_rating_counts[book_rating_counts >= min_book_ratings].index
ratings = ratings[ratings['ISBN'].isin(valid_books)]

min_user_ratings = 10
user_rating_counts = ratings.groupby('User-ID')['Book-Rating'].count()
valid_users = user_rating_counts[user_rating_counts >= min_user_ratings].index
ratings = ratings[ratings['User-ID'].isin(valid_users)]

print(f"Filtered dataset: {len(ratings)} ratings, {len(ratings['User-ID'].unique())} users, {len(ratings['ISBN'].unique())} books.")

# Create Mappings
users_unique = ratings['User-ID'].unique()
user_to_index = {user_id: i for i, user_id in enumerate(users_unique)}
index_to_user = {i: user_id for i, user_id in enumerate(users_unique)}

books_unique = ratings['ISBN'].unique()
book_to_index = {isbn: i for i, isbn in enumerate(books_unique)}
index_to_book = {i: isbn for i, isbn in enumerate(books_unique)}

# Create Sparse Matrix (Users x Books)
row = ratings['User-ID'].map(user_to_index)
col = ratings['ISBN'].map(book_to_index)
data = ratings['Book-Rating'].astype(float)
# Handle 0 ratings: Treat as small positive or keep as 0? 
# NMF requires non-negative. 0 is fine.
# But if we want to differentiate "rated 0" from "not rated", we might have an issue.
# In this dataset, 0 is implicit. 1-10 is explicit.
# Let's treat all ratings as "confidence" or "preference".
# We'll use the raw values.

user_item_matrix = sparse.csr_matrix((data, (row, col)), shape=(len(users_unique), len(books_unique)))

# Train Model using NMF (Alternating Least Squares / Coordinate Descent)
print("Training ALS (NMF) model...")
# n_components: latent factors
model = NMF(n_components=30, init='nndsvd', random_state=42, max_iter=200)
user_features = model.fit_transform(user_item_matrix)
item_features = model.components_

# Save Model and Artifacts
print("Saving model and artifacts...")
os.makedirs('models', exist_ok=True)

with open('models/nmf_model.pkl', 'wb') as f:
    pickle.dump({'model': model, 'user_features': user_features, 'item_features': item_features}, f)

with open('models/mappings.pkl', 'wb') as f:
    pickle.dump({
        'user_to_index': user_to_index,
        'index_to_user': index_to_user,
        'book_to_index': book_to_index,
        'index_to_book': index_to_book
    }, f)

# Save book metadata
valid_books_df = books[books['ISBN'].isin(books_unique)].drop_duplicates(subset=['ISBN'])
valid_books_df.to_pickle('models/books_metadata.pkl')

print("Model training complete.")
