import os
import requests
import polyline         # pip install polyline
import urllib.parse
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
from roboflow import Roboflow
from openai import OpenAI  # Using the new client interface
from dotenv import load_dotenv

# ------------------ Load Environment Variables ------------------
load_dotenv()  # loads variables from a .env file in project root

# ------------------ Flask Setup ------------------
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default-secret-key")  # set a secure key in env

UPLOAD_FOLDER = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------ API Keys ------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Validate presence of API keys
for key_name, key_val in [
    ("OPENAI_API_KEY", OPENAI_API_KEY),
    ("ROBOFLOW_API_KEY", ROBOFLOW_API_KEY),
    ("GOOGLE_API_KEY", GOOGLE_API_KEY)
]:
    if not key_val:
        raise RuntimeError(f"Missing required environment variable: {key_name}")

# ------------------ OpenAI Client Setup ------------------
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_chat_response(user_message, system_prompt="You are a helpful assistant specialized in vehicle diagnostics and travel recommendations."):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or "gpt-4"
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7
        )
        answer = response.choices[0].message.content.strip()
        return answer
    except Exception as e:
        print("OpenAI API error:", e)
        return f"I'm sorry, there was an error processing your request: {e}"

# ------------------ Roboflow Setup ------------------
rf = Roboflow(api_key=ROBOFLOW_API_KEY)
project = rf.workspace().project(os.getenv("ROBOFLOW_PROJECT_NAME"))  # project name from env
model = project.version(int(os.getenv("ROBOFLOW_MODEL_VERSION", 1))).model

# ------------------ Warning Definitions ------------------
warning_definitions = {
    "Check Engine": "There is a fault in the engine. Please run a diagnostic test or visit a mechanic.",
    "Oil Pressure": "Low oil pressure detected. Stop driving and check oil levels immediately.",
    "Battery": "Battery issues detected. Ensure your battery and alternator are functioning correctly.",
    "ABS": "Anti-lock Braking System issue detected. Have your braking system inspected promptly.",
    "CheckBrake ": "A problem with the braking system was detected. Check brake pads and fluid levels.",
    "Airbag": "Airbag malfunction detected. For safety, have the system inspected as soon as possible.",
    "Coolant": "High engine temperature. Check coolant levels and radiator performance.",
    "Tire Pressure": "Low tire pressure detected. Inflate your tires to the recommended levels.",
    "Door Open": "A door may not be securely closed. Please check that all doors are properly shut."
}

# ------------------ Trip Planning Helpers ------------------
# ... (rest of helper functions, same as before) ...

def get_itinerary(start, destination):
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    query = f"tourist attractions in {destination}"
    params = {"query": query, "key": GOOGLE_API_KEY}
    response = requests.get(base_url, params=params)
    data = response.json()
    itinerary = []
    for result in data.get("results", [])[:3]:
        item = {
            "place_name": result.get("name"),
            "description": result.get("formatted_address"),
            "visit_time": "To be arranged"
        }
        if "photos" in result and result.get("photos"):
            photo_ref = result["photos"][0]["photo_reference"]
            item["image_url"] = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_ref}&key={GOOGLE_API_KEY}"
        else:
            item["image_url"] = "https://via.placeholder.com/150?text=No+Image"
        itinerary.append(item)
    return itinerary

def get_travel_data(origin, destination):
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {"origins": origin, "destinations": destination, "key": GOOGLE_API_KEY, "mode": "driving"}
    response = requests.get(base_url, params=params)
    try:
        data = response.json()
    except Exception as e:
        print("Error decoding travel data JSON:", e)
        return "N/A", "N/A"
    if not data.get("rows") or not data["rows"][0].get("elements"):
        print("Error: No rows/elements in travel data response", data)
        return "N/A", "N/A"
    element = data["rows"][0]["elements"][0]
    if element.get("status") != "OK":
        print("Error: Element status not OK:", element.get("status"))
        return "N/A", "N/A"
    distance = element.get("distance", {}).get("text", "N/A")
    duration = element.get("duration", {}).get("text", "N/A")
    return distance, duration

def get_directions(origin, destination):
    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {"origin": origin, "destination": destination, "key": GOOGLE_API_KEY, "mode": "driving"}
    response = requests.get(base_url, params=params)
    try:
        data = response.json()
    except Exception as e:
        print("Error decoding directions JSON:", e)
        return []
    if not data.get("routes"):
        print("Error: No routes found in directions response", data)
        return []
    route = data["routes"][0]
    if not route.get("legs"):
        print("Error: No legs found in directions response", route)
        return []
    legs = route["legs"][0]
    steps = legs.get("steps", [])
    directions = [step.get("html_instructions", "") for step in steps]
    return directions

