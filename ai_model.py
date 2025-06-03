# Standard library imports
import json
import numpy as np
import joblib
import os
import argparse # Added for command-line arguments

# Scikit-learn imports
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.multioutput import MultiOutputRegressor

# Flask imports
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Global Configuration ---
SEQUENCE_LENGTH = 3
MODEL_FILENAME = "gbm_player_model.joblib"
DATA_FILENAME = "player_data.json" # Used by offline training

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)

# --- Global Model Variable ---
model = None # Global variable to hold the loaded model for the server

# --- Model Loading for Server ---
def load_global_model(filepath=MODEL_FILENAME):
    """Loads the model into the global 'model' variable for the Flask server."""
    global model
    try:
        if os.path.exists(filepath):
            model = joblib.load(filepath)
            print(f"--- Model '{filepath}' loaded successfully for Flask app. ---")
        else:
            print(f"--- SERVER ERROR: Model file '{filepath}' not found. Predictions will fail. ---")
            print(f"--- Please run training mode first: python ai_model.py --mode train ---")
            model = None
    except Exception as e:
        print(f"--- SERVER ERROR: Could not load model '{filepath}': {e} ---")
        model = None

# --- Core AI Functions ---
def preprocess_data(raw_data_list, sequence_length=SEQUENCE_LENGTH):
    features = []
    targets = []
    if not raw_data_list or len(raw_data_list) < sequence_length + 1:
        return np.array([]), np.array([])
    for i in range(len(raw_data_list) - sequence_length):
        sequence = raw_data_list[i : i + sequence_length]
        target_state = raw_data_list[i + sequence_length]
        current_features = []
        for state in sequence:
            current_features.extend([state['x'], state['y'], state['vx'], state['vy']])
        features.append(current_features)
        targets.append([target_state['x'], target_state['y']])
    if not features:
        return np.array([]), np.array([])
    return np.array(features), np.array(targets)

def train_gradient_boosting_model(features, targets, model_params=None):
    if model_params is None:
        model_params = {
            'n_estimators': 100, 'learning_rate': 0.1, 'max_depth': 3, 'random_state': 42
        }
    base_regressor = GradientBoostingRegressor(**model_params)
    multi_output_model = MultiOutputRegressor(base_regressor)
    multi_output_model.fit(features, targets)
    return multi_output_model

def predict_next_state(trained_model_instance, current_sequence_features):
    if trained_model_instance is None:
        print("Error: Model (instance) is not loaded/provided. Cannot predict.")
        return None
    if current_sequence_features is None:
        print("Error: Input sequence is None for prediction.")
        return None
    try:
        if not isinstance(current_sequence_features, np.ndarray):
            sequence_array = np.array(current_sequence_features)
        else:
            sequence_array = current_sequence_features

        expected_feature_length = SEQUENCE_LENGTH * 4
        if sequence_array.ndim == 1 and sequence_array.shape[0] != expected_feature_length:
            print(f"Error: Incorrect sequence length for prediction. Expected {expected_feature_length}, got {sequence_array.shape[0]}")
            return None

        reshaped_features = sequence_array.reshape(1, -1)
        prediction = trained_model_instance.predict(reshaped_features)
        return {'x': prediction[0, 0], 'y': prediction[0, 1]}
    except Exception as e:
        print(f"Error during prediction: {e}")
        return None

def save_trained_model(model_to_save, filepath=MODEL_FILENAME):
    try:
        joblib.dump(model_to_save, filepath)
        print(f"Model saved to {filepath}")
    except Exception as e:
        print(f"Error saving model to {filepath}: {e}")

def load_model_for_evaluation(filepath=MODEL_FILENAME): # Renamed for clarity
    try:
        loaded_model = joblib.load(filepath)
        return loaded_model
    except FileNotFoundError:
        print(f"Error (offline load): Model file not found at {filepath}")
        return None
    except Exception as e:
        print(f"Error (offline load): Could not load model from {filepath}: {e}")
        return None

