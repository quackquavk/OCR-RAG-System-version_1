import logging
from typing import List, Any, Optional, AsyncIterator

from huggingface_hub import AsyncInferenceClient

logger = logging.getLogger(__name__)


class LLMResponse:

    def __init__(self, content: Optional[str]):
        self.content = content or ""
    
    def __repr__(self):
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"LLMResponse(content='{preview}')"


class HuggingFaceLLMWrapper:
    def __init__(self, client: AsyncInferenceClient, model_id: str):
        self.client = client
        self.model_id = model_id
        logger.info(f"Initialized HuggingFace LLM wrapper with model: {model_id}")
    
    def _convert_messages_to_hf_format(self, messages: List[Any]) -> List[dict]:

        formatted_messages = []
        
        for msg in messages:
            role = "user"
            
            if hasattr(msg, "type"):
                if msg.type == "system":
                    role = "system"
                elif msg.type == "human":
                    role = "user"
                elif msg.type == "assistant":
                    role = "assistant"
            
            formatted_messages.append({
                "role": role,
                "content": msg.content
            })
        
        return formatted_messages
    
    async def ainvoke(self, messages: List[Any], **kwargs) -> LLMResponse:
        formatted_messages = self._convert_messages_to_hf_format(messages)
        
        logger.debug(f"Invoking HuggingFace model with {len(formatted_messages)} messages")
        
        response = await self.client.chat_completion(
            model=self.model_id,
            messages=formatted_messages,
            max_tokens=None,  # Let model decide based on context
            stream=False      # Non-streaming mode
        )
        
        content = ""
        if response and hasattr(response, "choices") and len(response.choices) > 0:
            content = response.choices[0].message.content or ""
        
        logger.debug(f"Received response with {len(content)} characters")
        
        return LLMResponse(content=content)
    
    async def astream(self, messages: List[Any], **kwargs) -> AsyncIterator[str]:
  
        # Step 1: Convert message format
        formatted_messages = self._convert_messages_to_hf_format(messages)
        
        logger.debug(f"Starting streaming response with {len(formatted_messages)} messages")
        
        # Step 2: Start streaming chat completion
        response_stream = await self.client.chat_completion(
            model=self.model_id,
            messages=formatted_messages,
            max_tokens=None,
            stream=True  # Enable streaming mode
        )
        
        # Step 3: Yield tokens as they arrive
        token_count = 0
        async for chunk in response_stream:
            # Each chunk contains a delta with new content
            if chunk.choices and len(chunk.choices) > 0:
                content = chunk.choices[0].delta.content
                
                if content:
                    token_count += 1
                    yield content
        
        logger.debug(f"Streaming completed with {token_count} tokens")


def create_huggingface_llm(api_token: str, model_id: str) -> HuggingFaceLLMWrapper:

    client = AsyncInferenceClient(token=api_token, timeout=60)  # 60 second timeout
    return HuggingFaceLLMWrapper(client, model_id)
