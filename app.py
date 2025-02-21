from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Dummy CNN function for dashboard interpretation and troubleshooting
def interpret_dashboard(image_path):
    # In a real application, load a pre-trained CNN model to analyze the image.
    # For this demo, return a dummy warning message and troubleshooting tip.
    warning_message = "Check Engine Light - Low Oil Pressure"
    troubleshooting_tip = "Tip: Check your oil level and consult your manual."
    return warning_message, troubleshooting_tip

# Dummy function to generate a travel itinerary along a route
def generate_itinerary(start, end):
    # In a real scenario, integrate with mapping APIs to generate a dynamic itinerary.
    itinerary = {
        "route": [start, "Scenic Stop A", "Cultural Spot B", end],
        "duration": "3 hours 15 minutes"
    }
    return itinerary

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_dashboard():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected."}), 400
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Get warning message and troubleshooting tip
    warning_message, troubleshooting_tip = interpret_dashboard(file_path)
    return jsonify({
        "warning_message": warning_message,
        "troubleshooting_tip": troubleshooting_tip
    })

@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.get_json()
    user_message = data.get('message', '').lower()
    
    # Check if the message is about travel itinerary
    if "itinerary" in user_message:
        start = data.get('start', 'Home')
        end = data.get('end', 'Destination')
        itinerary = generate_itinerary(start, end)
        response = (
            f"Your itinerary: {', '.join(itinerary['route'])} with an estimated duration of "
            f"{itinerary['duration']}."
        )
    # Otherwise, assume troubleshooting request related to dashboard warning lights
    elif "warning" in user_message or "dashboard" in user_message:
        # In a real scenario, you might analyze the message further or refer to the uploaded image interpretation.
        response = "Based on your dashboard warning light, here's a tip: Check your oil level and tire pressure."
    else:
        response = "How can I help? Ask for an itinerary or troubleshooting tip based on your dashboard warning light."
        
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)
