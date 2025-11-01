from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import os
import sys

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Model and TensorFlow setup
model = None
class_labels = ["Healthy", "Fungi", "Healthy", "Pest", "Pest", "Phytopthora", "Bacteria"]

def load_model():
    """Load TensorFlow model with error handling"""
    global model
    try:
        import tensorflow as tf
        from tensorflow.keras.preprocessing import image as keras_image
        
        # Suppress TensorFlow warnings
        import logging
        logging.getLogger('tensorflow').setLevel(logging.ERROR)
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
        
        model_path = os.path.join("model", "potato_disease_model.h5")
        
        if not os.path.exists(model_path):
            print(f"❌ Error: Model file not found at {model_path}")
            return False
            
        print(f"📦 Loading model from {model_path}...")
        model = tf.keras.models.load_model(model_path)
        print("✅ Model loaded successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Error: Required libraries not installed")
        print(f"   {str(e)}")
        print("\n💡 Try installing dependencies:")
        print("   pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error loading model: {str(e)}")
        return False

# Load model at startup
print("🚀 Starting Flask API...")
if not load_model():
    print("\n⚠️  WARNING: Model failed to load. Predictions will not work.")
    print("   The server will still start for testing purposes.\n")

@app.route("/")
def home():
    return "Flask server is running.ye"

@app.route("/predict", methods=["POST"])
def predict():
    """Predict potato disease from uploaded image"""
    
    # If model is not loaded, return demo prediction
    if model is None:
        import random
        demo_predictions = [
            {"prediction": "Healthy", "confidence": 0.92},
            {"prediction": "Fungi", "confidence": 0.87},
            {"prediction": "Bacteria", "confidence": 0.85},
            {"prediction": "Pest", "confidence": 0.90},
            {"prediction": "Phytopthora", "confidence": 0.88},
        ]
        result = random.choice(demo_predictions)
        print(f"🎭 DEMO MODE: Returning mock prediction - {result['prediction']}")
        return jsonify(result)
    
    # Check if image is in request
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    
    # Check if file is empty
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
    
    img_path = "temp.jpg"
    
    try:
        # Save uploaded file
        file.save(img_path)
        
        # Import here to avoid issues if TensorFlow isn't loaded
        import tensorflow as tf
        from tensorflow.keras.preprocessing import image as keras_image
        
        # Preprocess image
        img = keras_image.load_img(img_path, target_size=(224, 224))
        img_array = keras_image.img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        # Make prediction
        print("🔮 Making prediction...")
        prediction = model.predict(img_array, verbose=0)

        # Ensure output matches the number of classes
        if len(prediction[0]) != len(class_labels):
            return jsonify({"error": "Model output mismatch"}), 500

        # Get predicted class
        predicted_index = np.argmax(prediction)
        predicted_class = class_labels[predicted_index]
        confidence = float(np.max(prediction))

        print(f"✅ Prediction: {predicted_class} (confidence: {confidence:.2f})")
        
        # Clean up temp file
        if os.path.exists(img_path):
            os.remove(img_path)

        return jsonify({
            "prediction": predicted_class, 
            "confidence": confidence
        })

    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(img_path):
            os.remove(img_path)
            
        print(f"❌ Prediction error: {str(e)}")
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "model_loaded": model is not None,
        "message": "Flask API is healthy" if model is not None else "Model not loaded"
    })

if __name__ == "__main__":
    # Get port from environment variable (Render provides this)
    PORT = int(os.environ.get("PORT", 8000))
    
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🚀 Flask API Server")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"📍 Running on port: {PORT}")
    print(f"📍 Health check: /health")
    
    if model is None:
        print("\n⚠️  DEMO MODE: Model not loaded")
        print("   Predictions will return mock data")
        print("   To fix: Replace model file with actual .h5 file (not Git LFS pointer)")
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    # Use debug=False for production
    app.run(host="0.0.0.0", port=PORT, debug=False)

