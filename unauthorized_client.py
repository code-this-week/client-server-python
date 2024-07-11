import requests

SERVER_URL = 'http://127.0.0.1:5000'
CLIENT_ID = 'shady_client_id'  
client_key = 'I really hope this key works somehow' 
def predict(data):
    response = requests.post(
        f"{SERVER_URL}/predict",
        json={"client_id": CLIENT_ID, "key": client_key, "data": data}
    )
    if response.status_code == 200:
        print("Prediction:", response.json()['prediction'])
    else:
        print("Failed to get prediction:", response.json()['message'])

if __name__ == "__main__":
    sample_data = [5.1, 3.5, 1.4, 0.2]  
    predict(sample_data)
