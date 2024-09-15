import re
import time
import json
import glob
import math
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import selenium.webdriver.support.expected_conditions as ec
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from pymongo import MongoClient
from airflow.decorators import dag, task
from airflow.utils.dates import relativedelta

MONGO_URI = 'mongodb+srv://admin:FjdPyasYNVBUhE11c%24D*DNG%40%25NcLa%5Ejh@rsai.mdb.ai.dev.tmtco.org/?replicaSet=RSAI&authSource=admin&ssl=false'
# MONGO_URI = "mongodb://root:example@mongo:27017"
DATABASE_NAME = "AddressDataNew"
COLLECTION_NAME = "BaseWardDistrictProvinceData"

WARD = "ward"
DISTRICT = "district"
PROVINCE = "province"
WARD_CODE = "ward_code"
DISTRICT_CODE = "district_code"
PROVINCE_CODE = "province_code"

def padding(index: str):
    while len(index) < 5:
        index = "0" + index

    return index

default_args = {
    'owner': 'donvihanhchinh',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}

@dag(dag_id='update_don_vi_hanh_chinh_02', 
     default_args=default_args, 
     start_date=datetime(2024, 7, 1), 
    #  schedule_interval='0 0 1 * *')
     schedule_interval=relativedelta(months=3))
def update_danh_muc_hanh_chinh():

    @task()
    def down_danhmuchanhchinh():

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

        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-ssl-errors=yes')
        options.add_argument('--ignore-certificate-errors')
        prefs = {
            "download.default_directory" : "/home/seluser",
            # "download.prompt_for_download": False,
            # "directory_upgrade": True,
            # "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)

        driver = webdriver.Remote(
            command_executor='http://remote_chromedriver:4444/wd/hub',
            options=options
        )
        
        driver.get("https://danhmuchanhchinh.gso.gov.vn/Doi_Chieu_Moi.aspx")
        try:
            input_value = driver.find_element(By.XPATH, value='//*[@id="ctl00_PlaceHolderMain_txtNgay_I"]')
            now_day = input_value.get_attribute("value")
            driver.find_element(By.XPATH, value='//*[@id="ctl00_PlaceHolderMain_txtNgayDC_I"]').clear()
            driver.find_element(By.XPATH, value='//*[@id="ctl00_PlaceHolderMain_txtNgayDC_I"]').send_keys(update_dmy(now_day))
            time.sleep(1)
            input_value = driver.find_element(By.XPATH, value='//*[@id="ctl00_PlaceHolderMain_txtNgayDC_I"]')
            print(input_value.get_attribute("value"))

            button = WebDriverWait(driver, 10) \
                    .until(ec.presence_of_element_located((By.XPATH, "//*[@id=\"ctl00_PlaceHolderMain_cmdThucHien_CD\"]/span")))
            time.sleep(1)   
            button.click()
            time.sleep(1)

            button_down = WebDriverWait(driver, 10) \
                    .until(ec.presence_of_element_located((By.XPATH, "//*[@id=\"ctl00_PlaceHolderMain_cmdExcel_B\"]")))
            time.sleep(1)
            print("button found!!!!", button_down.text)
            button_down.click()
            time.sleep(5)
            driver.close()
        # try:
        #     print(button.text)
        #     print("button found!!!!")
        #     button.click()
        #     time.sleep(5)
        #     driver.close()
        except Exception as e:
            print(f"ERROR {e}")
            driver.close()

    @task()
    def load_danhmuchanhchinh():

        re_dd_mm_yy = re.compile(r"\d{2}\_\d{2}\_\d{4}")

        file_path = glob.glob("/opt/airflow/data/selenium_downloads/*.xls")
        print("file_path", file_path)
        list_d_m_y = []
        for path in file_path:
            a = re_dd_mm_yy.search(path)
            d_m_y = a.group()
            list_d_m_y.append([d_m_y, path])

        new_path = list_d_m_y[0][1]
        new_d = list_d_m_y[0][0].split("_")[0]
        new_m = list_d_m_y[0][0].split("_")[1]
        new_y = list_d_m_y[0][0].split("_")[2]
        for d_m_y, path in list_d_m_y:
            if d_m_y.split("_")[2] > new_y:
                new_path = path
                new_y = d_m_y.split("_")[2]
                new_m = d_m_y.split("_")[1]
                new_d = d_m_y.split("_")[0]
            elif d_m_y.split("_")[2] == new_y:
                if d_m_y.split("_")[1] > new_m:
                    new_path = path
                    new_y = d_m_y.split("_")[2]
                    new_m = d_m_y.split("_")[1]
                    new_d = d_m_y.split("_")[0]
                elif d_m_y.split("_")[1] == new_m:
                    if d_m_y.split("_")[0] > new_d:
                        new_path = path
                        new_y = d_m_y.split("_")[2]
                        new_m = d_m_y.split("_")[1]
                        new_d = d_m_y.split("_")[0]
        print(new_path)

        df = pd.read_excel(new_path)
        df = df.fillna("")
        print(f"load donvihanhchinh file with {df.shape} shape")
        return df.to_json()
    
    @task(multiple_outputs=True)
    def create_update_data(df):
        print(f"type df {type(df)}")
        df = json.loads(df)
        print(f"type df {type(df)}")
        df = pd.DataFrame(df)
        print(f"type df {type(df)}")
        list_info_address = []
        dict_update_address_old = {}

        for idx, raw in df.iterrows():
            ward_name = raw['Tên Xã']
            ward_code = raw['Xã']
            district_name = raw['Tên QH']
            district_code = raw['QH']
            province_name = raw['Tên Tỉnh']
            province_code = raw['Tỉnh']

            ward_name_dc = raw['Tên Xã DC']
            district_name_dc = raw['Tên QH DC']

            data = {
                WARD: ward_name if ward_name != '' and isinstance(ward_name, str) else "",
                WARD_CODE: str(int(ward_code)) if ward_code != '' and not math.isnan(ward_code) else "",
                DISTRICT: district_name if district_name != '' and isinstance(district_name, str) else "",
                DISTRICT_CODE: str(int(district_code)) if district_code != '' and not math.isnan(district_code) else "",
                PROVINCE: province_name if province_name != '' and isinstance(province_name, str) else "",
                PROVINCE_CODE: str(int(province_code)) if province_code != '' and not math.isnan(province_code) else "",
                "list_old_address": [],
                "list_place": [],
                "raw_info": []
            }
            
            if ward_name == ward_name_dc:
                key_map = "@".join([data[WARD_CODE], data[DISTRICT_CODE], data[PROVINCE_CODE]])
                list_info_address.append(data)
                dict_update_address_old[key_map] = []
            elif ward_name == "":
                data = list_info_address.pop(-1)
                key_map = "@".join([data[WARD_CODE], data[DISTRICT_CODE], data[PROVINCE_CODE]])
                
                address_old_mapping = {
                    "District": district_name_dc,
                    "Ward": ward_name_dc
                }
                data['list_old_address'].append(address_old_mapping)
                list_info_address.append(data)
                dict_update_address_old[key_map].append([address_old_mapping, data])
            else:
                key_map = "@".join([data[WARD_CODE], data[DISTRICT_CODE], data[PROVINCE_CODE]])
                
                address_old_mapping = {
                    "District": district_name_dc,
                    "Ward": ward_name_dc
                }
                data['list_old_address'].append(address_old_mapping)
                list_info_address.append(data)
                dict_update_address_old[key_map] = [[address_old_mapping, data]]

        print(f"length of list_info_address {len(list_info_address)}\n"
              f"length of dict_update_address_old {len(dict_update_address_old)}")

        return {"list_info_address": list_info_address, 
                "dict_update_address_old": dict_update_address_old}

    @task()
    def update_to_db(dict_update_address_old: dict):
        mongo_client = MongoClient(MONGO_URI)
        collection = mongo_client[DATABASE_NAME][COLLECTION_NAME]
        print(type(dict_update_address_old))
        for key, val in dict_update_address_old.items():
            if val == []:
                continue

            ward_code = key.split("@")[0]
            dis_code = key.split("@")[1]
            pro_code = key.split("@")[2]

            query = {
                # WARD_CODE: padding(ward_code),
                WARD_CODE: f"{int(ward_code):05d}",
                DISTRICT_CODE: dis_code,
                PROVINCE_CODE: pro_code
            }
            print(f"QUERY ==> {query}")

            cur = collection.find(query)
            
            list_old_address: list = cur['old_address']
            list_old_address.extend(val[0][1]['list_old_address'])
            
            # old_address = [addr for addr in list_old_address if addr not in list_old_address]
            data_update = {
                "ward": val[0][1]['ward'],
                "district": val[0][1]['district'],
                "old_address": list_old_address
            }
            
            print(f" query {query}"
                    f" update data {data_update} \n")
            
        mongo_client.close()


    down_file = down_danhmuchanhchinh()
    df_danh_muc_hanh_chinh = load_danhmuchanhchinh()

    down_file >> df_danh_muc_hanh_chinh
    update_address_old = create_update_data(df=df_danh_muc_hanh_chinh)
    update_to_db(dict_update_address_old=update_address_old['dict_update_address_old'])

greet_dag = update_danh_muc_hanh_chinh()
