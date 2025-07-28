import cv2
import numpy as np
import os
from flask import Flask, request, jsonify # Import jsonify
from werkzeug.utils import secure_filename
import base64 # For handling image data as base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/' # Temporary storage for processing
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def is_blurry(image_path, threshold=1000.0):
    if not os.path.exists(image_path):
        return None, None, "File not found."

    image = cv2.imread(image_path)

    if image is None:
        return None, None, "Could not read image. Invalid format or corrupt file."

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = laplacian.var()
    blurry = variance < threshold

    return blurry, variance, None # Return None for error message if successful

# API Endpoint to receive image and return blurriness
@app.route('/api/analyze_image', methods=['POST'])
def analyze_image_api():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        blurry, variance, error_msg = is_blurry(filepath)

        # Clean up the uploaded file after processing
        os.remove(filepath)

        if error_msg:
            return jsonify({"error": error_msg}), 400
        else:
            result_string = 'blurry' if blurry else 'clear'
            return jsonify({
                "status": "success",
                "is_blurry": blurry,
                "blurriness_score": round(variance, 2),
                "message": f"Image is {result_string}."
            }), 200
    else:
        return jsonify({"error": "Allowed file types are png, jpg, jpeg, gif"}), 400

if __name__ == '__main__':
    # For development, you can run it on 0.0.0.0 to be accessible from other devices
    # but for production, use a WSGI server like Gunicorn/uWSGI + Nginx/Apache
    app.run(host='0.0.0.0', port=5000, debug=True)