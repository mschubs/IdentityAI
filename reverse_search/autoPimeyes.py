import os
import time
import random

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


from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key="fc-28cce56afd4c4218852a6a700a2099d4")

load_dotenv()  # Load variables from .env

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

with open('reverse_search/cookies.json', 'r') as f:
    cookies = json.load(f)

pimeyes_url = "https://pimeyes.com/en"

CURR_SCRIPT_PATH = os.path.realpath(os.path.dirname(__file__))
profile_path = os.path.join(CURR_SCRIPT_PATH, "profile")

def open_chrome_with_profile():
    # Create a new Chrome session with the Chrome profile
    # options = Options()
    options = uc.ChromeOptions()
    # Use forward slashes for the profile path
    options.add_argument(f"--user-data-dir={profile_path}")
    # Create a new instance of the Chrome driver with the specified options
    # driver = webdriver.Chrome(executable_path=chromedriver_path, chrome_options=options)
    driver = uc.Chrome(options=options)
    return driver

def upload(path, driver):    
    try:
        # Wait for upload button
        upload_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="hero-section"]/div/div[1]/div/div/div[1]/button[2]'))
        )
        upload_button.click()
        
        # Wait for file input and send file
        file_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type=file]'))
        )
        
        time.sleep(random.uniform(1, 3))
        file_input.send_keys(path)
        time.sleep(random.uniform(4, 5))

        # Wait for file to be processed - look for loading step to disappear
        WebDriverWait(driver, 20).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, '.step.image-processing'))
        )
        print("uploaded file")

        # # Wait for checkboxes to be present and clickable
        # checkboxes = WebDriverWait(driver, 15).until(
        #     EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.permissions input[type=checkbox]'))
        # )

        # for checkbox in checkboxes:
        #     WebDriverWait(driver, 15).until(EC.element_to_be_clickable(checkbox))
        #     checkbox.click()
        #     # Wait for checkbox state to change
        #     WebDriverWait(driver, 5).until(
        #         lambda driver: checkbox.is_selected()
        #     )
        #     print("Clicked checkbox")

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
        # time.sleep(random.uniform(1, 2))
        driver.execute_script("arguments[0].click();", submit_button)
        print("clicked submit button")
        time.sleep(random.uniform(2, 2.5))
        # Wait for URL to change
        WebDriverWait(driver, 20).until(
            lambda driver: driver.current_url != pimeyes_url
        )
        return driver.current_url

    except Exception as e:
        print(f"An exception occurred: {e}")

