#!/usr/bin/env python3
"""
List all available Gemini models for your API key
"""

import os
import google.generativeai as genai

def list_models():
    """List all available Gemini models"""
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return
    
    print(f"Using API key: {api_key[:10]}...\n")
    
    genai.configure(api_key=api_key)
    
    print("="*60)
    print("Available Gemini Models")
    print("="*60)
    
    try:
        models = genai.list_models()
        
        generation_models = []
        
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                generation_models.append(model)
                print(f"\n✅ {model.name}")
                print(f"   Display name: {model.display_name}")
                print(f"   Description: {model.description}")
                print(f"   Input token limit: {model.input_token_limit:,}")
                print(f"   Output token limit: {model.output_token_limit:,}")
                print(f"   Supported methods: {', '.join(model.supported_generation_methods)}")
        
        print("\n" + "="*60)
        print(f"Total models supporting generateContent: {len(generation_models)}")
        print("="*60)
        
        if generation_models:
            print("\n💡 Recommended for LKML Dashboard:")
            
            # Find Flash model
            flash_models = [m for m in generation_models if 'flash' in m.name.lower()]
            if flash_models:
                print(f"\n   Use this in gemini_client.py:")
                print(f"   'flash': '{flash_models[0].name}'")
            
            # Find Pro model
            pro_models = [m for m in generation_models if 'pro' in m.name.lower()]
            if pro_models:
                print(f"\n   For higher quality:")
                print(f"   'pro': '{pro_models[0].name}'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check your API key is correct")
        print("2. Ensure you have internet connection")
        print("3. Try generating a new API key at:")
        print("   https://makersuite.google.com/app/apikey")

if __name__ == "__main__":
    list_models()
