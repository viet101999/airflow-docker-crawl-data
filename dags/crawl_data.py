import os
import time
from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.utils.dates import relativedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait, Select
import selenium.webdriver.support.expected_conditions as ec

# File server path (Update with the actual path)
FILE_SERVER_PATH = '/path/to/your/file/server'

# Chrome options configuration
def setup_selenium_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-ssl-errors=yes')
    options.add_argument('--ignore-certificate-errors')
    # options.add_argument('--disable-gpu')  # Disable GPU
    # options.add_argument('--headless')  # Run headless
    # options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    prefs = {
            "download.default_directory": "/home/seluser",  # Change to your desired download path
            # "download.prompt_for_download": False,
            # "directory_upgrade": True,
            # "safebrowsing.enabled": True
        }
    # prefs = {
    #     "download.default_directory": FILE_SERVER_PATH,  # Set download directory to file server
    # }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Remote(
        # command_executor='http://localhost:4444/wd/hub',
        # command_executor='http://remote_chromedriver:4444/wd/hub',
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )

    return driver

# Selenium task to download PDF files
def download_pdf_files(driver):

    def update_dmy(now_day: str):
        day = now_day.split("/")[0]
        month = now_day.split("/")[1]
        year = now_day.split("/")[2]
        update_month = int(month) - 3
        if update_month > 0:
            update_year = year
            return "/".join([day, f"{update_month:02d}", update_year])
        else:
            update_month = int(month) - 3 + 12
            update_year = str(int(year) - 1)
            return "/".join([day, f"{update_month:02d}", update_year])
        
        # update_year = int(year) - 1
        # return "/".join([day, month, str(update_year)])

    driver.get('https://finance.vietstock.vn/bao-cao-phan-tich/phan-tich-doanh-nghiep')
    time.sleep(3)

    # Select the source from the dropdown
    source_dropdown = Select(driver.find_element(By.ID, 'ddlSources'))
    source_dropdown.select_by_visible_text('BSC')  # Select the source by visible text

    # Set the date range
    input_value = driver.find_element(By.ID, 'toDate')
    now_day = input_value.get_attribute("value")
    
    from_date_input = driver.find_element(By.ID, 'fromDate')
    from_date_input.clear()
    from_date_input.send_keys(update_dmy(now_day)) # Set 'Từ ngày' (From date)
    time.sleep(1)
    
    # Click search button
    search_button = WebDriverWait(driver, 10).until(
        ec.element_to_be_clickable((By.XPATH, "//button[@id='btnSearchEDoc']"))
    )
    time.sleep(1)
    search_button.click()
    time.sleep(5)

    is_next = 1
    while is_next:
        # Handle overlay close buttons
        close_buttons = driver.find_elements(By.CSS_SELECTOR, "button.ats-overlay-bottom-close-button")
        if close_buttons:
            close_buttons[0].click()
            time.sleep(1)

        # Find and click all download buttons
        download_buttons = driver.find_elements(By.XPATH, "//span[text()='Tải về']/parent::a")
        for button in download_buttons:
            try:
                ActionChains(driver).move_to_element(button).perform()  # Scroll to the element
                time.sleep(1)
                button.click()
                time.sleep(1)
            except Exception as e:
                print(f"Error clicking button: {e}")

        # Navigate to the next page if available
        try:
            wait = WebDriverWait(driver, 10)
            next_button = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '#report-paging li.next a[aria-label="next"]')))
            driver.execute_script("arguments[0].scrollIntoView();", next_button)
            wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, '#report-paging li.next a[aria-label="next"]')))
            driver.execute_script("arguments[0].click();", next_button)

            is_next = 1
            time.sleep(3)
        except Exception as e:
            is_next = 0

    driver.quit()
    print("PDF Download complete")

# DAG default arguments
default_args = {
    'owner': 'financial_report',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}

@dag(
    dag_id='download_financial_reports',
    default_args=default_args,
    start_date=datetime(2024, 9, 26), # Adjust start date accordingly
    # schedule_interval='@quarterly',  # Run every 3 months
    schedule_interval=relativedelta(months=3), # Run every 3 months
    # schedule_interval='*/2 * * * *', # */2: Every 2 minutes, *: Every hour, day, month, and day of the week.
    catchup=False
)
def download_reports_dag():
    
    @task()
    def download_and_save_pdfs():
        driver = setup_selenium_driver()
        download_pdf_files(driver)

    download_and_save_pdfs()

# Instantiate the DAG
download_dag = download_reports_dag()
