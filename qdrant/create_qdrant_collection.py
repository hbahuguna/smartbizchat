from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, PointStruct

# Initialize the embedding model and Qdrant client
model = SentenceTransformer("all-MiniLM-L6-v2")  # Replace with your preferred model
client = QdrantClient(host="localhost", port=6333)

# Load the text file
file_path = "bizbooster.txt"  # Replace with your file path
with open(file_path, "r") as file:
    text = file.read()

# Split text into chunks (e.g., by sentences or paragraphs)
def split_text(text, chunk_size=100):
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield " ".join(words[i:i + chunk_size])

chunks = list(split_text(text, chunk_size=100))

# Generate embeddings for each chunk
embeddings = model.encode(chunks)

# Create a Qdrant collection
collection_name = "rag_collection"
vector_size = len(embeddings[0])  # Get the size of the embeddings

client.recreate_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=vector_size, distance="Cosine")
)

# Add chunks to the collection
points = [
    PointStruct(
        id=index,
        vector=embedding.tolist(),
        payload={"text": chunk}
    )
    for index, (chunk, embedding) in enumerate(zip(chunks, embeddings))
]

client.upsert(
    collection_name=collection_name,
    points=points
)

print(f"Added {len(points)} chunks to the collection '{collection_name}'.")