def get_snapped_roads(origin, destination):
    directions_url = "https://maps.googleapis.com/maps/api/directions/json"
    directions_params = {"origin": origin, "destination": destination, "key": GOOGLE_API_KEY, "mode": "driving"}
    directions_response = requests.get(directions_url, params=directions_params)
    try:
        directions_data = directions_response.json()
        overview_polyline = directions_data["routes"][0]["overview_polyline"]["points"]
    except (KeyError, IndexError) as e:
        print("Error: overview_polyline not found in directions response.", e)
        return []
    try:
        path_coords = polyline.decode(overview_polyline)
    except Exception as e:
        print("Error decoding polyline:", e)
        return []
    path_string = "|".join([f"{lat},{lng}" for lat, lng in path_coords])
    roads_url = "https://roads.googleapis.com/v1/snapToRoads"
    roads_params = {"path": path_string, "interpolate": "true", "key": GOOGLE_API_KEY}
    roads_response = requests.get(roads_url, params=roads_params)
    try:
        roads_data = roads_response.json()
    except Exception as e:
        print("Error decoding roads API JSON:", e)
        return []
    snapped_points = roads_data.get("snappedPoints", [])
    snapped_coords = []
    for pt in snapped_points:
        location = pt.get("location")
        if location:
            snapped_coords.append((location.get("latitude"), location.get("longitude")))
    return snapped_coords

def get_map_embed_url(origin, destination):
    encoded_origin = urllib.parse.quote(origin)
    encoded_destination = urllib.parse.quote(destination)
    return f"https://www.google.com/maps/embed/v1/directions?key={GOOGLE_API_KEY}&origin={encoded_origin}&destination={encoded_destination}&mode=driving"

# ------------------ Routes ------------------

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST" and "image" in request.files:
        if "image" not in request.files:
            flash("No image uploaded.")
            return redirect(request.url)
        file = request.files["image"]
        if file.filename == "":
            flash("No file selected.")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            result = model.predict(filepath, confidence=40, overlap=30).json()
            predictions = result.get("predictions", [])
            top_label = predictions[0]["class"] if predictions else "Unknown"
            explanation = warning_definitions.get(top_label, "No explanation available. Please consult your vehicle manual.")
            flash("Inference complete!")
            session["predicted_label"] = top_label
            return render_template("index.html",
                                   filename=filename,
                                   result=result,
                                   label=top_label,
                                   explanation=explanation,
                                   itinerary=None,
                                   travel_info=None,
                                   directions=None,
                                   snapped_roads=None,
                                   map_embed_url=None)
        else:
            flash("Only png, jpg, jpeg, and gif files are allowed.")
            return redirect(request.url)
    return render_template("index.html",
                           filename=None,
                           result=None,
                           itinerary=None,
                           travel_info=None,
                           directions=None,
                           snapped_roads=None,
                           map_embed_url=None)

@app.route("/plan-trip", methods=["POST"])
def plan_trip():
    start = request.form.get("starting-point")
    destination = request.form.get("destination")
    if not start or not destination:
        flash("Please provide both starting and destination points for trip planning.")
        return redirect(url_for("index"))
    itinerary = get_itinerary(start, destination)
    distance, duration = get_travel_data(start, destination)
    travel_info = {"distance": distance, "duration": duration}
    directions = get_directions(start, destination)
    snapped_roads = get_snapped_roads(start, destination)
    map_embed_url = get_map_embed_url(start, destination)
    flash("Trip plan generated successfully!")
    return render_template("trip_plan.html",
                           itinerary=itinerary,
                           travel_info=travel_info,
                           directions=directions,
                           snapped_roads=snapped_roads,
                           map_embed_url=map_embed_url,
                           origin=start,
                           destination=destination)

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form.get("message")
    if not user_message:
        return jsonify({"response": "Please enter a message."})
    predicted_label = session.get("predicted_label", "No diagnosis available")
    system_prompt = (
        f"You are a friendly assistant specialized in vehicle diagnostics and travel recommendations. "
        f"The current vehicle diagnostic result is: {predicted_label}. Respond helpfully to the user's question."
    )
    answer = generate_chat_response(user_message, system_prompt)
    return jsonify({"response": answer})

@app.route("/display/<filename>")
def display_image(filename):
    return redirect(url_for("static", filename="uploads/" + filename), code=301)

if __name__ == '__main__':
    app.run(debug=True)