def evaluate_model_performance(model_to_evaluate, test_features, test_targets):
    if model_to_evaluate is None or test_features.size == 0 or test_targets.size == 0:
        print("Error: Missing model, features, or targets for evaluation.")
        return None
    try:
        predictions = model_to_evaluate.predict(test_features)
        mse_x = mean_squared_error(test_targets[:, 0], predictions[:, 0])
        mse_y = mean_squared_error(test_targets[:, 1], predictions[:, 1])
        mse_overall = mean_squared_error(test_targets, predictions)
        print(f"  Model Evaluation MSE - X: {mse_x:.4f}")
        print(f"  Model Evaluation MSE - Y: {mse_y:.4f}")
        print(f"  Model Evaluation MSE - Overall: {mse_overall:.4f}")
        return {'mse_x': mse_x, 'mse_y': mse_y, 'mse_overall': mse_overall}
    except Exception as e:
        print(f"Error during model evaluation: {e}")
        return None

# --- Flask Routes ---
@app.route("/predict", methods=["POST"])
def handle_predict():
    global model # Uses the globally loaded model for the server
    if model is None:
        return jsonify({"error": "Model not loaded on server. Please ensure it's trained and server restarted."}), 500

    data = request.get_json()
    if not data: return jsonify({"error": "No input data provided"}), 400
    current_sequence = data.get("current_sequence")
    if current_sequence is None: return jsonify({"error": "Missing 'current_sequence'"}), 400
    if not isinstance(current_sequence, list) or not all(isinstance(item, (int, float)) for item in current_sequence):
        return jsonify({"error": "'current_sequence' must be a list of numbers"}), 400

    expected_length = SEQUENCE_LENGTH * 4
    if len(current_sequence) != expected_length:
        return jsonify({"error": f"Invalid sequence length. Expected {expected_length}, got {len(current_sequence)}"}), 400

    predicted_state = predict_next_state(model, np.array(current_sequence)) # Pass global server model
    if predicted_state:
        return jsonify(predicted_state)
    else:
        return jsonify({"error": "Prediction failed on server"}), 500

@app.route("/status", methods=["GET"])
def handle_status():
    global model
    if model is not None:
        return jsonify({"status": "Model loaded. Server is ready for predictions."})
    else:
        return jsonify({"status": f"Model '{MODEL_FILENAME}' not loaded. Server is NOT ready."}), 500

