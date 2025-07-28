import requests
import os
import json # Import json for pretty printing in case of non-json errors

# The URL of your deployed Flask API endpoint
API_URL = "https://blur-d6ed.onrender.com/api/analyze_image"

# Path to the image file you want to send
IMAGE_FILE_PATH = "clear1.png" # Make sure this matches your file

def test_upload_image():
    if not os.path.exists(IMAGE_FILE_PATH):
        print(f"Error: Image file not found at {IMAGE_FILE_PATH}")
        return

    try:
        with open(IMAGE_FILE_PATH, 'rb') as f:
            files = {'file': (IMAGE_FILE_PATH, f, 'image/png')} # Adjust mimetype if needed

            print(f"Sending POST request to: {API_URL} with file: {IMAGE_FILE_PATH}")
            response = requests.post(API_URL, files=files)

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            try:
                json_response = response.json()
                print("Response JSON (Success):")
                print(json.dumps(json_response, indent=2)) # Pretty print JSON

                print("\nImage analysis successful!")
                if json_response.get("is_blurry"):
                    print("Result: Image is BLURRY.")
                else:
                    print("Result: Image is CLEAR.")
                print(f"Blurriness Score: {json_response.get('blurriness_score')}")

            except requests.exceptions.JSONDecodeError:
                print("Error: Expected JSON response, but got invalid JSON.")
                print("Full Response Text:")
                print(response.text)
        else:
            # Handle non-200 responses
            print("API call failed.")
            try:
                # Try to parse as JSON if it's an API error message
                json_response = response.json()
                print("Response JSON (Error):")
                print(json.dumps(json_response, indent=2)) # Pretty print JSON
                print(f"Error from API: {json_response.get('error', 'No specific error message.')}")
            except requests.exceptions.JSONDecodeError:
                # If not JSON, print the raw text response (like the 500 HTML page)
                print("Response is not JSON:")
                print(response.text)
            print(f"HTTP Status Code: {response.status_code}")


    except requests.exceptions.RequestException as e:
        print(f"Network or request error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_upload_image()