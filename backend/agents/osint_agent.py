import os
import time
import random
from typing import Dict, Any, Optional

from groq import Groq


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
load_dotenv('.env')  # Load variables from .env

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
        # sample_payload = {
        #     "FirstName": "Nandan",
        #     "MiddleName": "M",
        #     "LastName": "Srikrishna",
        # }
        first_name = args.get("FirstName") or args.get("firstName")
        last_name = args.get("LastName") or args.get("lastName")
        
        if not first_name or not last_name:
            raise ValueError("Missing required name fields")

        payload = {
            "FirstName": first_name,
            "LastName": last_name,
            "Addresses": [
                {
                    "AddressLine2": args.get("address2", ""),
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
        data = response.json()

        # Process the returned JSON to only include fullName, fullAddress, and age.
        filtered_persons = []
        for person in data.get("persons", []):
            full_name = person.get("fullName", "")
            age = person.get("age", "")
            
            # Assuming you want the fullAddress from the first address in the list:
            full_address = ""
            addresses = person.get("addresses", [])
            if addresses:
                full_address = addresses[0].get("fullAddress", "")
            
            # Split the full_address by ";" and remove any leading/trailing whitespace
            parts = [part.strip() for part in full_address.split(";")]
            address_line_1 = parts[0] if len(parts) > 0 else ""
            address_line_2 = parts[1] if len(parts) > 1 else ""
            
            filtered_persons.append({
                "name": full_name,
                "age": age,
                "address-line-1": address_line_1,
                "address-line-2": address_line_2
            })

        # Return the filtered data as JSON
        return json.dumps({"persons": filtered_persons})

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

        response = requests.post(url, headers=headers, json=payload)

        return response.json()
    
    def choose_best_function(self, query: str) -> str:
        """
        Chooses the best function to use based on the query by sending a GROQ query.
        It then calls the appropriate function (fast people search or Sonar API) and
        returns the result of that function.
        """
        groq_prompt = '''
        You are an assistant tasked with selecting the most appropriate API function based on the orchestrator's query.
        Your goal is to choose the best function and paramters to that would best help the orchestrator.
        There are two functions available:
        1. **Person Search ("person")**:  
        - Use this function when the query appears to be asking for information about a specific person.  
        - The query may include personal details such as a person's name, and optionally an address.  
        - When using the person search function, extract:
            - `firstName`: The person's first name.
            - `lastName`: The person's last name.
            - Optionally, if an address is mentioned, include `address`.
        
        2. **Sonar Query ("sonar")**:  
        - Use this function for general queries that do not require person-specific parameters or more vague questions of a person.  
        - In this case, choose an appropriate query for the Sonar API.
        - Sonar queries can be used for more complex queries that require a more general search.

        Return your decision as a JSON object in one of the following formats:

        **Example for Person Search (with address):**
        {{
        "function": "person",
        "parameters": {{
            "firstName": "John",
            "lastName": "Doe",
            "address": "123 Elm Street"
        }}
        }}

        **Example for Person Search (without address):**
        {{
        "function": "person",
        "parameters": {{
            "firstName": "John",
            "lastName": "Doe"
        }}
        }}

        **Example for Sonar Query:**
        {{
        "function": "sonar",
        "parameters": {{
            "query": "Who is John Doe?"
        }}
        }}

        Even if the query does not explicitly mention "person search," use the context and details provided (such as names or addresses) to decide if the person search function should be used. If not, default to the sonar function.

        Here are the previous fast people queries (to avoid duplicates):
        {previous_queries}

        Please output only the JSON object without any additional text or formatting.

        The input query is: "{query}"
        '''

        groq_prompt = groq_prompt.format(query=query, previous_queries=json.dumps(self.previous_fastpeople_queries))

        # Instantiate the Groq client using the API key from environment variables.
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        # Send the prompt as a chat message to Groq.
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": groq_prompt}
            ],
            model="llama-3.3-70b-versatile",
        )
        
        # Extract and parse the Groq response.
        response_content = chat_completion.choices[0].message.content
        try:
            groq_response = json.loads(response_content)
        except json.JSONDecodeError:
            # Fallback to simple matching if JSON parsing fails.
            print("JSON parsing failed")
            if "person search" in query.lower():
                groq_response = {
                    "function": "person",
                    "parameters": {
                        "firstName": query.split()[0],
                        "lastName": query.split()[1] if len(query.split()) > 1 else ""
                    }
                }
            else:
                groq_response = {
                    "function": "sonar",
                    "parameters": {"query": query}
                }
    
        print("Groq response:", groq_response)

        # Decide which function to call based on the Groq response.
        if groq_response.get("function") == "person":
            print("Running fast people search")
            params = groq_response.get("parameters", {})
            result = self.run_fastpeople(params)
        else:
            print("Running Sonar API")
            sonar_query = groq_response.get("parameters", {}).get("query", query)
            result = self.run_sonar_query(sonar_query)
        
        return result


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

        # result = agent.choose_best_function("Who is Nandan Srikrishna?")
        # print("Result2 from choose_best_function:", result)
    except Exception as e:
        print(f"Error occurred: {str(e)}")
