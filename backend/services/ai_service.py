import os
import httpx
import base64
import json

async def verify_image_with_gemini(image_path: str) -> dict:
    """
    Sends the image to Gemini 2.0 Flash REST API to verify tree presence and health.
    Returns a structured dictionary matching the AIVerification schema.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    
    # If no key is set yet (user said they will paste it later), return a mock response
    if not api_key or api_key == "your_key":
        return {
            "tree_detected": True,
            "health_assessment": "moderate",
            "condition_notes": "Mocked response: API key missing. Assuming tree is healthy.",
            "confidence": 0.85
        }
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    with open(image_path, "rb") as f:
        image_data = f.read()
        
    b64_image = base64.b64encode(image_data).decode('utf-8')
    
    # We want a structured JSON response
    system_instruction = """
    You are an expert botanist and forestry AI. 
    Analyze the image and return a JSON object with these exact keys:
    - "tree_detected" (boolean): True if a sapling/tree is visible, False otherwise.
    - "health_assessment" (string): One of: "poor", "moderate", "good", "excellent".
    - "condition_notes" (string): A short sentence describing the plant's visible condition.
    - "confidence" (float): A number between 0.0 and 1.0 indicating your confidence in this assessment.
    
    Respond ONLY with raw JSON, no markdown blocks.
    """
    
    payload = {
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [
            {
                "parts": [
                    {"text": "Analyze this plantation photo."},
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": b64_image
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            content_text = data["candidates"][0]["content"]["parts"][0]["text"]
            # Clean up potential markdown formatting if Gemini ignored the instruction
            content_text = content_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            result = json.loads(content_text)
            return result
        except (KeyError, IndexError, json.JSONDecodeError, httpx.HTTPError) as e:
            print(f"Gemini API error: {e}")
            return {
                "tree_detected": False,
                "health_assessment": "poor",
                "condition_notes": "Failed to connect to or parse AI response.",
                "confidence": 0.0
            }
