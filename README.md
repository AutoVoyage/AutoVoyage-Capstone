**Project Title** 

AutoVoyage - AI-powered Dashboard Warning Light Identification and Personalized Travel Recommendations

**Project Overview**

AutoVoyage is an AI-powered platform designed to help car owners identify dashboard warning lights and receive personalized travel recommendations. The system uses machine learning for image recognition to diagnose warning lights and suggests nearby places to visit while travelling via Google Maps API.

**Features**

**Dashboard Warning Light Identification:** Uses AI to recognize and identify dashboard warning lights from images uploaded by users.

**Personalized Travel Recommendations:** Provides real-time travel assistance using user’s location  integrating Google Maps API for directions.

**Chatbot:** Offers a conversational interface to troubleshoot dashboard issues 

**Technologies Used**

**OpenAI (Natural Language Understanding - NLU):** Processes user queries and handles flexible response generation within the chatbot interface.

**Google Maps API:** Integrated for travel itinerary creation, route planning, and providing directions  based on the user’s location.

**Roboflow:** Used for annotating and augmenting the image dataset for training the machine learning model that recognizes dashboard warning lights.



**How to Run the Project Locally**

**1.Clone the repository**

**Command** 

git clone https://github.com/your-username/autovoyage.git

**2. Navigate to the Project Directory**

After cloning, move into the project directory:

**Command** 

cd autovoyage

**3.Set Up a Virtual Environment**
You can create a virtual environment with:

**Command** 

python3 -m venv venv

**4. Activate the Virtual Environment**

Once the virtual environment is created, activate it on Windows:

**Command** 

.\venv\Scripts\activate

**5. Install Dependencies**

With the virtual environment activated, install the project dependencies listed in requirements.txt:

**Command** 

pip install -r requirements.txt

**6. Set Up Environment Variables**

Some APIs, like Roboflow  ,Google Maps and OpenAI, require API keys. You’ll need to set them as environment variables.

Create a .env file in the root directory of your project.

Add your API keys to the .env file:



ROBOFLOW_API_KEY=api-key

GOOGLE_MAPS_API_KEY=api-key


OPENAI_API_KEY=your-openai-api-key

Replace your-google-maps-api-key and your-openai-api-key with your actual API keys.

7. Run the Application
   
Once everything is set up, you can run the application with:

**Command** 

python app.py

This will start the server.

9. Access the Application
    
Open a web browser and navigate to:

http://localhost:5000

You should see the AutoVoyage app running locally, where you can interact with the chatbot and upload dashboard images for recognition.
