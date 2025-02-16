import os
import time
import random
from typing import Dict, Any, Optional

from openai import OpenAI


# from openpyxl import load_workbook

# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# import undetected_chromedriver as uc

import bs4
from dotenv import load_dotenv
import json
import concurrent.futures


# VARIABLES
######################################################################################################################

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import random
# import undetected_chromedriver as uc
import re
import requests


from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key="fc-28cce56afd4c4218852a6a700a2099d4")

load_dotenv('secret.env')  # Load variables from .env
load_dotenv('secret.env')  # Load variables from .env

# ---------------------------------------------------------
# 3. OSINT Agent (Stub)
# ---------------------------------------------------------
class OSINTAgent:
    """
    Agent responsible for querying external tools (e.g., freepeoplesearch, ...)
    and consolidating the results.
    """
    def __init__(self):
        self.key_name = os.getenv('ENDATO_KEY_NAME')
        self.key_pass = os.getenv('ENDATO_KEY_PASS')
        self.previous_fastpeople_queries = []

    def run_fastpeople(self, args: Dict[str, Any]) -> str:
        # Convert lowercase keys to uppercase for the API
        payload = {
            "FirstName": args.get("firstName", args.get("FirstName", "")),
            "LastName": args.get("lastName", args.get("LastName", "")),
            "Addresses": [
                {
                    "AddressLine2": args.get("address", ""),
                }
            ],
        }

        # Append only the relevant payload without FilterOptions
        self.previous_fastpeople_queries.append({
            "FirstName": payload["FirstName"],
            "LastName": payload["LastName"],
            "Addresses": payload["Addresses"]
        })

        payload['FilterOptions'] = [
            "IncludeEmptyFirstNameResults",
            "IncludeSevenDigitPhoneNumbers",
            "IncludeLowQualityAddresses"
        ]

        url = "https://devapi.endato.com/PersonSearch"

        headers = {
            "accept": "application/json",
            "galaxy-ap-name": self.key_name,
            "galaxy-ap-password": self.key_pass,
            "galaxy-search-type": "Person",
            "content-type": "application/json"
        }
        
        response = requests.post(url, headers=headers, json=payload)
        return response.text

    def run_sonar_query(self, query: str) -> Dict[str, Any]:
        """
        Queries the Sonar API with the provided query string.

        Args:
            query (str): The query string to send to the Sonar API.

        Returns:
            Dict[str, Any]: The response from the Sonar API.
        """
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {os.getenv('SONAR_API_KEY')}",  # Ensure you have the API key in your .env
            "content-type": "application/json"
        }
        payload = {
            "model": "sonar",
            "messages": [
                {"role": "system", "content": "Be precise and concise."},
                {"role": "user", "content": query}
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            # Print response details for debugging
            print(f"Response status code: {response.status_code}")
            print(f"Response text: {response.text}")
            
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {str(e)}")
            return {"error": str(e)}
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {str(e)}")
            print(f"Raw response: {response.text}")
            return {"error": "Invalid JSON response"}
    
    def choose_best_function(self, query: str, attempted_tools: Optional[list] = None) -> str:
        """
        Decides which OSINT tool to use based on the query and which tools have already been attempted.
        Returns a JSON string that includes the tool used and its result.
        """
        if attempted_tools is None:
            attempted_tools = []

        # Include the history in your OpenAI prompt so it can choose a tool not already attempted.
        prompt = f'''
        You are an assistant tasked with selecting the most appropriate OSINT API function based on the user's query.
        Available functions:
        1. Person Search ("person") - good for queries with specific names and addresses.
        2. Sonar Query ("sonar") - good for general or vague queries.
        
        Tools already attempted: {attempted_tools}.
        
        Return your decision as a JSON object, for example:
        {{"function": "person", "parameters": {{"firstName": "John", "lastName": "Doe", "address": "123 Elm Street"}}}}
        or
        {{"function": "sonar", "parameters": {{"query": "Who is John Doe?"}}}}
        
        The input query is: "{query}"
        Output only valid JSON.
        '''
        
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="gpt-4o",
        )
        
        response_content = chat_completion.choices[0].message.content
        try:
            groq_response = json.loads(response_content)
        except json.JSONDecodeError:
            # Fallback: if JSON parsing fails, default to sonar if person was attempted.
            if "person" in attempted_tools:
                groq_response = {"function": "sonar", "parameters": {"query": query}}
            else:
                groq_response = {"function": "person", "parameters": {"firstName": query.split()[0], "lastName": query.split()[-1]}}
        
        function_name = groq_response.get("function", "sonar")
        parameters = groq_response.get("parameters", {})
        
        # Run the selected function
        if function_name == "person":
            result_raw = self.run_fastpeople(parameters)
            try:
                result_dict = json.loads(result_raw)
            except json.JSONDecodeError:
                result_dict = {"error": "Failed to parse FastPeople response", "rawResponse": result_raw}
        else:
            result_dict = self.run_sonar_query(parameters.get("query", query))
        
        final_result = {
            "functionCalled": function_name,
            "useful": isinstance(result_dict, dict) and not result_dict.get("error"),
            "error": result_dict.get("error", "") if isinstance(result_dict, dict) else "",
            "data": result_dict
        }
        
        # Return result along with the tool name, so the orchestrator can record it.
        result_with_tool = {"tool": function_name, "result": final_result}
        return json.dumps(result_with_tool)
    
    # Not Used
    def run_osint_checks(
        self, 
        face_image: bytes, 
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Uses the extracted user data (name, DOB, etc.) and the face image to run OSINT checks.

        Args:
            face_image (bytes): Binary content of the user's face image or ID face image.
            user_data (Dict[str, Any]): Parsed fields from ID (name, address, DOB, etc.)

        Returns:
            Dict[str, Any]: A structured summary of OSINT findings:
                {
                    "pimeyesMatches": [...],
                    "peopleSearchResults": {...},
                    "consolidatedConfidence": 0.88,
                    "notes": "All data lines up."
                }
        """
        # --- MOCK IMPLEMENTATION ---
        # Replace with real API calls:
        #   - Pimeyes / Firecrawl for face matching
        #   - freepeoplesearch or other person-data APIs
        return {
            "pimeyesMatches": [
                {
                    "url": "https://some-site.com",
                    "nameMentioned": user_data.get("name", ""),
                    "addressMentioned": user_data.get("address", ""),
                    "confidenceScore": 0.95
                }
            ],
            "peopleSearchResults": {
                "name": user_data.get("name", ""),
                "age": 33,  # For example
                "addressHistory": [user_data.get("address", "")],
                "relatives": ["Jane Doe"]
            },
            "consolidatedConfidence": 0.88,
            "notes": "OSINT checks found consistent data with no obvious contradictions."
        }

# Test Code
if __name__ == "__main__":
    try:
        agent = OSINTAgent()
    #     test_args = {
    #         "firstName": "Nandan",
    #         "lastName": "Srikrishna",
    #     }
    #     response = agent.run_fastpeople(test_args)
    #     print("Response from run_fastpeople:", response)

        # response = agent.run_sonar_query("Who is Nandan Srikrishna?")
        # print("Response from run_sonar_query:", response)

        result = agent.choose_best_function("Who is Nandan Srikrishna?")
        print("Result from choose_best_function:", result)

        result = agent.choose_best_function("Who is Nandan Srikrishna?")
        print("Result2 from choose_best_function:", result)
    except Exception as e:
        print(f"Error occurred: {str(e)}")
