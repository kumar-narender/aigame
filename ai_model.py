# Standard library imports
import json
import numpy as np
import joblib
import os

# Scikit-learn imports
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.multioutput import MultiOutputRegressor

# Flask imports
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Global Configuration ---
# SEQUENCE_LENGTH should match the one used during model training.
# Based on previous steps, the model was trained with data preprocessed using sequence_length=3.
SEQUENCE_LENGTH = 3
MODEL_FILENAME = "gbm_player_model.joblib"

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- Load Model On Startup ---
model = None # Global variable to hold the loaded model

def load_global_model(filepath=MODEL_FILENAME):
    """Loads the model into the global 'model' variable."""
    global model
    try:
        if os.path.exists(filepath):
            model = joblib.load(filepath)
            print(f"--- Model '{filepath}' loaded successfully for Flask app. ---")
        else:
            print(f"--- ERROR: Model file '{filepath}' not found. Predictions will fail. ---")
            print("--- Please ensure the model is trained and available. ---")
            model = None # Ensure model is None if file not found
    except Exception as e:
        print(f"--- ERROR: Could not load model '{filepath}': {e} ---")
        model = None # Ensure model is None on other errors

# --- Core AI Functions (Preprocessing, Training, Prediction, Evaluation) ---
def preprocess_data(raw_data_list, sequence_length=SEQUENCE_LENGTH): # Use global SEQUENCE_LENGTH
    features = []
    targets = []
    if not raw_data_list or len(raw_data_list) < sequence_length + 1:
        # print(f"Not enough data to create sequences. Need at least {sequence_length + 1} states, got {len(raw_data_list)}")
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

def predict_next_state(trained_model, current_sequence_features):
    """
    Predicts the next game state.
    Note: 'trained_model' here refers to the globally loaded 'model'.
    """
    if trained_model is None:
        print("Error: Model is not loaded. Cannot predict.")
        return None # Or raise an error, or return a specific error response
    if current_sequence_features is None:
        print("Error: Input sequence is None for prediction.")
        return None
    try:
        # Ensure input is a NumPy array before reshaping
        if not isinstance(current_sequence_features, np.ndarray):
            sequence_array = np.array(current_sequence_features)
        else:
            sequence_array = current_sequence_features

        # Validate sequence length (expected: SEQUENCE_LENGTH * 4 features)
        expected_feature_length = SEQUENCE_LENGTH * 4
        if sequence_array.ndim == 1 and sequence_array.shape[0] != expected_feature_length:
            print(f"Error: Incorrect sequence length. Expected {expected_feature_length}, got {sequence_array.shape[0]}")
            return None

        reshaped_features = sequence_array.reshape(1, -1)
        prediction = trained_model.predict(reshaped_features)
        predicted_x = prediction[0, 0]
        predicted_y = prediction[0, 1]
        return {'x': predicted_x, 'y': predicted_y}
    except Exception as e:
        print(f"Error during prediction: {e}")
        return None

def save_trained_model(model_to_save, filepath=MODEL_FILENAME):
    try:
        joblib.dump(model_to_save, filepath)
        print(f"Model saved to {filepath}")
    except Exception as e:
        print(f"Error saving model to {filepath}: {e}")

# This function is for loading models for training/evaluation, distinct from global model
def load_model_for_offline_tasks(filepath=MODEL_FILENAME):
    try:
        loaded_model = joblib.load(filepath)
        # print(f"Model loaded from {filepath} for offline tasks.")
        return loaded_model
    except FileNotFoundError:
        print(f"Error: Model file not found at {filepath}")
        return None
    except Exception as e:
        print(f"Error loading model from {filepath}: {e}")
        return None

