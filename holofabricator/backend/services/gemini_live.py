"""
Gemini Live API Service
Real-time voice conversations with WebSocket streaming
Uses gemini-live-2.5-flash-preview for audio I/O
"""

import asyncio
import json
import base64
from typing import Optional, Callable
import websockets
import logging

logger = logging.getLogger("holofabricator.gemini_live")

class GeminiLiveClient:
    """
    WebSocket client for Gemini Live API
    Enables real-time voice conversations with native audio
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.ws = None
        self.model = "gemini-live-2.5-flash-preview"
        self.base_url = "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent"

    async def connect(self, system_instruction: Optional[str] = None):
        """Establish WebSocket connection to Gemini Live API"""
        url = f"{self.base_url}?key={self.api_key}"

        try:
            self.ws = await websockets.connect(url)
            logger.info("[LIVE] Connected to Gemini Live API")

            # Send initial configuration
            config = {
                "setup": {
                    "model": f"models/{self.model}",
                    "generation_config": {
                        "response_modalities": ["AUDIO"],  # Get audio responses
                        "speech_config": {
                            "voice_config": {
                                "prebuilt_voice_config": {
                                    "voice_name": "Aoede"  # Natural voice
                                }
                            }
                        }
                    }
                }
            }

            if system_instruction:
                config["setup"]["system_instruction"] = {
                    "parts": [{"text": system_instruction}]
                }

            await self.ws.send(json.dumps(config))
            logger.info("[LIVE] Sent configuration")

            return True

        except Exception as e:
            logger.error(f"[LIVE] Connection failed: {e}")
            return False

    async def send_audio(self, audio_data: bytes):
        """
        Send audio to Gemini
        Audio must be: 16-bit PCM, 16kHz, mono
        """
        if not self.ws:
            raise RuntimeError("Not connected to Live API")

        # Encode audio as base64
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')

        message = {
            "realtime_input": {
                "media_chunks": [
                    {
                        "mime_type": "audio/pcm",
                        "data": audio_b64
                    }
                ]
            }
        }

        await self.ws.send(json.dumps(message))
        logger.debug("[LIVE] Sent audio chunk")

    async def send_text(self, text: str):
        """Send text message to Gemini"""
        if not self.ws:
            raise RuntimeError("Not connected to Live API")

        message = {
            "client_content": {
                "turns": [
                    {
                        "role": "user",
                        "parts": [{"text": text}]
                    }
                ],
                "turn_complete": True
            }
        }

        await self.ws.send(json.dumps(message))
        logger.info(f"[LIVE] Sent text: {text}")

    async def receive_stream(self,
                           on_audio: Optional[Callable[[bytes], None]] = None,
                           on_text: Optional[Callable[[str], None]] = None):
        """
        Receive streaming responses from Gemini
        Callbacks for audio and text chunks
        """
        if not self.ws:
            raise RuntimeError("Not connected to Live API")

        try:
            async for message in self.ws:
                data = json.loads(message)

                # Handle server content (responses)
                if "serverContent" in data:
                    content = data["serverContent"]

                    # Check for audio in response
                    if "modelTurn" in content:
                        for part in content["modelTurn"].get("parts", []):
                            # Audio response
                            if "inlineData" in part and part["inlineData"].get("mimeType") == "audio/pcm":
                                audio_b64 = part["inlineData"]["data"]
                                audio_bytes = base64.b64decode(audio_b64)

                                if on_audio:
                                    on_audio(audio_bytes)

                                logger.debug(f"[LIVE] Received audio chunk: {len(audio_bytes)} bytes")

                            # Text response
                            if "text" in part:
                                text = part["text"]

                                if on_text:
                                    on_text(text)

                                logger.info(f"[LIVE] Received text: {text}")

                # Handle tool calls (for search grounding)
                if "toolCall" in data:
                    logger.info(f"[LIVE] Tool call: {data['toolCall']}")

                # Handle setup complete
                if "setupComplete" in data:
                    logger.info("[LIVE] Setup complete, ready for conversation")

        except websockets.exceptions.ConnectionClosed:
            logger.info("[LIVE] Connection closed")
        except Exception as e:
            logger.error(f"[LIVE] Receive error: {e}")

    async def close(self):
        """Close WebSocket connection"""
        if self.ws:
            await self.ws.close()
            logger.info("[LIVE] Connection closed")


class GeminiWebClient:
    """
    Gemini 2.5 Pro with web scraping + image analysis
    Fetches any URL, extracts text and images, analyzes with Gemini multimodal
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-pro"):
        import google.generativeai as genai

        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name=model_name)

        logger.info(f"[WEB] Initialized {model_name} with web fetching + image analysis")

    def fetch_and_analyze(self, url: str, question: str, context: Optional[str] = None) -> dict:
        """
        Fetch web page (text + images) and analyze with Gemini 2.5 Pro
        Returns answer based on scraped content
        """
        import requests
        from bs4 import BeautifulSoup
        from PIL import Image
        from io import BytesIO
        import google.generativeai as genai

        try:
            # Fetch web page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract text content
            for script in soup(["script", "style", "nav", "footer", "aside"]):
                script.decompose()
            text_content = soup.get_text(separator='\n', strip=True)
            text_content = '\n'.join([line.strip() for line in text_content.split('\n') if line.strip()])
            text_content = text_content[:15000]  # Limit to 15k chars

            # Extract images
            images = []
            img_tags = soup.find_all('img', src=True)[:5]  # Max 5 images

            for img_tag in img_tags:
                img_url = img_tag['src']
                if not img_url.startswith('http'):
                    from urllib.parse import urljoin
                    img_url = urljoin(url, img_url)

                try:
                    img_response = requests.get(img_url, headers=headers, timeout=5)
                    img = Image.open(BytesIO(img_response.content))

                    # Convert to RGB if needed
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                        img = background

                    images.append(img)
                    logger.info(f"[WEB] Fetched image: {img_url[:80]}")
                except Exception as e:
                    logger.warning(f"[WEB] Failed to fetch image: {e}")
                    continue

            # Build multimodal prompt
            prompt_parts = []

            if context:
                prompt_parts.append(f"Context: {context}\n\n")

            prompt_parts.append(f"Website URL: {url}\n\n")
            prompt_parts.append(f"Website Content:\n{text_content}\n\n")

            # Add images to prompt
            for idx, img in enumerate(images):
                prompt_parts.append(img)
                prompt_parts.append(f"[Image {idx+1} from website]\n\n")

            prompt_parts.append(f"Question: {question}\n\nAnalyze the website content and images above. Provide a detailed technical answer with specific details, part numbers, specifications, or instructions found on the page.")

            # Query Gemini 2.5 Pro with multimodal input
            response = self.model.generate_content(
                prompt_parts,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                )
            )

            result = {
                "answer": response.text,
                "url": url,
                "images_analyzed": len(images),
                "text_length": len(text_content),
                "model": "gemini-2.5-pro"
            }

            logger.info(f"[WEB] Analyzed {url} - {len(images)} images, {len(text_content)} chars")
            return result

        except Exception as e:
            logger.error(f"[WEB] Error fetching {url}: {e}")
            return {
                "answer": f"Failed to fetch website: {str(e)}",
                "url": url,
                "images_analyzed": 0,
                "text_length": 0,
                "model": "gemini-2.5-pro"
            }

    def search_and_answer(self, query: str, context: Optional[str] = None) -> dict:
        """
        Answer question using Gemini 2.5 Pro knowledge base (no web fetch)
        """
        import google.generativeai as genai

        prompt = query
        if context:
            prompt = f"Context: {context}\n\nQuestion: {query}\n\nProvide a detailed technical answer with specifications, part numbers, and troubleshooting steps."
        else:
            prompt = f"{query}\n\nProvide a detailed technical answer with specifications, part numbers, and troubleshooting steps."

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                )
            )

            return {
                "answer": response.text,
                "model": "gemini-2.5-pro"
            }

        except Exception as e:
            logger.error(f"[WEB] Error: {e}")
            return {
                "answer": f"Query failed: {str(e)}",
                "model": "gemini-2.5-pro"
            }


# Helper function for audio format conversion
def convert_audio_to_pcm_16khz_mono(audio_data: bytes, input_format: str = "wav") -> bytes:
    """
    Convert audio to required format: 16-bit PCM, 16kHz, mono
    Uses pydub for conversion
    """
    try:
        from pydub import AudioSegment
        import io

        # Load audio
        audio = AudioSegment.from_file(io.BytesIO(audio_data), format=input_format)

        # Convert to mono
        audio = audio.set_channels(1)

        # Resample to 16kHz
        audio = audio.set_frame_rate(16000)

        # Convert to 16-bit
        audio = audio.set_sample_width(2)  # 2 bytes = 16-bit

        # Export as raw PCM
        return audio.raw_data

    except ImportError:
        logger.warning("[AUDIO] pydub not installed, returning raw audio")
        return audio_data
    except Exception as e:
        logger.error(f"[AUDIO] Conversion error: {e}")
        return audio_data
