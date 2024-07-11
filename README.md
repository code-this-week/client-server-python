## Endpoints

### 1. `/upload` (POST)

- **Purpose**: Uploads chunks of a dataset.
- **Parameters**:
  - `client_id`: Unique identifier for the client.
  - `file`: Chunk of the dataset file.
  - `filename`: Name of the dataset file.
  - `chunk_number`: The chunk number being uploaded.
- **Response**: `200 OK` on successful upload.

### 2. `/merge` (POST)

- **Purpose**: Merges all uploaded chunks into a single dataset file.
- **Parameters**:
  - `client_id`: Unique identifier for the client.
  - `filename`: Name of the dataset file.
  - `total_chunks`: Total number of chunks to be merged.
- **Response**: `200 OK` with a JSON object containing the unique key.

### 3. `/train` (POST)

- **Purpose**: Trains an SVM model using the uploaded dataset.
- **Parameters**:
  - `data_path`: Path to the dataset file.
- **Response**: `200 OK` with the model's accuracy.

### 4. `/predict` (POST)

- **Purpose**: Predicts the class of new data using the trained model.
- **Parameters**:
  - `client_id`: Unique identifier for the client.
  - `key`: Unique key received after merging the dataset.
  - `data`: New data for which the prediction is to be made.
- **Response**: `200 OK` with the prediction or `403 Forbidden` if the client is unauthorized.

## Client Scripts

### `client.py`

The client script interacts with the server to upload dataset chunks, merge them, train the model, and make predictions.

- **Usage**:
  1. Upload the dataset in chunks.
  2. Merge the chunks.
  3. Train the model.
  4. Make a prediction.

### `unauthorized_client.py`

The unauthorized client script attempts to make a prediction without having uploaded a dataset and without a valid key.

- **Usage**: 
  - Attempt to make a prediction. The server should deny this request.


### Using SHA-256 for Security


1. **Key Generation During Merge**:
    - When a client uploads all chunks of a dataset and requests to merge them, the server generates a unique SHA-256 hash (key) using the `client_id` and the combined dataset contents.
    - This key is stored on the server and sent back to the client.

2. **Key Verification During Prediction**:
    - When a client requests a prediction, it must provide the `client_id` and the unique key.
    - The server verifies the provided key against the stored key.
    - If the keys match, the prediction is processed. If not, the request is denied.

### Code Details

#### Key Generation in `server.py`:

```python
def generate_hash(client_id, data):
    hash_object = hashlib.sha256()
    hash_object.update(client_id.encode('utf-8'))
    hash_object.update(data)
    return hash_object.hexdigest()

@app.route('/merge', methods=['POST'])
def merge_chunks():
    client_id = request.args.get('client_id')
    filename = request.args.get('filename')
    total_chunks = int(request.args.get('total_chunks'))
    
    with open(os.path.join(UPLOAD_FOLDER, filename), 'wb') as f:
        for i in range(total_chunks):
            chunk_file = os.path.join(UPLOAD_FOLDER, f"{filename}.part{i}")
            with open(chunk_file, 'rb') as cf:
                f.write(cf.read())
            os.remove(chunk_file)

    # Generate and store the key
    with open(os.path.join(UPLOAD_FOLDER, filename), 'rb') as f:
        file_data = f.read()
    client_key = generate_hash(client_id, file_data)
    with open(KEY_FILE, 'r+') as kf:
        keys = json.load(kf)
        keys[client_id] = client_key
        kf.seek(0)
        json.dump(keys, kf)

    return jsonify({"message": "File merged successfully", "key": client_key}), 200
```

#### Key Verification in `server.py`:

```python
@app.route('/predict', methods=['POST'])
def predict():
    client_id = request.json['client_id']
    client_key = request.json['key']
    data = request.json['data']
    try:
        # Verify the client key
        with open(KEY_FILE, 'r') as kf:
            keys = json.load(kf)
            if keys.get(client_id) == client_key:
                clf, scaler = joblib.load(MODEL_PATH)
                input_data = scaler.transform([data])
                prediction = clf.predict(input_data)
                return jsonify({"prediction": prediction.tolist()})
        return jsonify({"message": "Unauthorized client"}), 403
    except Exception as e:
        return jsonify({"message": f"Failed to get prediction: {str(e)}"}), 500
```


## Example Usage

1. **Upload Dataset in Chunks**:
    ```python
    if upload_file_in_chunks('Iris.csv'):
        filename = os.path.basename('Iris.csv')
        file_size = os.path.getsize('Iris.csv')
        total_chunks = (file_size // CHUNK_SIZE) + 1
        merge_chunks(filename, total_chunks)
        train_model(os.path.join('uploads', filename))
        sample_data = [5.1, 3.5, 1.4, 0.2]
        predict(sample_data)
    ```

2. **Unauthorized Client**:
    ```python
    sample_data = [5.1, 3.5, 1.4, 0.2]
    predict(sample_data)
    ```

## Files

- `server.py`: Contains the Flask server code.
- `client.py`: Authorized client script.
- `unauthorized_client.py`: Unauthorized client script.
