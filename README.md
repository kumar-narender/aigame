# Advanced AI Space Shooter Game

## Overview
This project features an interactive Space Shooter game built with HTML and JavaScript, integrated with a Python-based AI that predicts player movement. The AI uses a Gradient Boosting Regressor model from `scikit-learn` and serves predictions in real-time via a local Python Flask server.

## Features
*   Interactive Space Shooter game implemented in HTML, CSS, and JavaScript.
*   Python-based AI for player movement prediction using `scikit-learn`'s Gradient Boosting Regressor.
*   Real-time AI predictions served via a local Python Flask server.
*   Mechanism for exporting player movement data (`player_data.json`) from the game.
*   Functionality to retrain the AI model with newly collected player data.

## AI System Architecture

*   **Game Client (`index.html`)**:
    *   Handles core game logic, rendering, and user input.
    *   Records player movement history.
    *   Can export player movement history as `player_data.json`.
    *   Sends recent player movement sequences to the AI server for predictions.
    *   (Currently, server predictions are logged to the console; game elements do not yet dynamically use them).

*   **AI Server (`ai_model.py`)**:
    *   A Python Flask application.
    *   Loads a pre-trained Gradient Boosting model (`gbm_player_model.joblib`) on startup.
    *   Exposes a `/predict` endpoint (POST) that accepts a sequence of player movements and returns predicted next `x, y` coordinates.
    *   Exposes a `/status` endpoint (GET) to check if the model is loaded and the server is ready.
    *   Can be run in a separate `--mode train` to re-process `player_data.json`, retrain the model, and save it.

## Project Structure
```
.
├── README.md               # This documentation file
├── index.html              # Main HTML file with game logic (JavaScript, CSS)
├── ai_model.py             # Python script for AI model (training, Flask server)
├── player_data.json        # Stores player movement data (exported from game, used for training)
└── gbm_player_model.joblib # Saved/serialized pre-trained Gradient Boosting model
```

## Setup and Installation

### Prerequisites
*   Python 3.7+
*   `pip` (Python package installer)
*   A modern web browser (e.g., Chrome, Firefox)

### 1. Clone the Repository
Download the project files or clone the repository:
```bash
git clone <repository_url>
cd <repository_directory_name>
```
(Replace `<repository_url>` and `<repository_directory_name>` accordingly)

### 2. Python Dependencies
Install the required Python packages. It's recommended to use a virtual environment.
```bash
pip install Flask flask-cors scikit-learn joblib numpy
```
(For larger projects, a `requirements.txt` file would typically be provided: `pip install -r requirements.txt`)

## How to Run

### 1. Start the AI Server
The AI server needs to be running first so the game can connect to it.
*   Open a terminal or command prompt.
*   Navigate to the project's root directory (where `ai_model.py` is located).
*   Run the AI server:
    ```bash
    python ai_model.py --mode server
    ```
    (Alternatively, `python ai_model.py` works as `server` is the default mode).
*   The server should start, and you'll see output indicating it's running on `http://localhost:5000`. It will also print a message about whether the `gbm_player_model.joblib` was loaded successfully. If the model file doesn't exist, it will state that predictions will fail and prompt you to run training.

### 2. Play the Game
*   Open the `index.html` file in your web browser.
*   The game interface includes an "AI STATUS" panel on the left.
    *   It will initially show "Not Connected".
    *   Once the game attempts to send data to the running server, it should update to "Connected" or indicate an "Error" if it can't reach the server.
*   Predictions received from the server are logged in the browser's developer console (Press F12 to open).

## AI Training

### 1. Collect Training Data
*   Play the game by opening `index.html` in your browser. The more varied your gameplay, the better the potential training data.
*   During or after a game session, click the **"Export Player Data"** button located in the "ML CONTROLS" panel (right side of the game).
*   This will trigger a download of a `player_data.json` file.
*   Replace the existing `player_data.json` in the project's root directory with this newly downloaded file (or save it directly with that name into the project folder).

### 2. Retrain the Model
*   **Stop the AI server** if it's currently running (usually Ctrl+C in the terminal).
*   Open a terminal or command prompt in the project's root directory.
*   Run the training script:
    ```bash
    python ai_model.py --mode train
    ```
*   The script will:
    *   Load data from `player_data.json` (or create a sample if it's missing).
    *   Preprocess the data into sequences.
    *   Split the data into training and testing sets.
    *   Train a new Gradient Boosting model.
    *   Save the newly trained model as `gbm_player_model.joblib` (overwriting the old one).
    *   Print evaluation metrics (Mean Squared Error) for the new model on the test set.

### 3. Restart Server with New Model
*   After the training script finishes, you **must restart the AI server** for it to load and use the newly trained model:
    ```bash
    python ai_model.py --mode server
    ```

## Troubleshooting

*   **Server Connection Issues (Game shows "Error" or "Not Connected")**:
    *   Ensure the Python AI server (`ai_model.py --mode server`) is running in a terminal.
    *   Check the AI server's terminal output for any error messages (e.g., model not found, port conflicts).
    *   Open the browser's developer console (usually F12) while `index.html` is open. Look for JavaScript errors, especially related to network requests to `http://localhost:5000/predict`.
    *   Verify that no firewall is blocking local network communication to port 5000.
    *   Ensure you are using `http://localhost:5000` and not `https://`.

*   **Model Training Issues (`--mode train`)**:
    *   Ensure `player_data.json` is present in the root directory and contains valid JSON data from the game. The training script will generate a small sample file if `player_data.json` is missing, but this sample is not sufficient for effective training.
    *   Check for Python errors in the terminal output if the training script fails.

*   **"Model not loaded on server" error from `/predict`**:
    *   This means the `gbm_player_model.joblib` file was not found or could not be loaded when the server started.
    *   Run the training mode (`python ai_model.py --mode train`) to generate the model file, then restart the server.

## Future Enhancements (Optional)
*   Implement real-time model updates on the server without needing a manual restart (e.g., using a file watcher or an admin endpoint).
*   Have game enemies or other game elements actively use the AI's predictions for more dynamic and challenging behavior.
*   Expand feature engineering for the AI model (e.g., include enemy positions, bullet information, player's current weapon/buffs) for potentially more accurate predictions.
*   Add more robust error handling and user feedback in both the game and the server.
*   Package Python dependencies into a `requirements.txt` file.
```