def evaluate_model_performance(model_to_evaluate, test_features, test_targets):
    if model_to_evaluate is None or test_features is None or test_targets is None or test_features.shape[0] == 0:
        print("Error: Missing model, features, or targets for evaluation, or test_features is empty.")
        return None
    try:
        predictions = model_to_evaluate.predict(test_features)
        mse_x = mean_squared_error(test_targets[:, 0], predictions[:, 0])
        mse_y = mean_squared_error(test_targets[:, 1], predictions[:, 1])
        mse_overall = mean_squared_error(test_targets, predictions)
        # print(f"Model Evaluation MSE - X: {mse_x:.4f}")
        # print(f"Model Evaluation MSE - Y: {mse_y:.4f}")
        # print(f"Model Evaluation MSE - Overall: {mse_overall:.4f}")
        return {'mse_x': mse_x, 'mse_y': mse_y, 'mse_overall': mse_overall}
    except Exception as e:
        print(f"Error during model evaluation: {e}")
        return None

# --- Flask Routes ---
@app.route("/predict", methods=["POST"])
def handle_predict():
    global model # Ensure we're using the globally loaded model
    if model is None:
        return jsonify({"error": "Model not loaded on server"}), 500

    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    current_sequence = data.get("current_sequence")
    if current_sequence is None:
        return jsonify({"error": "Missing 'current_sequence' in request"}), 400

    # Validate sequence type (should be a list of numbers)
    if not isinstance(current_sequence, list) or not all(isinstance(item, (int, float)) for item in current_sequence):
        return jsonify({"error": "'current_sequence' must be a list of numbers"}), 400

    # Validate sequence length
    expected_length = SEQUENCE_LENGTH * 4
    if len(current_sequence) != expected_length:
        return jsonify({"error": f"Invalid sequence length. Expected {expected_length}, got {len(current_sequence)}"}), 400

    try:
        sequence_array = np.array(current_sequence) # Already validated as list of numbers
        predicted_state = predict_next_state(model, sequence_array) # Call with global model

        if predicted_state:
            return jsonify(predicted_state)
        else:
            # predict_next_state would have printed an error, return a generic server error
            return jsonify({"error": "Prediction failed on server"}), 500
    except Exception as e:
        print(f"Exception in /predict: {e}") # Log server-side
        return jsonify({"error": "An unexpected error occurred during prediction."}), 500

@app.route("/status", methods=["GET"])
def handle_status():
    global model
    if model is not None:
        return jsonify({"status": "Model loaded. Server is ready for predictions."})
    else:
        return jsonify({"status": "Model not loaded. Server is NOT ready."}), 500

