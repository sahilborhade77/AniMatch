import os
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

# Path setup
model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "models"))
model_path = os.path.join(model_dir, "model.onnx")
tokenizer_path = os.path.join(model_dir, "tokenizer.json")

# Ensure models are loaded as a singleton once at module import time
if not os.path.exists(model_path) or not os.path.exists(tokenizer_path):
    raise FileNotFoundError(
        f"Model or tokenizer not found at {model_dir}. Run the download script first."
    )

# Load the ONNX model and the tokenizer
session = ort.InferenceSession(model_path)
tokenizer = Tokenizer.from_file(tokenizer_path)

# Query inputs to dynamically match expected session parameters
session_input_names = [inp.name for inp in session.get_inputs()]

def encode(text: str) -> list[float]:
    """
    Tokenizes the input text, runs the ONNX session, applies mean pooling
    over token embeddings, L2-normalizes the output, and returns a list of 384 floats.
    """
    if not text:
        return [0.0] * 384

    # Tokenize input text using tokenizers library
    encoded = tokenizer.encode(text)
    
    # Construct input arrays of shape (1, sequence_length)
    input_ids = np.array([encoded.ids], dtype=np.int64)
    attention_mask = np.array([encoded.attention_mask], dtype=np.int64)
    
    inputs = {
        "input_ids": input_ids,
        "attention_mask": attention_mask
    }
    
    # Only include token_type_ids if expected by the exported ONNX model
    if "token_type_ids" in session_input_names:
        token_type_ids = np.array([encoded.type_ids], dtype=np.int64)
        inputs["token_type_ids"] = token_type_ids

    # Run ONNX session
    outputs = session.run(None, inputs)
    
    # Perform mean pooling
    # outputs[0] is token_embeddings of shape (batch_size, sequence_length, hidden_size)
    token_embeddings = outputs[0]
    
    # Expand attention mask to match token embeddings shape (batch_size, sequence_length, 1)
    input_mask_expanded = np.expand_dims(attention_mask, axis=-1)
    input_mask_expanded = np.broadcast_to(input_mask_expanded, token_embeddings.shape).astype(float)
    
    # Calculate sum of token embeddings weighted by attention mask
    sum_embeddings = np.sum(token_embeddings * input_mask_expanded, axis=1)
    
    # Calculate sum of attention masks (clip to avoid division by zero)
    sum_mask = np.clip(np.sum(input_mask_expanded, axis=1), a_min=1e-9, a_max=None)
    
    # Get the pooled vector for batch index 0
    embedding = (sum_embeddings / sum_mask)[0]
    
    # L2-normalize
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
        
    return embedding.tolist()

if __name__ == "__main__":
    # Standard test query validation
    test_query = "test query"
    vector = encode(test_query)
    print(f"Successfully encoded '{test_query}'")
    print(f"Vector dimensions: {len(vector)}")
    print(f"First 5 dimensions: {vector[:5]}")
