import os
import requests

SERVER_URL = 'http://127.0.0.1:5000'
CHUNK_SIZE = 1024 * 1024  # 1MB chunks
CLIENT_ID = 'very_safe_client_id'  
client_key = None  

def upload_file_in_chunks(file_path):
    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    total_chunks = (file_size // CHUNK_SIZE) + 1

    with open(file_path, 'rb') as f:
        for chunk_number in range(total_chunks):
            chunk = f.read(CHUNK_SIZE)
            files = {'file': (filename, chunk)}
            response = requests.post(
                f"{SERVER_URL}/upload",
                files=files,
                params={'client_id': CLIENT_ID, 'filename': filename, 'chunk_number': chunk_number}
            )
            if response.status_code != 200:
                print(f"Failed to upload chunk {chunk_number}")
                return False
    return True

def merge_chunks(filename, total_chunks):
    global client_key
    response = requests.post(
        f"{SERVER_URL}/merge",
        params={'client_id': CLIENT_ID, 'filename': filename, 'total_chunks': total_chunks}
    )
    if response.status_code == 200:
        client_key = response.json().get('key')
        print("File merged successfully. Received key:", client_key)
    else:
        print("Failed to merge file.")

def train_model(data_path):
    response = requests.post(
        f"{SERVER_URL}/train",
        json={'data_path': data_path}
    )
    if response.status_code == 200:
        print("Model trained successfully.")
        print("Accuracy:", response.json()['accuracy'])
    else:
        print("Failed to train model:", response.json()['message'])

def predict(data):
    global client_key
    response = requests.post(
        f"{SERVER_URL}/predict",
        json={"client_id": CLIENT_ID, "key": client_key, "data": data}
    )
    if response.status_code == 200:
        print("Prediction:", response.json()['prediction'])
    else:
        print("Failed to get prediction:", response.json()['message'])

if __name__ == "__main__":
    file_path = 'Iris.csv'  
    if upload_file_in_chunks(file_path):
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        total_chunks = (file_size // CHUNK_SIZE) + 1
        merge_chunks(filename, total_chunks)
        train_model(os.path.join('uploads', filename))
        sample_data = [5.1, 3.5, 1.4, 0.2]  # Example data for prediction
        predict(sample_data)
