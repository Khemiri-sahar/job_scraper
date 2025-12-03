from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pickle
import pandas as pd

app = FastAPI()

try:
    model = SentenceTransformer("models/job_recommender_model")
    
    with open("models/job_embeddings.pkl", "rb") as f:
        embeddings = pickle.load(f)
    
    df = pd.read_csv("models/keejob_ml_dataset.csv")
    
    if np.isnan(embeddings).any():
        print("Warning: Embeddings contain NaN values, cleaning...")
        embeddings = np.nan_to_num(embeddings, nan=0.0)
    
    if np.isinf(embeddings).any():
        print("Warning: Embeddings contain Inf values, cleaning...")
        embeddings = np.nan_to_num(embeddings, posinf=0.0, neginf=0.0)
    
    print(f"Loaded {len(df)} jobs")
    print(f"Embeddings shape: {embeddings.shape}")
    
except Exception as e:
    print(f"Error loading models: {e}")
    raise


# API INPUT SCHEMA
class Query(BaseModel):
    text: str
    top_k: int = 5

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "Job Recommender API",
        "total_jobs": len(df),
        "embedding_shape": list(embeddings.shape)
    }

# RECOMMENDATION ENDPOINT
@app.post("/recommend")
def recommend(query: Query):
    try:
        q_embed = model.encode([query.text])
        
        q_embed = np.nan_to_num(q_embed, nan=0.0, posinf=0.0, neginf=0.0)
        
        scores = cosine_similarity(q_embed, embeddings)[0]
        
        scores = np.nan_to_num(scores, nan=0.0, posinf=0.0, neginf=0.0)
        
        top_idx = np.argsort(scores)[::-1][:query.top_k]
        
        results = df.iloc[top_idx][['title', 'company', 'sector', 'salary']].copy()
        
        results_dict = results.to_dict(orient="records")
        
        for record in results_dict:
            for key, value in record.items():
                if pd.isna(value) or (isinstance(value, float) and not np.isfinite(value)):
                    record[key] = None  
        
        return results_dict
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation error: {str(e)}")