import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """You are CropGuard AI Assistant, an expert agricultural advisor for Indian farmers.

Your expertise covers:
- Crop diseases and their treatments
- Fertilizer recommendations and soil health
- Irrigation planning and water management
- Weather impact on farming
- Pest control and prevention
- Crop recommendations based on soil and climate
- Market prices and farming economics
- Government schemes for farmers (PM-KISAN, crop insurance, etc.)
- Organic farming practices
- Seed selection and sowing techniques

Guidelines:
- Always give practical, actionable advice
- Use simple language that farmers can understand
- Reference Indian farming conditions, crops, and seasons (Kharif, Rabi, Zaid)
- Mention specific Indian crops: rice, wheat, sugarcane, cotton, pulses, vegetables
- When discussing diseases, mention both symptoms and treatments
- Always recommend consulting local agricultural officers for serious issues
- Be concise — farmers need quick, clear answers
- If asked in Hindi, respond in Hindi
- If asked in English, respond in English
- Never make up information — if unsure, say so and suggest consulting an expert"""


def chat_with_groq(messages, language='en'):
    """
    Sends conversation history to Groq API and returns the assistant's response.

    Args:
        messages: list of {role, content} dicts (conversation history)
        language: 'en', 'hi', or 'mr'

    Returns:
        dict with success, message, and usage info
    """
    api_key = settings.GROQ_API_KEY
    if not api_key:
        return {
            'success': False,
            'error': 'Groq API key not configured. Please add GROQ_API_KEY to your .env file.',
        }

    # Add language instruction if Hindi or Marathi
    system_prompt = SYSTEM_PROMPT
    if language == 'hi':
        system_prompt += "\n\nIMPORTANT: The user is communicating in Hindi. Always respond in Hindi (Devanagari script)."
    elif language == 'mr':
        system_prompt += "\n\nIMPORTANT: The user is communicating in Marathi. Always respond in Marathi (Devanagari script)."

    try:
        payload = {
            "model": "openai/gpt-oss-20b",
            "messages": [
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            "temperature": 0.7,
            "max_tokens": 1024,
            "stream": False,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            GROQ_API_URL,
            json=payload,
            headers=headers,
            timeout=30,
        )

        if response.status_code == 401:
            return {
                'success': False,
                'error': 'Invalid Groq API key. Please check your GROQ_API_KEY in .env.',
            }

        if response.status_code == 429:
            return {
                'success': False,
                'error': 'Groq API rate limit reached. Please wait a moment and try again.',
            }

        if response.status_code != 200:
            logger.error(f"Groq API error: {response.status_code} — {response.text}")
            return {
                'success': False,
                'error': f'AI service returned an error. Please try again.',
            }

        data = response.json()
        message = data['choices'][0]['message']['content']
        usage = data.get('usage', {})

        return {
            'success': True,
            'message': message,
            'model': data.get('model', 'openai/gpt-oss-20b'),
            'tokens_used': usage.get('total_tokens', 0),
        }

    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'The AI assistant timed out. Please try again.',
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Cannot reach the AI service. Check your internet connection.',
        }
    except Exception as e:
        logger.error(f"Groq chatbot error: {e}")
        return {
            'success': False,
            'error': 'An unexpected error occurred.',
        }


def get_suggested_questions(language='en'):
    """Returns starter questions to show in the chat UI."""
    questions = {
        'en': [
            "My tomato leaves have yellow spots. What disease is this?",
            "Which crop should I grow in black soil during Kharif season?",
            "How much water does rice need per day?",
            "What fertilizer should I use for wheat?",
            "How do I control aphids on my cotton crop?",
            "What are the symptoms of late blight in potato?",
        ],
        'hi': [
            "मेरे टमाटर की पत्तियों पर पीले धब्बे हैं। यह कौन सी बीमारी है?",
            "काली मिट्टी में खरीफ सीजन में कौन सी फसल उगाएं?",
            "चावल को प्रतिदिन कितने पानी की जरूरत है?",
            "गेहूं के लिए कौन सा उर्वरक उपयोग करें?",
            "कपास पर माहू कीट का नियंत्रण कैसे करें?",
        ],
        'mr': [
            "माझ्या टोमॅटोच्या पानांवर पिवळे डाग आहेत. हा कोणता रोग आहे?",
            "काळ्या मातीत खरीप हंगामात कोणते पीक घ्यावे?",
            "भाताला दररोज किती पाणी लागते?",
            "गव्हासाठी कोणते खत वापरावे?",
            "कापसावरील मावा किडीचे नियंत्रण कसे करावे?",
        ],
    }
    return questions.get(language, questions['en'])