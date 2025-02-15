from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc 
import random
import time
from pynput import keyboard

def search_person(name, location):
    # Setup undetected Chrome driver with enhanced options
    options = uc.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument(f'--window-size={random.randint(1050, 1920)},{random.randint(800, 1080)}')
    options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 120)}.0.0.0 Safari/537.36')
    
    driver = uc.Chrome(options=options)
    
    try:
        # Randomize window size and position
        driver.set_window_position(random.randint(0, 100), random.randint(0, 100))
        
        # Navigate to the website with more realistic behavior
        driver.get("https://www.fastpeoplesearch.com/")
        time.sleep(random.uniform(3, 5))
        
        # Simulate human-like mouse movements before typing
        name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "search-name-name"))
        )
        
        # Random scrolling behavior
        driver.execute_script(f"window.scrollTo(0, {random.randint(50, 200)})")
        time.sleep(random.uniform(0.5, 1.5))
        
        # Clear field and type with variable delays
        name_input.clear()
        for char in name:
            name_input.send_keys(char)
            time.sleep(random.uniform(0.2, 0.4))  # Slightly longer delays
        
        time.sleep(random.uniform(1.5, 2.5))
        
        # More natural transition to location field
        location_input = driver.find_element(By.ID, "search-name-address")
        location_input.clear()
        for char in location:
            location_input.send_keys(char)
            time.sleep(random.uniform(0.2, 0.4))
        
        time.sleep(random.uniform(1.5, 2.5))
        
        # Random mouse movement before clicking
        search_button = driver.find_element(
            By.CSS_SELECTOR, 
            "button.search-form-button-submit"
        )
        
        # Simulate human pause before clicking
        time.sleep(random.uniform(0.5, 1.5))
        search_button.click()
        
        # Wait longer for results with random delay
        time.sleep(random.uniform(6, 8))
        
        # Additional random scrolling after results
        driver.execute_script(f"window.scrollTo(0, {random.randint(100, 500)})")
        time.sleep(random.uniform(2, 4))
        
        # Wait for escape key instead of auto-closing
        print("Press ESC to close the browser...")
        def on_press(key):
            if key == keyboard.Key.esc:
                driver.quit()
                return False  # Stop listener
                
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
            
    except Exception as e:
        print(f"An error occurred: {e}")
        driver.quit()

if __name__ == "__main__":
    # Example usage
    search_person("John Doe", "New York, NY")
