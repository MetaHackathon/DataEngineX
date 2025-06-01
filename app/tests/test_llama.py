#!/usr/bin/env python3
"""
Simple test script for Llama client functionality
"""

import asyncio
import sys
import os

from services.llama_client import LlamaClient

async def test_llama_client():
    """Test the Llama client with a simple prompt"""
    
    print("🧪 Testing Llama Client...")
    print("=" * 50)
    
    # Initialize client
    client = LlamaClient()
    
    # Check if API key is available
    if client.api_key:
        print("✅ LLAMA_API_KEY found in environment")
    else:
        print("⚠️  LLAMA_API_KEY not found - will use mock responses")
    
    print(f"🔗 API URL: {client.api_url}")
    print()
    
    # Test 1: Simple generation
    print("🔍 Test 1: Simple text generation")
    print("-" * 30)
    
    simple_prompt = "What are the key benefits of using transformer architectures in deep learning? Please provide a brief, structured answer."
    
    try:
        response = await client.generate_response(
            prompt=simple_prompt,
            max_tokens=300,
            temperature=0.3
        )
        
        print("✅ Response received:")
        print(response)
        print()
        
    except Exception as e:
        print(f"❌ Error in simple generation: {e}")
        print()
    
    # Test 2: Paper analysis
    print("🔍 Test 2: Paper analysis")
    print("-" * 30)
    
    try:
        analysis = await client.analyze_paper(
            title="Attention Is All You Need",
            abstract="We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
            analysis_type="summary"
        )
        
        print("✅ Paper analysis completed:")
        print(f"Analysis: {analysis['analysis'][:200]}...")
        print(f"Insights count: {len(analysis['insights'])}")
        print(f"Key concepts count: {len(analysis['key_concepts'])}")
        print()
        
    except Exception as e:
        print(f"❌ Error in paper analysis: {e}")
        print()
    
    # Test 3: Chat functionality
    print("🔍 Test 3: Chat with paper")
    print("-" * 30)
    
    try:
        chat_response = await client.chat_with_paper(
            paper_title="Attention Is All You Need",
            paper_abstract="We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
            user_question="What makes the Transformer architecture different from previous approaches?"
        )
        
        print("✅ Chat response:")
        print(chat_response)
        print()
        
    except Exception as e:
        print(f"❌ Error in chat functionality: {e}")
        print()
    
    print("🏁 Llama client test completed!")

if __name__ == "__main__":
    asyncio.run(test_llama_client()) 