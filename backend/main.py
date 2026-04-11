from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import base64

app = FastAPI(title="Japan Invoice Extraction System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "qwen3.5:35b-a3b-q4_K_M"

@app.post("/api/extract_invoice")
async def extract_invoice(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode('utf-8')

        prompt = """
            You are an emotionless JSON formatting machine. Please extract key information from the following invoice/receipt.

            [Highest Directive: Violating the following rules will be deemed a severe error]
            1. You must ONLY output the specified JSON structure. Adding unrequested fields such as store, subtotal_amount, tax_amount, or price is strictly prohibited!
            2. Each object in the items list must ONLY contain two keys: "value" and "needs_review"!

            [Field Requirements]
            1. date (Date)
            2. items (Specific item names. Since there may be multiple items, it must be output in a list/array format)
            3. total_amount (Total amount, digits only)

            [Core Rules]
            If you believe the extracted content of a specific field is highly likely to be incorrect, you must set the 'needs_review' for that field to True.
            If all 'needs_review' fields are False, 'global_warning' does not need to be set to True.

            [The standard output format must be exactly as follows]
            {
            "invoice_data": 
                {
                "date": {"value": "2026.03.19", "needs_review": false},
                "items": [
                    {"value": "Good A name", "needs_review": false},
                    {"value": "Good B name", "needs_review": true}
                ],
                "total_amount": {"value": "15000", "needs_review": false}
                },
            "global_warning": false
            }
        """

        print(f"Sending to {LLM_MODEL} (Generate MODE) ...")
        
        response = requests.post(OLLAMA_URL, json={
            "model": LLM_MODEL,
            "prompt": prompt,             
            "images": [base64_image],    
            "stream": False,
            "options": {
                "temperature": 0.1 
            }
        })
        
        if response.status_code != 200:
            print(f"\n Ollama Interface Error: HTTP {response.status_code} - {response.text}")
            raise ValueError(f"Ollama Server Connection Error: {response.status_code}")
            
        response_data = response.json()
        if "error" in response_data:
            print(f"\n Ollama Error: {response_data['error']}")
            raise ValueError(f"Ollama Error: {response_data['error']}")
            
        llm_result = response_data.get('response', '').strip()
        
        if not llm_result:
            raise ValueError("Return empty content，Please check LLM status")

        if llm_result.startswith('```json'):
            llm_result = llm_result[7:]
        elif llm_result.startswith('```'):
            llm_result = llm_result[3:]
        if llm_result.endswith('```'):
            llm_result = llm_result[:-3]
        llm_result = llm_result.strip()

        parsed_json = json.loads(llm_result)
        
        if "invoice_data" not in parsed_json:
            raise ValueError("Please check the origin output")
            
        return parsed_json
        
    except json.JSONDecodeError:
        print("\n Error: Not Json")
        raise HTTPException(status_code=500, detail="Not Json")
    except Exception as e:
        print(f"\n Backend Error: {e}")
        raise HTTPException(status_code=500, detail=f"System Error: {str(e)}")