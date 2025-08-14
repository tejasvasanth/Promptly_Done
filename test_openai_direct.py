#!/usr/bin/env python3

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

async def test_openai_api():
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Get the API key (stored as CLAUDE_API_KEY but might be OpenAI)
        api_key = os.getenv('CLAUDE_API_KEY')
        print(f"Testing API key as OpenAI: {api_key[:20]}...{api_key[-10:]}")
        
        # Initialize OpenAI chat
        openai_chat = LlmChat(
            api_key=api_key,
            session_id="test-session",
            system_message="You are a helpful assistant. Respond with a simple JSON object containing a greeting."
        ).with_model("openai", "gpt-4o")
        
        # Test message
        user_message = UserMessage(text="Say hello in JSON format")
        
        print("Sending test message to OpenAI API...")
        response = await openai_chat.send_message(user_message)
        
        print("✅ OpenAI API Response:")
        print(response[:200] + "..." if len(response) > 200 else response)
        print("\n🎉 This is a working OpenAI API key!")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API Error: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_openai_api())
    sys.exit(0 if result else 1)