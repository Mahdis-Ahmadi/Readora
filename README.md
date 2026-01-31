# Amazon Bookshop Recommendation System

A Data Science project that implements a Book Recommendation System using Collaborative Filtering (ALS/NMF) and provides an interactive web application using Streamlit.

## Project Overview

This project analyzes the Amazon Books dataset to build a recommendation engine. It includes:
- **Exploratory Data Analysis (EDA)**: Insights into user ratings, book popularity, and distributions.
- **Machine Learning Model**: Uses Non-negative Matrix Factorization (NMF) for collaborative filtering to recommend books to users.
- **Web Application**: A Streamlit-based UI that mimics an online bookstore, allowing users to:
    - View personalized recommendations.
    - Search for books.
    - View book details (Title, Author, Rating, Description).
    - Analyze their own rating history.

## Features

- **Personalized Recommendations**: tailored to specific users based on their rating history.
- **Search Functionality**: Search books by title or author.
- **Popular Books**: Showcases top-rated/most popular books for new users (Cold Start problem).
- **User Dashboard**: Visualizes user's rating distribution and favorite books.

## File Structure

```
amazon_bookshop_recommendation_system/
├── app.py                  # Main Streamlit application
├── train_model.py          # Script to train the NMF model
├── eda_analysis.py         # Script for Exploratory Data Analysis
├── inspect_schema.py       # Helper to inspect database schema
├── requirements.txt        # Project dependencies
├── database/               # Database files (Not included in repo due to size)
│   └── user_rate_book.db   # SQLite database containing Books, Users, Ratings
├── models/                 # Saved model artifacts
│   ├── nmf_model.pkl       # Trained NMF model
│   ├── mappings.pkl        # User/Item mappings
│   └── books_metadata.pkl  # Pre-processed book metadata
├── reports/                # Generated analysis reports (CSVs)
└── .streamlit/             # Streamlit configuration
```

## Installation & Setup

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd amazon_bookshop_recommendation_system
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup the Database**:
    - The project requires the `user_rate_book.db` SQLite database.
    - Due to its size, it is not included in this repository.
    - Place your `user_rate_book.db` file inside the `database/` directory.

4.  **Train the Model (Optional)**:
    - If you want to retrain the model or regenerate artifacts:
    ```bash
    python train_model.py
    ```

## Running the Application

To start the web application, run:

```bash
streamlit run app.py
```

The app will open in your default browser (usually at `http://localhost:8501`).

## Login Credentials

For demonstration purposes, you can log in as one of the following sample users:
- User A (11676)
- User B (198711)
- User C (153662)
- User D (98391)
- User E (35859)
- User F (212898)
