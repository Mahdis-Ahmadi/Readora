# import sqlite3
# import pandas as pd
# import numpy as np
# import os
#
# # Connect to database
# db_path = 'database/user_rate_book.db'
# conn = sqlite3.connect(db_path)
#
# # Load data
# print("Loading data...")
# books = pd.read_sql("SELECT * FROM Books", conn)
# users = pd.read_sql("SELECT * FROM Users", conn)
# ratings = pd.read_sql("SELECT * FROM Ratings", conn)
# conn.close()
#
# # Data Cleaning
# print("Cleaning data...")
# # Books
# books['Year-Of-Publication'] = pd.to_numeric(books['Year-Of-Publication'], errors='coerce')
# books['Year-Of-Publication'] = books['Year-Of-Publication'].fillna(0).astype(int)
#
# # Users
# users['Age'] = pd.to_numeric(users['Age'], errors='coerce')
#
# # Ratings
# ratings['Book-Rating'] = pd.to_numeric(ratings['Book-Rating'], errors='coerce')
# ratings['User-ID'] = pd.to_numeric(ratings['User-ID'], errors='coerce')
#
# # EDA Report
# eda_data = []
#
# def add_eda_row(metric, value):
#     eda_data.append({'Metric': metric, 'Value': value})
#
# add_eda_row('Total Books', len(books))
# add_eda_row('Total Users', len(users))
# add_eda_row('Total Ratings', len(ratings))
# add_eda_row('Unique Books in Ratings', ratings['ISBN'].nunique())
# add_eda_row('Unique Users in Ratings', ratings['User-ID'].nunique())
# add_eda_row('Average Rating', ratings['Book-Rating'].mean())
# add_eda_row('Missing Ages', users['Age'].isnull().sum())
# add_eda_row('Missing Book Authors', books['Book-Author'].isnull().sum())
# add_eda_row('Missing Publishers', books['Publisher'].isnull().sum())
#
# # Rating Distribution
# rating_dist = ratings['Book-Rating'].value_counts().sort_index().to_dict()
# for rating, count in rating_dist.items():
#     add_eda_row(f'Count of Rating {rating}', count)
#
# eda_df = pd.DataFrame(eda_data)
# eda_df.to_csv('reports/eda_report.csv', index=False)
# print("Saved reports/eda_report.csv")
#
# # Data Analysis Report
# # 1. Top 10 Rated Books (with at least 5 ratings)
# rating_counts = ratings.groupby('ISBN')['Book-Rating'].count()
# popular_books_isbn = rating_counts[rating_counts >= 10].index # At least 10 ratings
# avg_ratings = ratings[ratings['ISBN'].isin(popular_books_isbn)].groupby('ISBN')['Book-Rating'].mean()
# top_books = avg_ratings.sort_values(ascending=False).head(50).reset_index()
# top_books = top_books.merge(books[['ISBN', 'Book-Title', 'Book-Author', 'Publisher']], on='ISBN', how='left')
# top_books.columns = ['ISBN', 'Average Rating', 'Title', 'Author', 'Publisher']
#
# top_books.to_csv('reports/data_analysis_report.csv', index=False)
# print("Saved reports/data_analysis_report.csv")
#
# # 2. Most Active Users
# active_users = ratings.groupby('User-ID')['Book-Rating'].count().sort_values(ascending=False).head(50).reset_index()
# active_users.columns = ['User-ID', 'Rating Count']
# active_users.to_csv('reports/active_users.csv', index=False)
# print("Saved reports/active_users.csv")
#
# # 3. Save popular books for the app (Cold start problem or just general recommendations)
# # Weighted Rating (IMDB formula): (v/(v+m) * R) + (m/(m+v) * C)
# # v = number of ratings for the book
# # m = minimum number of ratings required to be listed
# # R = average rating of the book
# # C = mean vote across the whole report
# C = ratings['Book-Rating'].mean()
# m = rating_counts.quantile(0.9) # 90th percentile
# q_books = ratings[ratings['ISBN'].isin(rating_counts[rating_counts >= m].index)]
#
# def weighted_rating(x, m=m, C=C):
#     v = x.count()
#     R = x.mean()
#     return (v/(v+m) * R) + (m/(m+v) * C)
#
# # Calculate weighted score for qualified books
# # Note: This might be slow if done on groupby apply.
# # Alternative: Calculate aggregations first.
# book_stats = q_books.groupby('ISBN')['Book-Rating'].agg(['count', 'mean'])
# book_stats['score'] = book_stats.apply(lambda x: (x['count']/(x['count']+m) * x['mean']) + (m/(x['count']+m) * C), axis=1)
# top_scored_books = book_stats.sort_values('score', ascending=False).head(100).reset_index()
# top_scored_books = top_scored_books.merge(books[['ISBN', 'Book-Title', 'Book-Author', 'Image-URL-M']], on='ISBN', how='left')
#
# top_scored_books.to_csv('reports/popular_books_weighted.csv', index=False)
# print("Saved reports/popular_books_weighted.csv")
#
# print("EDA and Analysis Complete.")

