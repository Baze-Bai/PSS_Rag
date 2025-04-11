import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
from Extract_PDF import extract_chunks_from_pdf
import os

def store_data():
    # Get the directory of the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))

    folder_path = os.path.join(current_dir, '_Marketing Project Sheets')

    chunks, file_names = extract_chunks_from_pdf(folder_path)

    # Load the pre-trained sentence vector model (MiniLM example)
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    # Calculate the vector representation for each text chunk
    embeddings = model.encode(chunks)  # shape: (num_chunks, 384)
    embeddings = np.array(embeddings, dtype="float32")

    # Create an index object and build a FAISS index 
    # (using cosine similarity: normalize vectors then use inner product for search)
    vec_dim = embeddings.shape[1]  # Vector dimension, e.g., all-MiniLM-L6-v2 is 384
    index = faiss.IndexFlatIP(vec_dim)
    # If using cosine similarity, vectors need to be L2 normalized first
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    # Store the index to disk
    faiss.write_index(index, "my_faiss.index")
    
    return chunks, index, file_names