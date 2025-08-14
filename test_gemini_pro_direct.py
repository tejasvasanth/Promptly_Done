#!/usr/bin/env python3

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

async def test_gemini_pro_api():
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Get the Gemini Pro API key
        gemini_pro_key = os.getenv('GEMINI_PRO_API_KEY')
        print(f"Testing Gemini Pro API key: {gemini_pro_key[:20]}...{gemini_pro_key[-10:]}")
        
        # Initialize Gemini Pro chat
        gemini_pro_chat = LlmChat(
            api_key=gemini_pro_key,
            session_id="test-session",
            system_message="You are a helpful assistant. Respond with a simple JSON object containing a greeting."
        ).with_model("gemini", "gemini-2.0-flash")
        
        # Test message
        user_message = UserMessage(text="Say hello in JSON format")
        
        print("Sending test message to Gemini Pro API...")
        response = await gemini_pro_chat.send_message(user_message)
        
        print("✅ Gemini Pro API Response:")
        print(response[:200] + "..." if len(response) > 200 else response)
        print("\n🎉 Gemini Pro API is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Gemini Pro API Error: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_gemini_pro_api())
    sys.exit(0 if result else 1)