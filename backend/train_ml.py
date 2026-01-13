import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import mean_squared_error
import os
import joblib
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data', 'ml-100k')
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models', 'ml_models')

# Ensure model directory exists
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

def load_data():
    """Load MovieLens 100K data."""
    u_data_path = os.path.join(DATA_DIR, 'u.data')
    if not os.path.exists(u_data_path):
        raise FileNotFoundError(f"Data file not found at {u_data_path}. Please run download script first.")

    # Load ratings
    columns = ['user_id', 'item_id', 'rating', 'timestamp']
    df = pd.read_csv(u_data_path, sep='\t', names=columns)
    logger.info(f"Loaded {len(df)} ratings.")
    return df

def preprocess_data(df):
    """
    Create a user-item matrix and split data.
    Returns: train_matrix, test_matrix, user_mapper, item_mapper
    """
    # Simple pivot for SVD (Note: sparse matrix is better for large data, using pivot for simplicity in 100k)
    user_item_matrix = df.pivot(index='user_id', columns='item_id', values='rating').fillna(0)
    
    # Store index/column mappings for later
    user_mapper = {user: i for i, user in enumerate(user_item_matrix.index)}
    item_mapper = {item: i for i, item in enumerate(user_item_matrix.columns)}
    
    matrix = user_item_matrix.values
    
    # Split data 80-20
    # For matrix recommendation, we usually mask some ratings in the test set.
    # Approach:
    # 1. Split interactions (ratings) into train/test
    # But since we are using TruncatedSVD on the full matrix structure, we'll use a standard strategy:
    # Randomly select 20% of non-zero entries to be the test set, masking them in training.
    
    train_matrix = matrix.copy()
    test_data = []

    # Get coordinates of all ratings
    nz_users, nz_items = matrix.nonzero()
    n_ratings = len(nz_users)
    n_test = int(n_ratings * 0.2)
    
    logger.info(f"Splitting data: {n_ratings} ratings total. Selecting {n_test} for testing (20%).")
    
    # Randomly choose indices for test set
    indices = np.random.choice(n_ratings, n_test, replace=False)
    
    for idx in indices:
        u, i = nz_users[idx], nz_items[idx]
        test_data.append((u, i, matrix[u, i])) # Store true rating
        train_matrix[u, i] = 0 # Mask in training
        
    return train_matrix, test_data, user_item_matrix, user_mapper, item_mapper

def train_svd(matrix, n_components=20):
    """Train SVD model."""
    logger.info(f"Training SVD with {n_components} components...")
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    svd.fit(matrix)
    return svd

def predict_rating(svd_model, matrix_avg, u_idx, i_idx):
    # This basic SVD reconstruction might be slightly off without bias handling, 
    # but serves the prototype purpose.
    # Rating ~ UserFactor * ItemFactor
    # Reconstructed matrix
    reconstructed = svd_model.inverse_transform(svd_model.transform(matrix_avg))
    return reconstructed[u_idx, i_idx]

def evaluate_model(svd, matrix, test_data):
    """Calculate RMSE on test data."""
    # Reconstruct matrix approximation
    matrix_transformed = svd.transform(matrix)
    matrix_reconstructed = svd.inverse_transform(matrix_transformed)
    
    y_true = []
    y_pred = []
    
    for u, i, rating in test_data:
        y_true.append(rating)
        # Clamp prediction between 1 and 5
        pred = matrix_reconstructed[u, i]
        pred = max(1, min(5, pred))
        y_pred.append(pred)
        
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    logger.info(f"Test RMSE: {rmse:.4f}")
    return rmse

def train_and_eval():
    try:
        # Load
        df = load_data()
        
        # Preprocess
        train_matrix, test_data, full_df, user_map, item_map = preprocess_data(df)
        
        # Train
        svd_model = train_svd(train_matrix, n_components=50) # Increased components for better accuracy
        
        # Evaluate
        evaluate_model(svd_model, train_matrix, test_data)
        
        # Save
        model_path = os.path.join(MODEL_DIR, 'svd_model.pkl')
        mappings_path = os.path.join(MODEL_DIR, 'mappings.pkl')
        
        joblib.dump(svd_model, model_path)
        joblib.dump({'user_map': user_map, 'item_map': item_map, 'index': full_df.index, 'columns': full_df.columns}, mappings_path)
        
        logger.info(f"Model saved to {model_path}")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    train_and_eval()
