#!/usr/bin/env python3
"""
A simple program that uses the Gemini API.
"""

import os
import google.generativeai as genai


def get_gemini_response(model, prompt):
    """
    Connects to the Gemini API and gets a response.
    """
    response = model.generate_content(prompt)
    return response.text


def main():
    """
    Main function.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Please set the GEMINI_API_KEY environment variable.")
        return

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = "Explain how AI works in a few words"
    try:
        response = get_gemini_response(model, prompt)
        print(response)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
