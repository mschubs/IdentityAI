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

from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key="fc-28cce56afd4c4218852a6a700a2099d4")

load_dotenv()  # Load variables from .env

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

with open('cookies.json', 'r') as f:
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
    results = None
    currenturl = None 

    try:

        # upload_button = WebDriverWait(driver, 20).until(
        #     EC.element_to_be_clickable((By.XPATH, '//button[@class="upload" and @aria-label="Upload photo"]'))
        # )

        upload_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="hero-section"]/div/div[1]/div/div/div[1]/button[2]'))
        )

        upload_button.click()

        file_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type=file]'))
        )

        time.sleep(random.uniform(1, 3))

        file_input.send_keys(path)
        time.sleep(random.uniform(5, 7))
        print("uploaded file")

        # Use more resilient selectors that target specific elements rather than full paths
        # Find all checkboxes in the permissions div
        # checkboxes = WebDriverWait(driver, 15).until(
        #     EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.permissions input[type=checkbox]'))
        # )
        # print(checkboxes)

        # # Click each checkbox
        # for checkbox in checkboxes:
        #     WebDriverWait(driver, 15).until(EC.element_to_be_clickable(checkbox)).click()
        #     time.sleep(0.5) # Small delay between clicks
        #     print("Clicked checkbox")

        # Click the submit button
        print("finding submit button")
        submit_buttons = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button[data-v-f20a56d6]"))
        )
        submit_button = submit_buttons[3]  # Use the third button found
        driver.execute_script("arguments[0].click();", submit_button)
        print("clicked submit button")

        time.sleep(5)
        return driver.current_url
        # results_url = "https://pimeyes.com/en/results/Jaw_25021534265fta2c3yq4y9f0f54a2?query=ffc0803e1f3ee0c000001981fdffe3db"
        # driver.get(results_url)

    except Exception as e:
        print(f"An exception occurred: {e}")

def get_results(url, driver):
    driver.get(url)
    time.sleep(2)
    
    # Wait for images to be present
    images = WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img[data-v-d11d31e3]"))
    )
    
    results = []
    # Click each image
    try:
        for image in images:
            # Wait for loading element to disappear
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "p[data-v-1825a511]"))
            )
            
            # Scroll element into view
            driver.execute_script("arguments[0].scrollIntoView(true);", image)
            
            driver.execute_script("arguments[0].click();", image)
            
            # Wait for and click the "Open website" button
            try:
                open_website_button = WebDriverWait(driver, .5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.action-item:has(svg use[href='#icon-result-actions-open-website'])"))
                )
                open_website_button.click()
                driver.switch_to.window(driver.window_handles[-1])
                results.append(driver.current_url)
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                # Find and click the close button
                # Click on the left side of the screen to close the modal
                # driver.find_element(By.CSS_SELECTOR, "div[data-v-5b790c50].mask").click()
                from selenium.webdriver.common.keys import Keys
                ActionChains(driver).move_to_element(driver.find_element("tag name", "body")).move_by_offset(-300, 0).click().perform()
                # ActionChains(driver).send_keys(Keys.ESCAPE).perform()

                print("clicked screen")
                time.sleep(1)

            except:
                pass

    except Exception as e:
        print(f"Error clicking image: {e}", flush=True)

    finally:
        if driver:
            driver.quit()
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
    path = "/Users/alexs/Documents/nandan_id.jpeg"

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

    results_url = upload(path, driver)
    # results_url = "https://pimeyes.com/en/results/Jaw_25021534265fta2c3yq4y9f0f54a2?query=ffc0803e1f3ee0c000001981fdffe3db"
    urls = get_results(results_url, driver)
    webpage_data = scrape_urls(urls)

    print(webpage_data)

if __name__ == "__main__":
    main()

