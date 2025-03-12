from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from flask_cors import CORS
import os
import traceback
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configure Gemini AI with API key
API_KEY = "AIzaSyDqgRQe8nu1lJry7NI0MgF21WSdRSOLEmw"
genai.configure(api_key=API_KEY)
#AIzaSyAnOuinmsV8FH4SpPX1NmPH2p5GiLK_OMU
# Multi-language support dictionary
LANGUAGES = {
    "English": {
        "land_types": ["Clay Soil", "Sandy Soil", "Loamy Soil", "Silt Soil", "Black Soil"],
        "seasons": ["Kharif (Monsoon)", "Rabi (Winter)", "Zaid (Summer)"],
        "crops": ["Rice", "Wheat", "Cotton", "Sugarcane", "Pulses", "Vegetables", "Fruits", "Oil Seeds"]
    },
    "Hindi": {
        "land_types": ["मिट्टी की मिट्टी", "रेतीली मिट्टी", "दोमट मिट्टी", "गाद मिट्टी", "काली मिट्टी"],
        "seasons": ["खरीफ (मानसून)", "रबी (सर्दी)", "जायद (गर्मी)"],
        "crops": ["चावल", "गेहूं", "कपास", "गन्ना", "दालें", "सब्जियां", "फल", "तिलहन"]
    },
    "Telugu": {
        "land_types": ["బంక మట్టి", "ఇసుక నేల", "లోమి నేల", "బురద నేల", "నల్ల నేల"],
        "seasons": ["ఖరీఫ్ (వర్షాకాలం)", "రబీ (శీతాకాలం)", "జైద్ (వేసవి)"],
        "crops": ["వరి", "గోధుమ", "పత్తి", "చెరకు", "పప్పు ధాన్యాలు", "కూరగాయలు", "పండ్లు", "నూనె గింజలు"]
    }
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/get_options/<language>')
def get_options(language):
    if language in LANGUAGES:
        return jsonify(LANGUAGES[language])
    return jsonify({"error": "Language not supported"}), 400

# Function to list available models
@app.route('/api/list_models')
def list_models():
    try:
        models = genai.list_models()
        model_names = [model.name for model in models]
        return jsonify({"models": model_names})
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error listing models: {str(e)}")
        print(error_details)
        return jsonify({"error": str(e), "traceback": error_details}), 500

@app.route('/api/generate_solution', methods=['POST'])
def generate_solution():
    try:
        # Print received data for debugging
        print("Received data:", request.data)
        
        # Check if request has JSON data
        if not request.is_json:
            print("Error: Request does not contain JSON data")
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.json
        print("Parsed JSON data:", data)
        
        # Validate required fields
        required_fields = ['land_type', 'season', 'crop_type', 'acres', 'problem']
        for field in required_fields:
            if field not in data:
                print(f"Error: Missing required field '{field}'")
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        language = data.get('language', 'English')
        
        # Set up model and generate content
        print("Setting up Gemini model")
        
        # Use a specific model instead of auto-selecting the first one
        model_name = 'models/gemini-1.5-pro'
        print(f"Using model: {model_name}")
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        As an agricultural expert, provide a detailed solution in {language} for the following farming situation:
        
        Land Type: {data['land_type']}
        Season: {data['season']}
        Crop Type: {data['crop_type']}
        Land Area: {data['acres']} acres
        Problem Description: {data['problem']}
        
        Please provide:
        1. Problem analysis
        2. Recommended solutions
        3. Preventive measures for the future
        4. Additional tips specific to the land type, crop, and season
        """
        
        print("Sending prompt to Gemini API")
        response = model.generate_content(prompt)
        print("Received response from Gemini API")
        
        # Create solutions directory if it doesn't exist
        os.makedirs('solutions', exist_ok=True)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"solutions/farm_solution_{timestamp}.txt"
        
        print(f"Writing solution to file: {filename}")
        with open(filename, "w", encoding="utf-8") as f:
            f.write("FARM PROBLEM DETAILS\n")
            f.write("-------------------\n\n")
            for key, value in data.items():
                f.write(f"{key.title()}: {value}\n")
            f.write("\nRECOMMENDED SOLUTION\n")
            f.write("-------------------\n\n")
            f.write(response.text)
        
        print("Successfully generated solution")
        return jsonify({
            "solution": response.text,
            "filename": filename
        })
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error in generate_solution: {str(e)}")
        print(error_details)
        return jsonify({"error": str(e), "traceback": error_details}), 500

if __name__ == '__main__':
    app.run(debug=True)
