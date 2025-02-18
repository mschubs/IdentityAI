import os
import time
import random
import json
import re
import concurrent.futures

from anthropic import Anthropic
import undetected_chromedriver as uc
from openpyxl import load_workbook
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

from groq import Groq
from firecrawl import FirecrawlApp

# Load environment variables
load_dotenv('secret.env')

def create_chat_completion(content, model, client):  # New function to create chat completion
    return client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
        model=model,
    )

def extract_json(text):  # Find content between json and markers
    start_marker = "json"
    end_marker = "```"
    
    try:
        # Find the start of JSON content
        start_index = text.find(start_marker) + len(start_marker)
        
        # Find the end of JSON content
        end_index = text.find(end_marker, start_index)
        
        if start_index == -1 or end_index == -1:
            raise ValueError("JSON markers not found in text")
            
        # Extract the JSON string
        json_str = text[start_index:end_index].strip()
        
        # Parse the JSON string
        return json.loads(json_str)
        
    except Exception as e:
        print(f"Error extracting JSON: {e}")
        return None

def run_groq(content, model, client):
    chat_completion = create_chat_completion(content, model, client)
    response_content = chat_completion.choices[0].message.content
    print(response_content)
    json_data = extract_json(response_content)
    return json_data

class ReverseImageAgent:
    def __init__(self):
        """
        Initialize the scraper, load cookies, set up Firecrawl and Groq clients,
        and prepare the paths needed.
        """
        # Firecrawl
        self.app = FirecrawlApp(api_key="fc-28cce56afd4c4218852a6a700a2099d4")
        
        # Groq client
        # self.client = Groq(
        #     api_key=os.environ.get("GROQ_API_KEY"),
        # )
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        # Read cookies from local JSON
        with open('backend/agents/cookies.json', 'r') as f:
            self.cookies = json.load(f)

        # Pimeyes constants
        self.pimeyes_url = "https://pimeyes.com/en"

        # Paths
        self.CURR_SCRIPT_PATH = os.path.realpath(os.path.dirname(__file__))
        self.profile_path = os.path.join(self.CURR_SCRIPT_PATH, "profile")

        # Initialize undetected_chromedriver with profile
        self.driver = self.open_chrome_with_profile()

    def open_chrome_with_profile(self):
        """
        Open a Chrome session using an existing user profile.
        """
        options = uc.ChromeOptions()
        options.add_argument(f"--user-data-dir={self.profile_path}")
        driver = uc.Chrome(options=options)
        return driver

    def upload(self, path):
        """
        Upload an image to Pimeyes and return the results URL.
        """
        driver = self.driver
        try:
            # Convert relative path to absolute path
            absolute_path = os.path.abspath(path)
            
            # Wait for upload button
            time.sleep(1)
            upload_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="hero-section"]/div/div[1]/div/div/div[1]/button[2]'))
            )
            upload_button.click()
            
            # Wait for file input and send file
            file_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type=file]'))
            )
            
            time.sleep(random.uniform(1, 3))
            file_input.send_keys(absolute_path)
            time.sleep(random.uniform(4, 5))

            # Wait for file to be processed - look for loading step to disappear
            WebDriverWait(driver, 20).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, '.step.image-processing'))
            )
            print("uploaded file")

            # Wait for submit button
            print("finding submit button")
            time.sleep(random.uniform(0.2, 1))
            submit_buttons = WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button[data-v-f20a56d6]"))
            )

            submit_button = submit_buttons[3]
            time.sleep(random.uniform(0.2, 1))
            # Wait for button to be clickable
            WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable(submit_button)
            )
            driver.execute_script("arguments[0].click();", submit_button)
            print("clicked submit button")
            time.sleep(random.uniform(2, 2.5))
            
            # Wait for URL to change
            WebDriverWait(driver, 20).until(
                lambda d: d.current_url != self.pimeyes_url
            )
            return driver.current_url

        except Exception as e:
            print(f"An exception occurred during upload: {e}")

    def get_results(self, url):
        """
        From the Pimeyes results page, navigate and extract each 'Open website' link
        by intercepting Pimeyes's window.open calls.
        """
        if not url:
            print("Error: No valid URL provided to get_results")
            return []
        
        driver = self.driver
        print(f"Starting get_results with URL: {url}")
        driver.get(url)
        time.sleep(random.uniform(1, 2))
        
        # Add JavaScript to intercept navigation
        intercept_script = """
        window.open = function(url) {
            document.body.setAttribute('data-last-url', url);
            return { closed: false };  // Mock window object
        };
        """
        driver.execute_script(intercept_script)
        
        # Wait for the main container to appear
        print("Waiting for container to load...")
        container = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.container.banner-content"))
        )

        rows = container.find_elements(By.CSS_SELECTOR, "div[class^='row-'][class*='results-row']")
        images = []

        # Traverse each row
        for row in rows:
            results_divs = row.find_elements(By.CSS_SELECTOR, "div[class^='results-']")
            for rdiv in results_divs:
                class_name = rdiv.get_attribute("class")
                match = re.search(r"results-(\d+)", class_name)
                if match:
                    n = int(match.group(1))
                else:
                    n = 1

                child_divs = rdiv.find_elements(By.CSS_SELECTOR, "div.result.visible")
                if not child_divs:
                    continue

                if n != 1:
                    child_divs = [child_divs[0]]

                for child in child_divs:
                    try:
                        img = child.find_element(By.CSS_SELECTOR, "img[data-v-d11d31e3]")
                        images.append(img)
                    except:
                        pass

        print(f"Total extracted images (unique DOM elements): {len(images)}")
        
        results = []
        
        for i, image in enumerate(images, 1):
            print(f"\nProcessing image {i}/{len(images)}")

            # Wait for any loading indicators to disappear
            print("Waiting for loading indicators to disappear...")
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "p[data-v-1825a511]"))
            )
            
            print("Scrolling image into view...")
            driver.execute_script("arguments[0].scrollIntoView(true);", image)
            
            # Wait for image to be visible/clickable
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(image)
            )
            time.sleep(random.uniform(0.2, 0.3))

            print("Clicking on image...")
            driver.execute_script("arguments[0].click();", image)
            time.sleep(random.uniform(0.1, 0.2))

            # Check for subgrid
            subgrid_images = driver.find_elements(By.CSS_SELECTOR, "div.sub-grid div.result.visible")
            subgrid_present = bool(subgrid_images)
            print("subgrid_present: ", subgrid_present)

            if subgrid_present:
                try:
                    WebDriverWait(driver, 2).until(
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.mask"))
                    )
                except:
                    actions = ActionChains(driver)
                    actions.move_to_element(driver.find_element(By.TAG_NAME, "body"))\
                           .move_by_offset(-300, 0).click().perform()
                    time.sleep(random.uniform(0.2, 0.3))

                print("Sub-grid detected, clicking first sub-grid image...")
                driver.execute_script("arguments[0].scrollIntoView(true);", subgrid_images[0])
                time.sleep(random.uniform(0.1, 0.2))
                driver.execute_script("arguments[0].click();", subgrid_images[0])

            try:
                print("Looking for 'Open website' button...")
                open_website_button = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div.action-item:has(svg use[href='#icon-result-actions-open-website'])")
                    )
                )
                open_website_button = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable(open_website_button)
                )
                time.sleep(random.uniform(0.1, 0.2))

                print("Clicking 'Open website' button...")
                open_website_button.click()

                current_url = driver.execute_script(
                    "return document.body.getAttribute('data-last-url');"
                )
                print(f"Intercepted URL: {current_url}")
                results.append(current_url)

                print("Closing modal...")
                actions = ActionChains(driver)
                actions.move_to_element(driver.find_element(By.TAG_NAME, "body"))\
                       .move_by_offset(-300, 0).click().perform()
                time.sleep(random.uniform(0.1, 0.2))

                WebDriverWait(driver, 5).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.mask"))
                )
                print("Modal closed successfully")
                time.sleep(random.uniform(0.1, 0.2))

                if subgrid_present:
                    print("Closing sub-grid after modal is closed...")
                    close_btn = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "div.sub-grid div.sub-header button[type='button']")
                        )
                    )
                    close_btn.click()
                    WebDriverWait(driver, 5).until(
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.sub-grid"))
                    )
                    
                    driver.execute_script("arguments[0].scrollIntoView(true);", image)
                    time.sleep(random.uniform(0.1, 0.2))

            except Exception as e:
                print(f"Error processing website button: {str(e)}")
                if "timeout" in str(e).lower():
                    print("Timeout occurred while waiting for element")
                continue

        return results
    
    def scrape_urls(self, urls, id_name):
        futures = []
        markdown = []
        time_start = time.time()

        time_start = time.time()
        urls_to_scrape = urls[:5]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.scrape_url, url) for url in urls_to_scrape]
            for future in concurrent.futures.as_completed(futures):
                markdown.append(future.result())
        time_end = time.time()
        print(f"Time to scrape all urls: {time_end - time_start} seconds")

        time_start = time.time()
        # content = """
        #         You will be passed data in the form of a list of webpages in markdown format. If the webpages contain information about Nandan Srikrishna, please return this name and any information abou them on these webpages in a json format. If the websites do not mention Nandan Srikrishna, please return an empty json object. Denote the json object to start with `json` and end with ````"""
        # content += str(markdown)
        # result = run_groq(content, "mixtral-8x7b-32768", self.client)
        chat_completion = self.client.messages.create(
                temperature=0,
                system=f'You will be passed data in the form of a list of webpages in markdown format. If the webpages contain information about {id_name}, please return this name and any information about them on these webpages in a json format. If the websites do not mention{id_name}, please return an empty json object. Format the json so that it has a `name` field and `bio` field. The bio must have a length of two sentences or less.Denote the json object to start with `json` and end with ````',
            messages=[
                {
                    "role": "user",
                    "content": str(markdown)
                }
            ],
            model="claude-3-5-sonnet-20241022",
            max_tokens=500
        )

        result = chat_completion.content[0].text
        print(result)

        time_end = time.time()
        print(f"Time for claude inference: {time_end - time_start} seconds")
        return urls_to_scrape, extract_json(result)


        # with concurrent.futures.ThreadPoolExecutor() as executor:
        #     futures = [executor.submit(self.scrape_url, url) for url in urls]
        # for future in futures:
        #     result = future.result()
            
        # print(f"Time to scrape all urls: {time_end - time_start} seconds")
        # return webpage_data

    
    def scrape_url(self, url):
        try:
            print("scraping url: ", url)
            return self.app.scrape_url(
                url,
                params={'formats': ['markdown']}
            )
        except Exception as e:
            print(f"Error scraping url: {e}", flush=True)
            return None

    def run(self, image_path, id_name):
        """
        Orchestrates the entire flow: 
        1) Load Pimeyes, add cookies, refresh. 
        2) Upload image. 
        3) Gather results. 
        4) Scrape URLs. 
        5) Print or return data.
        """
        self.webpage_data = {}
        self.futures = []

        self.driver.get(self.pimeyes_url)
        print("test")
        # Add cookies
        for cookie in self.cookies:
            self.driver.add_cookie({
                'name': cookie['name'],
                'value': cookie['value'],
                'domain': cookie.get('domain', ''),
                'path': cookie.get('path', '/')
            })

        self.driver.refresh()
        print("test2")
        # Upload
        # results_url = self.upload(image_path)
        results_url = "https://pimeyes.com/en/results/ERx_250216zv8qkaau7b9wss0823835fb?query=fce1e3fef0c08088001078f1fbf4f27a"
        time.sleep(2)
        # Get final URL set
        time_start = time.time()
        urls = self.get_results(results_url)
        time_end = time.time()
        print(f"Time to get pimeyes url results: {time_end - time_start} seconds")
        print("test3")
        urls, result = self.scrape_urls(urls, id_name)

        # Save URLs to JSON file
        with open('urls.json', 'w') as f:
            json.dump(urls, f, indent=4)

        print(result)
        return result, urls
# from my_pimeyes_scraper import PimeyesScraper

def do_reverse_search(image_path, id_name):
    scraper = ReverseImageAgent()
    data = scraper.run(image_path, id_name)
    # do something with 'data'
    return data

if __name__ == "__main__":
    # Example call
    results = do_reverse_search("/Users/alexs/Documents/treehacks2025/backend/agents/nandan_face.jpg")
    print(results)