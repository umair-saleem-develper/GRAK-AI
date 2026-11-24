import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    print("Navigating to login...")
    driver.get("http://localhost:3000/login")
    
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
    driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys("umair@test.com")
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys("umairtest123")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    
    print("Logged in, waiting for dashboard...")
    WebDriverWait(driver, 10).until(EC.url_matches("http://localhost:3000/"))
    
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea")))
    print("On dashboard, sending message...")
    driver.find_element(By.CSS_SELECTOR, "textarea").send_keys("Hello")
    
    # Click send (usually a button with a lucide-send icon or similar, let's find the nearest button next to textarea)
    buttons = driver.find_elements(By.CSS_SELECTOR, "button")
    send_button = None
    for b in buttons:
        if b.find_elements(By.CSS_SELECTOR, "svg.lucide-send"):
            send_button = b
            break
    if send_button:
        send_button.click()
    else:
        # Fallback to just clicking the last button or form submit
        print("Could not find specific send button, clicking last button")
        buttons[-1].click()
        
    print("Waiting 15 seconds to observe logs...")
    time.sleep(15)
    
    print("\n--- BROWSER LOGS ---")
    logs = driver.get_log("browser")
    for entry in logs:
        print(f"[{entry['level']}] {entry['message']}")
        
finally:
    driver.quit()