import sqlite3
import pandas as pd
import numpy as np
import os
import json

# ---------------------------
# Helpers
# ---------------------------
def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def add_eda_row(eda_data, metric, value):
    eda_data.append({"Metric": metric, "Value": value})

def table_schema_missing_report(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """
    Returns a per-column report:
    - dtype
    - missing_count
    - missing_pct
    - unique_count
    """
    n = len(df)
    out = pd.DataFrame({
        "table": table_name,
        "column": df.columns,
        "dtype": [str(t) for t in df.dtypes],
        "missing_count": [int(df[c].isna().sum()) for c in df.columns],
        "missing_pct": [round((df[c].isna().sum() / n) * 100, 4) if n else np.nan for c in df.columns],
        "unique_count": [int(df[c].nunique(dropna=True)) for c in df.columns],
    })
    return out

def null_columns_summary(df: pd.DataFrame) -> dict:
    """Returns dict of columns that have any missing values -> missing_count."""
    null_counts = df.isna().sum()
    null_counts = null_counts[null_counts > 0]
    return {col: int(cnt) for col, cnt in null_counts.items()}

# ---------------------------
# Load data from SQLite
# ---------------------------
db_path = "database/user_rate_book.db"
reports_dir = "reports"
ensure_dir(reports_dir)

conn = sqlite3.connect(db_path)

print("Loading data...")
books = pd.read_sql("SELECT * FROM Books", conn)
users = pd.read_sql("SELECT * FROM Users", conn)
ratings = pd.read_sql("SELECT * FROM Ratings", conn)
conn.close()

print("Cleaning data...")
# Books
books["Year-Of-Publication"] = pd.to_numeric(books["Year-Of-Publication"], errors="coerce")
books["Year-Of-Publication"] = books["Year-Of-Publication"].fillna(0).astype(int)

# Users
users["Age"] = pd.to_numeric(users["Age"], errors="coerce")

# Ratings
ratings["Book-Rating"] = pd.to_numeric(ratings["Book-Rating"], errors="coerce")
ratings["User-ID"] = pd.to_numeric(ratings["User-ID"], errors="coerce")

# ---------------------------
# Schema + Missingness report (NEW)
# ---------------------------
schema_report = pd.concat([
    table_schema_missing_report(books, "Books"),
    table_schema_missing_report(users, "Users"),
    table_schema_missing_report(ratings, "Ratings"),
], ignore_index=True)

schema_report.to_csv(os.path.join(reports_dir, "schema_and_missingness.csv"), index=False)
print("Saved reports/schema_and_missingness.csv")

# ---------------------------
# EDA Report (expanded)
# ---------------------------
eda_data = []

# Table sizes
add_eda_row(eda_data, "Total Books", len(books))
add_eda_row(eda_data, "Total Users", len(users))
add_eda_row(eda_data, "Total Ratings", len(ratings))

# Duplicates
add_eda_row(eda_data, "Duplicate Rows in Books", int(books.duplicated().sum()))
add_eda_row(eda_data, "Duplicate Rows in Users", int(users.duplicated().sum()))
add_eda_row(eda_data, "Duplicate Rows in Ratings", int(ratings.duplicated().sum()))

# Key uniqueness checks (common in this dataset)
if "ISBN" in books.columns:
    add_eda_row(eda_data, "Unique ISBN in Books", int(books["ISBN"].nunique()))
if "User-ID" in users.columns:
    add_eda_row(eda_data, "Unique User-ID in Users", int(users["User-ID"].nunique()))
if set(["User-ID", "ISBN"]).issubset(ratings.columns):
    dup_pairs = int(ratings.duplicated(subset=["User-ID", "ISBN"]).sum())
    add_eda_row(eda_data, "Duplicate (User-ID, ISBN) pairs in Ratings", dup_pairs)

# Basic interaction counts
add_eda_row(eda_data, "Unique Books in Ratings", int(ratings["ISBN"].nunique()))
add_eda_row(eda_data, "Unique Users in Ratings", int(ratings["User-ID"].nunique()))

# Rating stats
add_eda_row(eda_data, "Average Rating (all)", float(ratings["Book-Rating"].mean()))
add_eda_row(eda_data, "Median Rating (all)", float(ratings["Book-Rating"].median()))
add_eda_row(eda_data, "Min Rating", float(ratings["Book-Rating"].min()))
add_eda_row(eda_data, "Max Rating", float(ratings["Book-Rating"].max()))

# Explicit vs implicit (0)
n_total = len(ratings)
n_zero = int((ratings["Book-Rating"] == 0).sum())
n_exp = int((ratings["Book-Rating"] > 0).sum())
add_eda_row(eda_data, "Total Rating Rows", n_total)
add_eda_row(eda_data, "Rating Rows where Book-Rating=0", n_zero)
add_eda_row(eda_data, "Rating Rows where Book-Rating>0 (explicit)", n_exp)
add_eda_row(eda_data, "Pct Rating=0", round((n_zero / n_total) * 100, 4) if n_total else np.nan)

# Missing/null columns info (NEW metrics you requested)
books_nulls = null_columns_summary(books)
users_nulls = null_columns_summary(users)
ratings_nulls = null_columns_summary(ratings)

add_eda_row(eda_data, "Books: #columns with any nulls", len(books_nulls))
add_eda_row(eda_data, "Books: null columns (name->count)", json.dumps(books_nulls, ensure_ascii=False))

add_eda_row(eda_data, "Users: #columns with any nulls", len(users_nulls))
add_eda_row(eda_data, "Users: null columns (name->count)", json.dumps(users_nulls, ensure_ascii=False))

add_eda_row(eda_data, "Ratings: #columns with any nulls", len(ratings_nulls))
add_eda_row(eda_data, "Ratings: null columns (name->count)", json.dumps(ratings_nulls, ensure_ascii=False))

# Some specific missing counts you already had
add_eda_row(eda_data, "Missing Ages", int(users["Age"].isnull().sum()))
add_eda_row(eda_data, "Missing Book Authors", int(books["Book-Author"].isnull().sum()) if "Book-Author" in books.columns else "N/A")
add_eda_row(eda_data, "Missing Publishers", int(books["Publisher"].isnull().sum()) if "Publisher" in books.columns else "N/A")

# Join coverage (helpful for project write-up)
# What % of rating ISBNs exist in Books?
books_isbn_set = set(books["ISBN"].astype(str))
ratings_isbn = ratings["ISBN"].astype(str)
isbn_match_pct = float(ratings_isbn.isin(books_isbn_set).mean() * 100) if len(ratings_isbn) else np.nan
add_eda_row(eda_data, "Ratings→Books ISBN match %", round(isbn_match_pct, 4))

# What % of rating users exist in Users?
users_set = set(users["User-ID"].dropna().astype(int))
ratings_users = ratings["User-ID"].dropna().astype(int)
user_match_pct = float(ratings_users.isin(users_set).mean() * 100) if len(ratings_users) else np.nan
add_eda_row(eda_data, "Ratings→Users User-ID match %", round(user_match_pct, 4))

# Rating distribution
rating_dist = ratings["Book-Rating"].value_counts().sort_index()
for rating, count in rating_dist.items():
    add_eda_row(eda_data, f"Count of Rating {int(rating) if pd.notna(rating) else rating}", int(count))

eda_df = pd.DataFrame(eda_data)
eda_df.to_csv(os.path.join(reports_dir, "eda_report.csv"), index=False)
print("Saved reports/eda_report.csv")

# ---------------------------
# Data Analysis Report
# ---------------------------
# 1) Top rated books (at least 10 ratings)
rating_counts = ratings.groupby("ISBN")["Book-Rating"].count()
popular_books_isbn = rating_counts[rating_counts >= 10].index
avg_ratings = ratings[ratings["ISBN"].isin(popular_books_isbn)].groupby("ISBN")["Book-Rating"].mean()

top_books = avg_ratings.sort_values(ascending=False).head(50).reset_index()
top_books = top_books.merge(
    books[["ISBN", "Book-Title", "Book-Author", "Publisher"]],
    on="ISBN",
    how="left"
)
top_books.columns = ["ISBN", "Average Rating", "Title", "Author", "Publisher"]
top_books.to_csv(os.path.join(reports_dir, "data_analysis_report.csv"), index=False)
print("Saved reports/data_analysis_report.csv")

# 2) Most active users
active_users = ratings.groupby("User-ID")["Book-Rating"].count().sort_values(ascending=False).head(50).reset_index()
active_users.columns = ["User-ID", "Rating Count"]
active_users.to_csv(os.path.join(reports_dir, "active_users.csv"), index=False)
print("Saved reports/active_users.csv")

# 3) Popular books for app (weighted rating, IMDB-style)
C = ratings["Book-Rating"].mean()
m = rating_counts.quantile(0.9)  # 90th percentile threshold
q_books = ratings[ratings["ISBN"].isin(rating_counts[rating_counts >= m].index)]

book_stats = q_books.groupby("ISBN")["Book-Rating"].agg(["count", "mean"])
book_stats["score"] = book_stats.apply(
    lambda x: (x["count"] / (x["count"] + m) * x["mean"]) + (m / (x["count"] + m) * C),
    axis=1
)

top_scored_books = book_stats.sort_values("score", ascending=False).head(100).reset_index()
top_scored_books = top_scored_books.merge(
    books[["ISBN", "Book-Title", "Book-Author", "Image-URL-M"]],
    on="ISBN",
    how="left"
)

top_scored_books.to_csv(os.path.join(reports_dir, "popular_books_weighted.csv"), index=False)
print("Saved reports/popular_books_weighted.csv")

print("EDA and Analysis Complete.")