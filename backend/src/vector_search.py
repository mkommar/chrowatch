import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def cosine_similarity_search(query_vector, database_vectors, top_k=5):
    # Ensure query_vector is 2D
    if query_vector.ndim == 1:
        query_vector = query_vector.reshape(1, -1)
    
    # Ensure database_vectors is 2D
    if database_vectors.ndim == 1:
        database_vectors = database_vectors.reshape(1, -1)
    elif database_vectors.ndim > 2:
        database_vectors = database_vectors.reshape(database_vectors.shape[0], -1)
    
    similarities = cosine_similarity(query_vector, database_vectors)
    top_indices = np.argsort(similarities[0])[-top_k:][::-1]
    return top_indices, similarities[0][top_indices]