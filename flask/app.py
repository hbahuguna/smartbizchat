from flask import Flask, request, jsonify
import requests
import psycopg2
from flask_cors import CORS
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
CONTEXT_WINDOW = 25

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
OLLAMA_HOST = "localhost"
OLLAMA_PORT = 11434
COLLECTION_NAME = "rag_collection"

# Database configuration
DB_CONFIG = {
    "host": "localhost",  # Change if running Docker on a different host
    "port": 5432,         # Default Postgres port
    "dbname": "n8n",
    "user": "root",
    "password": "password"
}

# Initialize Qdrant Client
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# Initialize SentenceTransformer model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Replace with your preferred model


@app.route('/api/chat', methods=['POST'])
def chat():
    user_message = request.json.get("chatInput")
    if not user_message:
        return jsonify({"error": "Message is required"}), 400
    session_id = request.json.get("sessionId")
    if not session_id:
        return jsonify({"error": "SessionId is required"}), 400
    try:
        context = get_chat_context(session_id, CONTEXT_WINDOW)
        query_embedding = embed_query(user_message)
        qdrant_context = search_qdrant_collection(query_embedding, COLLECTION_NAME)
        full_context = f"{context}\n\nAdditional Context:\n{qdrant_context}"
        prompt = (
        f"You are an expert assistant. Use the following context to answer the question.\n\n"
        f"Context:\n{full_context}\n\n"
        f"Question:\n{user_message}\n\n"
        )
        url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/generate"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": "llama3.2:latest",
            "prompt": prompt,
            "format": "json",
            "temperature": 0,
            "stream": False
        }
        response = requests.post(url, json=payload, headers=headers)
        # Check if the response from Ollama is successful
        if response.status_code == 200:
            ollama_data = response.json()

            # Extract the response field
            bot_reply = ollama_data.get("response", "No response from the model.")
            bot_reply_clean = clean_response(bot_reply.strip())
            if bot_reply_clean == "{}":
                return jsonify({"error": "Failed to generate response from Ollama"}), 500
            store_message(session_id, "user", user_message)
            store_message(session_id, "assistant", bot_reply_clean)
            
            # Return the JSON response to the frontend
            return jsonify({"reply": bot_reply_clean})
        else:
            return jsonify({"error": "Failed to generate response from Ollama"}), 500

    except Exception as e:
        # Handle any exceptions that occur during the request
        return jsonify({"error": str(e)}), 500    

def connect_to_db():
    """Connect to the PostgreSQL database."""
    conn = psycopg2.connect(**DB_CONFIG)
    return conn


def store_message(session_id, role, message):
    """Store a message in the chat_history table."""
    conn = connect_to_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO chat_history (session_id, role, message) VALUES (%s, %s, %s)",
                (session_id, role, message)
            )
            conn.commit()
    finally:
        conn.close()


def get_chat_context(session_id, context_window=25):
    """
    Retrieve the last `context_window` messages for the given session_id.
    Args:
        session_id (str): The session ID to filter messages.
        context_window (int): Number of messages to include in context.
    Returns:
        str: Combined context from the retrieved messages.
    """
    conn = connect_to_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT role, message FROM chat_history
                WHERE session_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (session_id, context_window)
            )
            messages = cursor.fetchall()
    finally:
        conn.close()

    # Combine messages into a single context string
    context = "\n".join(f"{role.capitalize()}: {message}" for role, message in reversed(messages))
    return context

def clean_response(input_string):
    import re

    # Remove curly braces
    input_string = input_string.strip("{}")

    # Use regex to remove field names like 'field_name:'
    cleaned_string = re.sub(r'"\w+":\s*', '', input_string)

    # Remove unnecessary double quotes
    cleaned_string = cleaned_string.replace('"', '').strip()

    return cleaned_string

def search_qdrant_collection(query_embedding, collection_name, top_k=5):
    """
    Perform a similarity search in the specified Qdrant collection.
    Args:
        query_embedding (list): Embedding of the query.
        collection_name (str): Name of the Qdrant collection.
        top_k (int): Number of top results to retrieve.

    Returns:
        str: Combined context from the retrieved documents.
    """
    results = qdrant_client.search(
        collection_name=collection_name,
        query_vector=query_embedding,
        limit=top_k
    )

    # Extract text payloads
    context_chunks = [result.payload.get("text", "") for result in results]
    #print("Retrieved Context Chunks:", context_chunks)

    # Combine context into a single string
    context = "\n".join(context_chunks)
    return context


def embed_query(query):
    """
    Generate an embedding for the query using SentenceTransformers.
    Args:
        query (str): Query string to embed.

    Returns:
        list: Query embedding.
    """
    embedding = embedding_model.encode(query).tolist()  # Generate and convert to a list
    #print("Generated Query Embedding:", embedding)
    return embedding


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, ssl_context=("/root/ssl_cert.pem", "/root/ssl_key.pem"))

