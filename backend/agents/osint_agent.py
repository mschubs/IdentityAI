import os
import time
import random
from typing import Dict, Any, Optional

from groq import Groq


from openpyxl import load_workbook

# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc

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
import undetected_chromedriver as uc
import re
import requests


from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key="fc-28cce56afd4c4218852a6a700a2099d4")

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
        pass

    def run_fastpeople(self, args: Dict[str, Any]) -> str:
        # sample_payload = {
        #     "FirstName": "Nandan",
        #     "MiddleName": "M",
        #     "LastName": "Srikrishna",
        # }
        payload = {
            "FirstName": args["firstName"],
            "LastName": args["lastName"],
            "Addresses": [
                {
                    "AddressLine2": args["address2"],
                }
            ],
        }

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
