import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
import selenium.webdriver.support.expected_conditions as ec

def update_dmy(now_day: str):
    day = now_day.split("/")[0]
    month = now_day.split("/")[1]
    year = now_day.split("/")[2]
    update_year = str(int(year) + 1)
    return "/".join([day, month, update_year])

    # update_month = int(month) - 3
    # if update_month > 0:
    #     update_year = year
    #     return "/".join([day, f"{update_month:02d}", update_year])
    # else:
    #     update_month = int(month) - 3 + 12
    #     update_year = str(int(year) - 1)
    #     return "/".join([day, f"{update_month:02d}", update_year])
                   
def get_financial_report():
    try:
        # Set Chrome options
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-ssl-errors=yes')
        options.add_argument('--ignore-certificate-errors')
        # options.add_argument('--disable-gpu')  # Disable GPU
        # options.add_argument('--headless')  # Run headless
        # options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')  # Prevent crashes

        prefs = {
            "download.default_directory": "/home/seluser",  # Change to your desired download path
            # "download.prompt_for_download": False,
            # "directory_upgrade": True,
            # "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)

        # Connect to remote ChromeDriver
        driver = webdriver.Remote(
            command_executor='http://localhost:4444/wd/hub',
            options=options
        )
        
        print("Connected to remote ChromeDriver.")

        # Navigate to the website
        url = 'https://finance.vietstock.vn/bao-cao-phan-tich/phan-tich-doanh-nghiep'
        driver.get(url)
        print(f"Navigating to {url}")
        time.sleep(3)

        # # Locate and fill the keyword field
        # keyword_input = driver.find_element(By.ID, 'txtKeyword')
        # keyword_input.send_keys('Your keyword here')

        # Select the source from the dropdown
        source_dropdown = Select(driver.find_element(By.ID, 'ddlSources'))
        source_dropdown.select_by_visible_text('BSC')  # Select the source by visible text

        # Set the date range
        from_date_input = driver.find_element(By.ID, 'fromDate')
        now_day = from_date_input.get_attribute("value")
        # from_date_input.send_keys(update_dmy(now_day))  # Set 'Từ ngày' (From date)
        from_date_input.clear()
        from_date_input.send_keys("15/09/2024")
        time.sleep(1)

        # to_date_input = driver.find_element(By.ID, 'toDate')
        # to_date_input.send_keys('01/01/2024')  # Set 'Đến ngày' (To date)

        # Click the search button
        search_button = WebDriverWait(driver, 10).until(
                            ec.element_to_be_clickable((By.XPATH, "//button[@id='btnSearchEDoc']"))
                        )
        time.sleep(1)   
        search_button.click()
        time.sleep(5)

        is_next = 1
        while is_next:
            
            # Check if the close button is present
            close_buttons = driver.find_elements(By.CSS_SELECTOR, "button.ats-overlay-bottom-close-button")
            # If the close button exists, click the first instance
            if close_buttons:
                close_buttons[0].click()
                time.sleep(1)  # Add a delay if needed for the overlay to close
            else:
                print("Close button not found.")

            # Find all elements with <span>Tải về</span> and click them
            download_buttons = driver.find_elements(By.XPATH, "//span[text()='Tải về']/parent::a")

            # Loop through and click each button
            for button in download_buttons:
                try:
                    ActionChains(driver).move_to_element(button).perform()  # Scroll to the element
                    time.sleep(1) 
                    button.click()
                    print("Clicked a download button!")
                    time.sleep(1) 
                except Exception as e:
                    print(f"Error clicking button: {e}")

            # Locate the 'Next' button using the aria-label or 'page' attribute
            try:
                # Wait for the 'Next' button to be clickable
                wait = WebDriverWait(driver, 10)
                next_button = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '#report-paging li.next a[aria-label="next"]')))
                driver.execute_script("arguments[0].scrollIntoView();", next_button)
                wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, '#report-paging li.next a[aria-label="next"]')))
                driver.execute_script("arguments[0].click();", next_button)
                
                is_next = 1
                time.sleep(3)
            except Exception as e:
                is_next = 0

        # Close the driver
        driver.quit()

        print("PDF Download complete")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    get_financial_report()