# --- Main Execution Block ---
if __name__ == "__main__":
    # Load the model when the script starts
    load_global_model() # Loads into global 'model' variable

    # Start the Flask development server
    print(f"--- Starting Flask server on port 5000 with SEQUENCE_LENGTH={SEQUENCE_LENGTH}... ---")
    app.run(debug=True, port=5000, use_reloader=False) # use_reloader=False is good for stable model loading

    # --------------------------------------------------------------------
    # The offline training and evaluation code is commented out below.
    # To run it, you would typically call it from a separate script or
    # use command-line arguments to switch between server mode and train mode.
    # --------------------------------------------------------------------
    """
    print("--- AI Model Script: Offline Training/Evaluation Mode (Not Server) ---")

    data_filename = "player_data.json" # Make sure this file exists from previous steps or game data export

    if not os.path.exists(data_filename):
        print(f"'{data_filename}' not found. Creating a sample file for demonstration.")
        sample_data = [
            {"x": 50, "y": 400, "vx": 1, "vy": 0, "time": 1000},
            {"x": 51, "y": 400, "vx": 1, "vy": 0, "time": 1016},
            {"x": 52, "y": 400, "vx": 1, "vy": 0, "time": 1032},
            {"x": 53, "y": 401, "vx": 1, "vy": 1, "time": 1048},
            {"x": 54, "y": 402, "vx": 1, "vy": 1, "time": 1064},
            {"x": 55, "y": 403, "vx": 1, "vy": 1, "time": 1080},
            {"x": 56, "y": 404, "vx": 1, "vy": 1, "time": 1096},
            {"x": 57, "y": 405, "vx": 0, "vy": 1, "time": 1112},
            {"x": 57, "y": 406, "vx": 0, "vy": 1, "time": 1128},
            {"x": 57, "y": 407, "vx": 0, "vy": 1, "time": 1144}
        ]
        with open(data_filename, 'w') as f:
            json.dump(sample_data, f, indent=4)
        print(f"Sample '{data_filename}' created with {len(sample_data)} records.")

    print(f"\nLoading data from '{data_filename}'...")
    try:
        with open(data_filename, 'r') as f:
            raw_player_data = json.load(f)
        print(f"Data loaded successfully. Number of records: {len(raw_player_data)}")
    except FileNotFoundError:
        print(f"Error: Could not find '{data_filename}'. Please ensure it exists.")
        raw_player_data = []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{data_filename}'.")
        raw_player_data = []

    features_offline = np.array([])
    targets_offline = np.array([])

    if raw_player_data:
        print(f"\nPreprocessing data with sequence length {SEQUENCE_LENGTH}...")
        features_offline, targets_offline = preprocess_data(raw_player_data) # Uses global SEQUENCE_LENGTH

        if features_offline.size > 0 and targets_offline.size > 0:
            print(f"Preprocessing complete. Features shape: {features_offline.shape}, Targets shape: {targets_offline.shape}")

            if features_offline.shape[0] < 2 :
                 print("Not enough samples to perform train-test split. Skipping further steps.")
            else:
                print("\nSplitting data into training and testing sets...")
                train_features, test_features, train_targets, test_targets = train_test_split(
                    features_offline, targets_offline, test_size=0.2, random_state=42
                )
                print(f"Train features shape: {train_features.shape}, Train targets shape: {train_targets.shape}")
                print(f"Test features shape: {test_features.shape}, Test targets shape: {test_targets.shape}")

                if train_features.shape[0] == 0 or test_features.shape[0] == 0:
                    print("Not enough data in train or test split after splitting. Skipping training and evaluation.")
                else:
                    print("\nTraining Gradient Boosting model on training data...")
                    custom_params = {
                        'n_estimators': 100, 'learning_rate': 0.1, 'max_depth': 3, 'random_state': 42
                    }
                    offline_trained_model = train_gradient_boosting_model(train_features, train_targets, model_params=custom_params)
                    print("Model training complete.")

                    print(f"\nSaving trained model to '{MODEL_FILENAME}'...")
                    save_trained_model(offline_trained_model, filepath=MODEL_FILENAME) # Saves to global MODEL_FILENAME

                    print("\nLoading the saved model for testing...")
                    # Load specifically for this offline test, not affecting global 'model'
                    loaded_offline_model = load_model_for_offline_tasks(filepath=MODEL_FILENAME)

                    if loaded_offline_model:
                        print("\n--- Prediction Test (using first test sample) ---")
                        sample_seq_features = test_features[0]
                        # Use the predict_next_state with the model loaded for offline tasks
                        predicted_offline_state = predict_next_state(loaded_offline_model, sample_seq_features)
                        if predicted_offline_state:
                            print(f"Predicted next state: {predicted_offline_state}")
                        actual_offline_state = test_targets[0]
                        print(f"Actual next state (test_targets[0]): {{'x': {actual_offline_state[0]}, 'y': {actual_offline_state[1]}}}")

                        print("\n--- Model Evaluation (on test set) ---")
                        offline_eval_metrics = evaluate_model_performance(loaded_offline_model, test_features, test_targets)
                        if offline_eval_metrics:
                            print(f"Returned evaluation metrics: {offline_eval_metrics}")
                    else:
                        print("Could not load the model for offline testing.")
        else:
            print("Preprocessing resulted in no features or targets. Skipping model training, saving, and evaluation.")
    else:
        print("No data loaded. Skipping all processing.")

    print("\nAI Model script (offline mode) execution finished.")
    """