# --- Offline Training Pipeline Function ---
def run_offline_training_pipeline():
    print("--- Running Offline Training Pipeline ---")

    # Ensure sample data file exists (or create it)
    if not os.path.exists(DATA_FILENAME):
        print(f"'{DATA_FILENAME}' not found. Creating a sample file.")
        sample_data = [
            {"x": 50, "y": 400, "vx": 1, "vy": 0, "time": 1000}, {"x": 51, "y": 400, "vx": 1, "vy": 0, "time": 1016},
            {"x": 52, "y": 400, "vx": 1, "vy": 0, "time": 1032}, {"x": 53, "y": 401, "vx": 1, "vy": 1, "time": 1048},
            {"x": 54, "y": 402, "vx": 1, "vy": 1, "time": 1064}, {"x": 55, "y": 403, "vx": 1, "vy": 1, "time": 1080},
            {"x": 56, "y": 404, "vx": 1, "vy": 1, "time": 1096}, {"x": 57, "y": 405, "vx": 0, "vy": 1, "time": 1112},
            {"x": 57, "y": 406, "vx": 0, "vy": 1, "time": 1128}, {"x": 57, "y": 407, "vx": 0, "vy": 1, "time": 1144}
        ]
        with open(DATA_FILENAME, 'w') as f:
            json.dump(sample_data, f, indent=4)
        print(f"Sample '{DATA_FILENAME}' created with {len(sample_data)} records.")

    print(f"\n1. Loading data from '{DATA_FILENAME}'...")
    try:
        with open(DATA_FILENAME, 'r') as f:
            raw_player_data = json.load(f)
        print(f"   Data loaded successfully. Number of records: {len(raw_player_data)}")
    except FileNotFoundError:
        print(f"   Error: Could not find '{DATA_FILENAME}'.")
        return # Stop pipeline if data not found
    except json.JSONDecodeError:
        print(f"   Error: Could not decode JSON from '{DATA_FILENAME}'.")
        return

    print(f"\n2. Preprocessing data with SEQUENCE_LENGTH={SEQUENCE_LENGTH}...")
    features, targets = preprocess_data(raw_player_data) # Uses global SEQUENCE_LENGTH

    if features.size == 0 or targets.size == 0:
        print("   Preprocessing resulted in no features or targets. Halting pipeline.")
        return
    print(f"   Preprocessing complete. Features shape: {features.shape}, Targets shape: {targets.shape}")

    if features.shape[0] < 2:
         print("   Not enough samples to perform train-test split. Halting pipeline.")
         return

    print("\n3. Splitting data into training and testing sets (test_size=0.2)...")
    train_features, test_features, train_targets, test_targets = train_test_split(
        features, targets, test_size=0.2, random_state=42
    )
    print(f"   Train features: {train_features.shape}, Train targets: {train_targets.shape}")
    print(f"   Test features: {test_features.shape}, Test targets: {test_targets.shape}")

    if train_features.shape[0] == 0 or test_features.shape[0] == 0:
        print("   Not enough data in train or test split. Halting pipeline.")
        return

    print("\n4. Training Gradient Boosting model on training data...")
    custom_params = {'n_estimators': 100, 'learning_rate': 0.1, 'max_depth': 3, 'random_state': 42}
    trained_offline_model = train_gradient_boosting_model(train_features, train_targets, model_params=custom_params)
    print("   Model training complete.")

    print(f"\n5. Saving trained model to '{MODEL_FILENAME}'...")
    save_trained_model(trained_offline_model, filepath=MODEL_FILENAME)

    print("\n6. Loading the saved model for verification...")
    loaded_offline_model = load_model_for_evaluation(filepath=MODEL_FILENAME)

    if loaded_offline_model:
        print("   Model loaded successfully for verification.")
        print("\n7. Prediction Test (using first test sample)...")
        if test_features.size > 0:
            sample_seq_features = test_features[0]
            print(f"   Sample input sequence (test_features[0]):\n   {sample_seq_features}")
            # Pass the loaded model instance to predict_next_state
            predicted_offline_state = predict_next_state(loaded_offline_model, sample_seq_features)
            if predicted_offline_state:
                print(f"   Predicted next state: {predicted_offline_state}")
            actual_offline_state = test_targets[0]
            print(f"   Actual next state (test_targets[0]): {{'x': {actual_offline_state[0]}, 'y': {actual_offline_state[1]}}}")
        else:
            print("   Skipping prediction test as no test features are available.")

        print("\n8. Model Evaluation (on test set)...")
        offline_eval_metrics = evaluate_model_performance(loaded_offline_model, test_features, test_targets)
        if offline_eval_metrics:
            print(f"   Returned evaluation metrics: {offline_eval_metrics}")
    else:
        print("   Could not load the model for verification. Skipping tests.")
    print("\n--- Offline Training Pipeline Finished ---")

# --- Main Execution Block ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Model Server and Trainer")
    parser.add_argument(
        "--mode",
        type=str,
        default="server",
        choices=["server", "train"],
        help="Execution mode: 'server' to start the Flask server, 'train' to run the offline training pipeline."
    )
    args = parser.parse_args()

    if args.mode == "train":
        run_offline_training_pipeline()
    else: # Default or --mode server
        print(f"--- Starting Flask Server Mode (SEQUENCE_LENGTH={SEQUENCE_LENGTH}) ---")
        load_global_model() # Load model into global 'model' for the server
        print(f"--- Starting Flask app on http://localhost:5000 ---")
        # Setting use_reloader=False can be helpful for stability with global model object
        app.run(debug=True, port=5000, use_reloader=False)
