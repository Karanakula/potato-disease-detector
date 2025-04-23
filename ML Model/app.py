from flask import Flask, request, jsonify
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import os

app = Flask(__name__)

# Load the trained model
model_path = os.path.join("model", "potato_disease_model.h5")  # Update path if necessary
model = tf.keras.models.load_model(model_path)

# Define class labels (Update these to match your dataset)
class_labels = ["Healthy", "Fungi", "Healthy", "Pest", "Pest", "Phytopthora", "Bacteria"]

@app.route("/")
def home():
    return "Flask server is running.ye"

@app.route("/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    img_path = "temp.jpg"
    file.save(img_path)

    try:
        # Preprocess image
        img = image.load_img(img_path, target_size=(224, 224))  # Ensure the correct input shape
        img_array = image.img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        # Make prediction
        prediction = model.predict(img_array)

        # Ensure output matches the number of classes
        if len(prediction[0]) != len(class_labels):
            return jsonify({"error": "Model output mismatch"}), 500

        # Get predicted class
        predicted_index = np.argmax(prediction)
        predicted_class = class_labels[predicted_index]
        confidence = float(np.max(prediction))  # Highest probability score

        return jsonify({"prediction": predicted_class, "confidence": confidence})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
