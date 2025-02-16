from dotenv import load_dotenv
import os
from groq import Groq

load_dotenv()  # This loads the variables from .env

def run_groq_agent():
    try:
        # Ensure your API key is available
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Please set the GROQ_API_KEY environment variable.")

        # Create a Groq client
        client = Groq(api_key=api_key)

        # Specify your desired model
        model_name = "llama-3.3-70b-versatile"

        # Define a conversation
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": "How do I start using Groq API to build an agent?"}
        ]

        # # Request a completion from the Groq API
        # chat_completion = client.chat.completions.create(
        #     messages=messages,
        #     model=model_name,
        #     temperature=0.7,
        #     max_tokens=1000,
        # )

        # # Print the generated response
        # print(chat_completion.choices[0].message.content)
        
    except ValueError as ve:
        print(f"Configuration error: {ve}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_groq_chat()
