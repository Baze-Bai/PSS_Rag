from Store_data import store_data
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
from Extract_PDF import extract_chunks_from_pdf
import os

chunks, index = store_data()
# Store the text chunks into MongoDB (or PostgreSQL and other relational databases)
client = MongoClient("mongodb://localhost:27017/")
db = client["ps_rag"]
col = db["pdf_chunks"]
# Clear the collection before inserting data
col.delete_many({})
docs = [{"chunk_id": i, "text": chunk} for i, chunk in enumerate(chunks)]
col.insert_many(docs)
print("Number of text chunks saved to the database:", col.count_documents({}))