from flask import Flask, request, jsonify
import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
import joblib
import hashlib
import json

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
MODEL_PATH = 'svm_model.pkl'
KEY_FILE = 'client_keys.json'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'w') as f:
        json.dump({}, f)

def generate_hash(client_id, data):
    hash_object = hashlib.sha256()
    hash_object.update(client_id.encode('utf-8'))
    hash_object.update(data)
    return hash_object.hexdigest()

@app.route('/upload', methods=['POST'])
def upload_chunk():
    client_id = request.args.get('client_id')
    file = request.files['file']
    filename = request.args.get('filename')
    chunk_number = request.args.get('chunk_number')
    
    file_path = os.path.join(UPLOAD_FOLDER, f"{filename}.part{chunk_number}")
    with open(file_path, 'wb') as f:
        f.write(file.read())

    return 'Chunk uploaded successfully', 200

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

@app.route('/train', methods=['POST'])
def train_model():
    data_path = request.json['data_path']
    try:
        df = pd.read_csv(data_path)
        X = df.drop(['Id', 'Species'], axis=1)
        y = df['Species']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

        clf = SVC(kernel='linear')
        clf.fit(X_train, y_train)

        joblib.dump((clf, scaler), MODEL_PATH)

        accuracy = clf.score(X_test, y_test)
        return jsonify({"message": "Model trained successfully", "accuracy": accuracy})
    except Exception as e:
        return jsonify({"message": f"Failed to train model: {str(e)}"}), 500

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

if __name__ == '__main__':
    app.run(debug=True)
