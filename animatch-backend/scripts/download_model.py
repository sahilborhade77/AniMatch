import os
import urllib.request

def download_file(url, dest):
    print(f"Downloading {url} to {dest}...")
    urllib.request.urlretrieve(url, dest)
    print(f"Successfully downloaded to {dest}")

def main():
    dest_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "models"))
    os.makedirs(dest_dir, exist_ok=True)
    
    model_url = "https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/onnx/model.onnx"
    tokenizer_url = "https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/tokenizer.json"
    
    download_file(model_url, os.path.join(dest_dir, "model.onnx"))
    download_file(tokenizer_url, os.path.join(dest_dir, "tokenizer.json"))
    print("All model files downloaded successfully.")

if __name__ == "__main__":
    main()
