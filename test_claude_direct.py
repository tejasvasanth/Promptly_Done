#!/usr/bin/env python3

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

async def test_claude_api():
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Get the Claude API key
        claude_api_key = os.getenv('CLAUDE_API_KEY')
        print(f"Testing Claude API key: {claude_api_key[:20]}...{claude_api_key[-10:]}")
        
        # Initialize Claude chat
        claude_chat = LlmChat(
            api_key=claude_api_key,
            session_id="test-session",
            system_message="You are a helpful assistant. Respond with a simple JSON object containing a greeting."
        ).with_model("anthropic", "claude-3-7-sonnet-20250219")
        
        # Test message
        user_message = UserMessage(text="Say hello in JSON format")
        
        print("Sending test message to Claude API...")
        response = await claude_chat.send_message(user_message)
        
        print("✅ Claude API Response:")
        print(response[:200] + "..." if len(response) > 200 else response)
        print("\n🎉 Claude API is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Claude API Error: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_claude_api())
    sys.exit(0 if result else 1)