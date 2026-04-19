"""
Image analyis for RaithaMithra
"""

import os
import base64
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from google import genai
import httpx
from loguru import logger
from prompt.prompts import get_system_prompt
from core.config import get_settings

# Initialize Gemini Client
#llm = genai.Client(api_key="AIzaSyAYoeLGEECXvyvROfeAGtE9EqIFwXHaZL8")

class image_analysis:
    """Analysis image """

    # def __init__(self):
    #     self.settings = get_settings()
    #     self.api_key = self.settings.google_api_key
    #     self.prompt = get_system_prompt()
    #     if not self.api_key:
    #         raise ValueError("GOOGLE_API_KEY not found in environment variables")
    #     self.llm = genai.Client(api_key=self.api_key)
    def __init__(self):
        self.settings = get_settings()

        # Load multiple keys
        raw_keys = self.settings.google_image_keys
        self.api_keys = [key.strip() for key in raw_keys.split(",") if key.strip()]

        if not self.api_keys:
            raise ValueError("No GOOGLE_API_KEYS provided")

        self.current_index = 0
        self.prompt = get_system_prompt()

        # Initialize first key
        self.llm = self._create_client(self.api_keys[self.current_index])
        logger.info(f"Initialized Gemini with key index: {self.current_index}")

    def _create_client(self, api_key: str):
        """Create a Gemini client from a given key"""
        return genai.Client(api_key=api_key)

    def _rotate_key(self):
        """Switch to the next API key (round robin)"""
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        new_key = self.api_keys[self.current_index]
        self.llm = self._create_client(new_key)
        logger.warning(f"Switched Gemini key → index: {self.current_index}")

    async def _safe_api_call(self, func, *args, **kwargs):
        """
        Wrapper that attempts API calls with failover + load-balancing.
        Tries all keys before failing.
        """
        attempts = len(self.api_keys)

        for attempt in range(attempts):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                logger.error(f"API Key index {self.current_index} failed: {e}")
                self._rotate_key()

        raise RuntimeError("All Gemini API keys failed. Check quota or network.")


    async def analyze_image(
        self, 
        image_path: str, 
        prompt: str = "Describe this image in detail",
        model: str = "gemini-2.5-flash",
        language: str = "kn"
    ) -> str:
        """Analyze image using Google vision model"""
         
        try:
            
            # Check if file exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Read and encode image
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Determine MIME type based on file extension
            file_ext = Path(image_path).suffix.lower()
            if file_ext in ['.jpg', '.jpeg']:
                mime_type = "image/jpeg"
            elif file_ext == '.png':
                mime_type = "image/png"
            elif file_ext == '.gif':
                mime_type = "image/gif"
            elif file_ext == '.webp':
                mime_type = "image/webp"
            else:
                mime_type = "image/jpeg"  # Default
            
            # Prepare the prompt based on language
            if language == "kn":
                system_prompt = "ಈ ಚಿತ್ರವನ್ನು ವಿವರವಾಗಿ ವಿವರಿಸಿ. ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸಿ."
            else:
                system_prompt = "Describe this image in detail. Respond in English."
            
            intent = await self.classify_image(mime_type,image_base64,language)

            if "disease" in intent.lower():
                return await self.disease_analysis(mime_type, image_base64,language)
            elif "identification" in intent.lower():
                return await self.identification_image(mime_type, image_base64,language)
            else:
                return await self.describe_image(mime_type, image_base64,language)

        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return f"ಕ್ಷಮಿಸಿ, ಚಿತ್ರ ವಿಶ್ಲೇಷಣೆಯಲ್ಲಿ ದೋಷ ಸಂಭವಿಸಿದೆ." if language == "kn" else "Sorry, an error occurred in image analysis."
        
    async def classify_image(
            self,
            mime_type: str,
            image_base64: str,
            langauge: str
    ) -> str:
        #prompt = self.prompt.classify_prompt()
        prompt = """
                You are an AI expert in agriculture. Classify this input into one of three categories:
            1. disease – plant shows disease symptoms
            2. identification – identify plant species
            3. none – unrelated or unrecognizable(like a person doing some work)
            Just return a single word: disease, identification, or none.
            """
        response = await self._safe_api_call(
            self.llm.models.generate_content,
            model="gemini-2.5-flash",
            contents=[{"inline_data": {"mime_type": mime_type, "data": image_base64}}, prompt]
        )

        return response.text

    async def disease_analysis(
            self,
            mime_type: str,
            image_base64: str,
            langauge: str
    ) -> str:
        #prompt = self.prompt.diesase_prompt()
        prompt = f"""
                You are an expert in crop health. Analyze this plant image and provide:
                1. Detected Disease
                2. Affected Crop
                3. Symptoms Observed
                4. Recommended Treatment Plan
                5. Prevention Tips
                6. Severity Level

                note: 
                the response should be in the {langauge} language.
                If unrecognizable, respond: "Could not recognize the crop or disease."

                the response should be in the {langauge} language.
                with a limit of 300 tokens.
                """
        response = await self._safe_api_call(
            self.llm.models.generate_content,
            model="gemini-2.5-flash",
            contents=[{"inline_data": {"mime_type": mime_type, "data": image_base64}}, prompt]
        )

        return response.text

    async def identification_image(
            self,
            mime_type: str,
            image_base64: str,
            langauge: str
    ) -> str:
        #prompt = self.prompt.identification_prompt()
        prompt = f"""
            You are a botanist and plant taxonomy expert. Analyze this plant image and provide:
            1. Common Name
            2. Scientific Name
            3. Family
            4. Key Identifying Features
            5. Possible Uses
            6. Native Region
            7. Additional Notes

            note: 
            If identification is unclear, respond: "Could not identify the plant species."
            the response should be in the {langauge} language.
            with a limit of 300 tokens.
            """
        response = await self._safe_api_call(
            self.llm.models.generate_content,
            model="gemini-2.5-flash",
            contents=[{"inline_data": {"mime_type": mime_type, "data": image_base64}}, prompt]
        )


        return response.text

    async def describe_image(
            self,
            mime_type: str,
            image_base64: str,
            langauge: str
    ) -> str:
        #prompt = self.prompt.describe_prompt()
        prompt = f"""Describe this image.
        the response should be in the {langauge} language.
        with a limit of 300 tokens.
        """
        # response = self.llm.models.generate_content(
        #         model="gemini-2.5-flash",
        #         contents=[
        #     {"inline_data": {"mime_type": mime_type, "data": image_base64}},
        #     prompt,]
        # )
        response = await self._safe_api_call(
            self.llm.models.generate_content,
            model="gemini-2.5-flash",
            contents=[{"inline_data": {"mime_type": mime_type, "data": image_base64}}, prompt]
        )

        return response.text
        


Image_analysis = image_analysis()

def get_image_analysis() -> image_analysis:
    """Image analysis service"""
    return Image_analysis