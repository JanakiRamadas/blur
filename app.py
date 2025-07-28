import cv2
import numpy as np
import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import logging

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def is_blurry(image_path, threshold=1000.0):
    app.logger.info(f"Checking blurriness for image: {image_path}")
    if not os.path.exists(image_path):
        app.logger.error(f"File not found during blur check: {image_path}")
        return None, None, "File not found."

    try:
        image = cv2.imread(image_path)
    except Exception as e:
        app.logger.error(f"Error reading image with OpenCV: {e}", exc_info=True)
        return None, None, f"Error reading image with OpenCV: {str(e)}"

    if image is None:
        app.logger.error(f"OpenCV returned None for image: {image_path}. Possible corrupt or unsupported format.")
        return None, None, "Could not read image. Invalid format or corrupt file."

    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        blurry = variance < threshold # This is numpy.bool_
        app.logger.info(f"Blur check successful for {image_path}. Variance: {variance:.2f}, Blurry: {blurry}")
        return blurry, variance, None
    except Exception as e:
        app.logger.error(f"Error during Laplacian calculation: {e}", exc_info=True)
        return None, None, f"Error during image processing: {str(e)}"


@app.route('/api/analyze_image', methods=['POST'])
def analyze_image_api():
    app.logger.info("Received request for /api/analyze_image")
    if 'file' not in request.files:
        app.logger.warning("No file part in the request.")
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        app.logger.warning("No selected file name.")
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            file.save(filepath)
            app.logger.info(f"File saved successfully to: {filepath}")
        except Exception as e:
            app.logger.error(f"Error saving file: {e}", exc_info=True)
            return jsonify({"error": f"Failed to save file: {str(e)}"}), 500

        blurry, variance, error_msg = is_blurry(filepath)

        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                app.logger.info(f"Cleaned up file: {filepath}")
        except Exception as e:
            app.logger.warning(f"Failed to remove file {filepath}: {e}")

        if error_msg:
            app.logger.error(f"Image processing error: {error_msg}")
            return jsonify({"error": error_msg}), 400
        else:
            result_string = 'blurry' if blurry else 'clear'
            app.logger.info(f"API success: Image is {result_string}, variance: {variance}")
            return jsonify({
                "status": "success",
                "is_blurry": bool(blurry),  # <--- CONVERT TO NATIVE PYTHON BOOL HERE
                "blurriness_score": round(variance, 2),
                "message": f"Image is {result_string}."
            }), 200
    else:
        app.logger.warning(f"Disallowed file type for filename: {file.filename}")
        return jsonify({"error": "Allowed file types are png, jpg, jpeg, gif"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)