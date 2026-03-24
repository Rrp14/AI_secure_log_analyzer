import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


def clean_ai_response(text: str):
    # 🔥 Remove markdown code blocks like ```json ... ```
    text = re.sub(r"```json|```", "", text).strip()
    return text


def analyze_with_ai(log_text: str, findings: list):
    try:
        prompt = f"""
You are a cybersecurity AI system.

Analyze logs and findings.

Return ONLY valid JSON. No explanation.
DO NOT wrap response in markdown or code blocks.

{{
  "summary": "...",
  "risks": ["..."],
  "root_cause": "...",
  "attack_narrative": "..."
}}

Logs:
{log_text[:3000]}

Findings:
{findings}
"""

        response = model.generate_content(prompt)

        text = response.text.strip()

        # 🔥 Clean markdown
        text = clean_ai_response(text)

        try:
            return json.loads(text)
        except:
            return {
                "summary": text,
                "risks": [],
                "root_cause": "Parsing failed",
                "attack_narrative": "AI returned unstructured output"
            }

    except Exception as e:
        return {
            "summary": "AI analysis failed",
            "risks": [],
            "root_cause": str(e),
            "attack_narrative": ""
        }