import openai
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Summarizer:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("OPENAI_API_KEY is not set. AI Summaries will be disabled.")

    def summarize_text(self, text: str) -> str:
        if not self.client:
            return "AI Summary Unavailable: API Key missing."

        try:
            # Truncate text to avoid token limits (rough heuristic: 12k chars ~ 3k tokens)
            # GPT-3.5-turbo-16k or GPT-4o supports more, but let's be safe/cheap.
            truncated_text = text[:12000]
            
            prompt = (
                "You are an expert summarizer. Please provide a concise, well-structured summary "
                "of the following text in French. Use bullet points for key concepts. "
                "Keep the tone professional and accessible."
                "\n\nText:\n" + truncated_text
            )

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.5
            )
            
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return f"Error gathering summary: {str(e)}"

_summarizer_instance = None

def get_summarizer():
    global _summarizer_instance
    if _summarizer_instance is None:
        _summarizer_instance = Summarizer()
    return _summarizer_instance