def get_results(url, driver):
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

    # Now find all 'row-*' containers that have 'results-row' in their class
    rows = container.find_elements(By.CSS_SELECTOR, "div[class^='row-'][class*='results-row']")
    
    # We will collect all the img elements of interest in this list
    images = []
    
    # Traverse each row
    for row in rows:
        # Find each "results-n" block in this row
        results_divs = row.find_elements(By.CSS_SELECTOR, "div[class^='results-']")
        
        for rdiv in results_divs:
            # Extract the 'n' from "results-n"
            class_name = rdiv.get_attribute("class")
            match = re.search(r"results-(\d+)", class_name)
            if match:
                n = int(match.group(1))
            else:
                n = 1  # Default if for some reason not matched, treat as 1

            # Within the current "results-n" block, we look for child results
            # Usually something like <div data-v-d11d31e3 ... class="result visible">...
            child_divs = rdiv.find_elements(By.CSS_SELECTOR, "div[data-v-d11d31e3].result.visible")
            
            if not child_divs:
                continue
            
            # If n != 1, we only want the *first* child because duplicates are inside
            if n != 1:
                child_divs = [child_divs[0]]
            
            # Gather the img[data-v-d11d31e3] from each child
            for child in child_divs:
                try:
                    img = child.find_element(By.CSS_SELECTOR, "img[data-v-d11d31e3]")
                    images.append(img)
                except:
                    # If there's any child that doesn't have the expected <img>, skip it
                    pass

    print(f"Total extracted images (unique DOM elements): {len(images)}")
    
    results = []
    
    # Proceed with your original routine (scroll, click image, open website, etc.)
    for i, image in enumerate(images, 1):
        print(f"\nProcessing image {i}/{len(images)}")
        
        # Wait for any loading indicators to disappear
        print("Waiting for loading indicators to disappear...")
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "p[data-v-1825a511]"))
        )
        
        # Scroll and wait for the image to be in viewport
        print("Scrolling image into view...")
        driver.execute_script("arguments[0].scrollIntoView(true);", image)
        
        # Wait for image to be visible and clickable
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(image)
        )
        time.sleep(random.uniform(0.2, 0.3))  # Small delay to ensure image is fully loaded

        print("Clicking on image...")
        driver.execute_script("arguments[0].click();", image)
        time.sleep(random.uniform(0.1, 0.2))

        # Check if subgrid exists
        subgrid_images = driver.find_elements(By.CSS_SELECTOR, "div.sub-grid div.result.visible")
        
        subgrid_present = bool(subgrid_images)  # Track if subgrid was found
        print("subgrid_present: ", subgrid_present)
        if subgrid_present:
            # First make sure any existing modal/mask is gone
            try:
                WebDriverWait(driver, 2).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, "div[data-v-5b790c50].mask"))
                )
            except:
                # If timeout occurs, try clicking outside to dismiss any modal
                actions = ActionChains(driver)
                actions.move_to_element(driver.find_element(By.TAG_NAME, "body")).move_by_offset(-300, 0).click().perform()
                time.sleep(random.uniform(0.2, 0.3))

            # Now proceed with subgrid interaction
            print("Sub-grid detected, clicking first sub-grid image...")
            driver.execute_script("arguments[0].scrollIntoView(true);", subgrid_images[0])
            time.sleep(random.uniform(0.1, 0.2))
            
            # Use JavaScript click instead of regular click
            driver.execute_script("arguments[0].click();", subgrid_images[0])

        try:
            # Wait for and click the "Open website" button
            print("Looking for 'Open website' button...")
            # time.sleep(random.uniform(0.2, 0.3))  # Small delay before looking
            
            # First wait for element to be present
            open_website_button = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.action-item:has(svg use[href='#icon-result-actions-open-website'])")
                )
            )
            # Then wait for it to be clickable
            open_website_button = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable(open_website_button)
            )
            time.sleep(random.uniform(0.1, 0.2))  # Small delay before clicking
            
            print("Clicking 'Open website' button...")
            open_website_button.click()
            
            # Get the intercepted URL
            current_url = driver.execute_script("return document.body.getAttribute('data-last-url');")
            print(f"Intercepted URL: {current_url}")
            results.append(current_url)
            
            # Close modal by clicking outside it and wait for it to disappear
            print("Closing modal...")
            actions = ActionChains(driver)
            actions.move_to_element(driver.find_element(By.TAG_NAME, "body")).move_by_offset(-300, 0).click().perform()
            time.sleep(random.uniform(0.1, 0.2))  # Small delay after clicking
            
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "div[data-v-5b790c50].mask"))
            )
            print("Modal closed successfully")
            time.sleep(random.uniform(0.1, 0.2))

            # Only attempt to close subgrid if it was present
            if subgrid_present:
                print("Closing sub-grid after modal is closed...")
                close_btn = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "div.sub-grid div.sub-header button[type='button']")
                    )
                )
                close_btn.click()
                
                # Wait for subgrid to disappear
                WebDriverWait(driver, 5).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.sub-grid"))
                )
                
                driver.execute_script("arguments[0].scrollIntoView(true);", image)
                time.sleep(random.uniform(0.1, 0.2))

        except Exception as e:
            print(f"Error processing website button: {str(e)}")
            # Optionally add more specific error handling
            if "timeout" in str(e).lower():
                print("Timeout occurred while waiting for element")
            continue

    return results

def scrape_urls(urls):
    ret = []
    
    def scrape_single_url(url):
        try:
            print("scraping url: ", url)
            return app.scrape_url(
                url,
                params={'formats': ['markdown']}
            )
        except Exception as e:
            print(f"Error scraping url: {e}", flush=True)
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        ret = list(executor.map(scrape_single_url, urls))
        
    return ret

def main():
    # path = input("Enter path to the image: ")
    path = "/Users/derekmiller/Documents/sideproj/IdentityAI/reverse_search/IMG_9276.jpg"

    # Get the directory of the current script 
    driver = open_chrome_with_profile()
    driver.get(pimeyes_url)
    for cookie in cookies:
        driver.add_cookie({
        'name': cookie['name'],
        'value': cookie['value'],
        'domain': cookie.get('domain', ''),
        'path': cookie.get('path', '/')
    })
        
    driver.refresh()

    # results_url = upload(path, driver)
    results_url = "https://pimeyes.com/en/results/Jaw_25021534265fta2c3yq4y9f0f54a2?query=ffc0803e1f3ee0c000001981fdffe3db"
    urls = get_results(results_url, driver)
    webpage_data = scrape_urls(urls)

    print(webpage_data)

if __name__ == "__main__":
    main()

