import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class EmbeddingClient:
    def __init__(
        self, 
        base_url: str, 
        model: str, 
        api_key: str,
        batch_size: int = 32
    ):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.api_key = api_key
        self.batch_size = batch_size
        self.endpoint = f"{self.base_url}/embeddings"
        
        logger.info(f"Initialized embedding client")
        logger.info(f"  Base URL: {self.base_url}")
        logger.info(f"  Model: {self.model}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def embed_text(self, text: str) -> Optional[list[float]]:
        """Embed a single text using Requesty OpenAI-compatible API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.endpoint,
                json={
                    "model": self.model,
                    "input": text,
                    "encoding_format": "float"
                },
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            if "data" in data and len(data["data"]) > 0:
                return data["data"][0]["embedding"]
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error embedding text: {e}")
            raise
    
    def embed_texts(self, texts: list[str]) -> list[Optional[list[float]]]:
        """Embed multiple texts with batching"""
        embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_embeddings = self._embed_batch(batch)
            embeddings.extend(batch_embeddings)
        return embeddings
    
    def _embed_batch(self, texts: list[str]) -> list[Optional[list[float]]]:
        """Embed a batch of texts using Requesty API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.endpoint,
                json={
                    "model": self.model,
                    "input": texts,
                    "encoding_format": "float"
                },
                headers=headers,
                timeout=120
            )
            response.raise_for_status()
            data = response.json()
            
            embeddings = [None] * len(texts)
            for item in data.get("data", []):
                idx = item.get("index", 0)
                if idx < len(embeddings):
                    embeddings[idx] = item.get("embedding")
            
            return embeddings
        except requests.exceptions.RequestException as e:
            logger.error(f"Error embedding batch: {e}")
            raise
    
    def verify_connection(self) -> bool:
        """Verify that the API is accessible"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.endpoint,
                json={
                    "model": self.model,
                    "input": "test",
                    "encoding_format": "float"
                },
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✓ Successfully connected to Requesty API")
                return True
            elif response.status_code == 401:
                logger.error("✗ Unauthorized - check your API key")
                return False
            else:
                logger.error(f"✗ API error: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"✗ Connection error: {e}")
            return False