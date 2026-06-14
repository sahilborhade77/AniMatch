import os
import torch
from sentence_transformers import SentenceTransformer

# WARNING: This script requires `torch` and `sentence-transformers` locally.
# These must NOT be added to requirements.txt as they exceed the 120MB Render memory budget.

def export():
    # 1. Load model
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    print(f"Loading SentenceTransformer model: {model_name}...")
    model = SentenceTransformer(model_name)
    
    # Get the underlying transformer model and tokenizer
    transformer = model[0].auto_model
    tokenizer = model[0].tokenizer.backend_tokenizer

    # 2. Prepare paths
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "models"))
    os.makedirs(output_dir, exist_ok=True)
    
    model_path = os.path.join(output_dir, "model.onnx")
    tokenizer_path = os.path.join(output_dir, "tokenizer.json")

    # 3. Export Tokenizer
    print("Saving tokenizer vocabulary to tokenizer.json...")
    tokenizer.save(tokenizer_path)

    # 4. Export Model to ONNX
    print("Exporting model to ONNX format...")
    dummy_text = "test query"
    encoded_input = model[0].tokenizer(dummy_text, return_tensors="pt")
    
    # The transformer model expects input_ids, attention_mask, token_type_ids
    input_names = ["input_ids", "attention_mask", "token_type_ids"]
    output_names = ["last_hidden_state", "pooler_output"]
    
    # We care about the last_hidden_state (token embeddings) for mean pooling
    dynamic_axes = {
        "input_ids": {0: "batch_size", 1: "sequence_length"},
        "attention_mask": {0: "batch_size", 1: "sequence_length"},
        "token_type_ids": {0: "batch_size", 1: "sequence_length"},
        "last_hidden_state": {0: "batch_size", 1: "sequence_length"},
        "pooler_output": {0: "batch_size"}
    }

    # Ensure evaluation mode
    transformer.eval()
    
    with torch.no_grad():
        torch.onnx.export(
            transformer,
            args=(
                encoded_input["input_ids"],
                encoded_input["attention_mask"],
                encoded_input["token_type_ids"]
            ),
            f=model_path,
            input_names=input_names,
            output_names=output_names,
            dynamic_axes=dynamic_axes,
            opset_version=14,
            do_constant_folding=True
        )

    size_mb = os.path.getsize(model_path) / (1024 * 1024)
    print(f"Model exported to model.onnx — {size_mb:.2f} MB")

if __name__ == "__main__":
    export()
