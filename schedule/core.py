import calendar
from datetime import datetime

import requests

from urllib.parse import urlencode
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options


async def call_by_name(name):
    cred = get_credentials(name)
    return await cred['func'](*cred['args'])


def get_credentials(name):
    return {
        'vodovod': {
            'func': get_vodovod_data,
            # 'args': [64258, 'Racanovic Ljubo'],
            'args': [64261, 'Racanovic Ljubo'],
        },
        'electricity': {
            'func': get_electicity_data,
            # 'args': ['091683659', '15N4E5B2514808511'],
            'args': ['091683691', '15N4E5B2514808425'],
        },
        'komunalno': {
            'func': get_komunalno_data,
            'args': ['G22794 Racanovic Ljubo',
                     '85310 BUDVA, UL XVIII/SP.III/ST.19  AG 19'],
        }
    }.get(name)


POST_PATH = 'https://vodovodbudva.me/zaduzenje/indexp.php'
PDF_PATH = 'https://www.vodovodbudva.me/zaduzenje/search3.php'
ELECT = 'https://www.racun.epcg.com/provjera-racuna'
ELECT2 = 'https://www.racun.epcg.com/pdf-bill/1'
# class=pdf-download

async def get_vodovod_data(sifra, name, url=POST_PATH, pdf_link=PDF_PATH):
    params = urlencode({
        'idpot': sifra,
        'ime': name,
    })

    full_url = f'{url}?{params}'
    pdf_url = f'{pdf_link}?{params}'
    results = {
        'sifra': sifra,
        'name': name,
    }
    with Scrapper(full_url, wait='TotalAmountNE') as browser:
        results['Ukupan dug'] = browser.get_by_name('TotalAmountNE')
        results['Iznos za plaćanje'] = browser.get_by_name('TotalAmount')

    results_msg = "\n".join(
        [f"{key}: {value}" for key, value in results.items()])

    msg = f'Vodovod:\n{results_msg}\n\n{full_url}\n\nPDF:{pdf_url}'
    return {'msg': msg}


async def get_electicity_data(home, brojila, url=ELECT):
    params = {'edit-home-pretplatni-broj': home,
              'edit-home-broj-brojila': brojila}
    # full_url = f'{url}?{urlencode(params)}'
    full_url = url

    results = {
        'Pretplatni/Naplatni broj *': home,
        'Broj brojila': brojila,
    }

    with Scrapper(full_url, method='POST', data=params, wait='total') as scr:
        results['Ukupno za uplatu'] = scr.get_by_class('total')
        results['Poslednji račun'] = scr.get_by_class('last-bill')
        session = requests.session()
        selenium_cookies = scr.driver.get_cookies()
        for cookie in selenium_cookies:
            session.cookies.set(cookie["name"], cookie["value"])

        pdf_response = session.get(ELECT2)
        pdf_bytes = pdf_response.content

    results_msg = "\n".join(
        [f"{key}: {value}" for key, value in results.items()])

    msg = f'Electricity:\n{results_msg}\n\n{full_url}'
    return {'msg': msg, 'files': [{'Electricity.pdf': pdf_bytes}]}


class KomunalnoPrice:
    def __getitem__(self, key):
        if not isinstance(key, int):
            raise ValueError('Key must be an integer')

        if key == 0:
            return self.get_value(1)
        denom = key // 12
        if denom:
            key -= 12 * denom
        return self.get_value(key)

    @staticmethod
    def get_value(key):
        # if key in [6, 7, 8]:
        if key in [6, 7, 8, 9]:
            return 5.5
            # return 4.32
        # return 3.33
        return 4.23


async def get_komunalno_data(korisnic, adress):
    now = datetime.now()
    month = now.month - 1
    if now.day < 9:
        month -= 1
    results = {
        "Korisnic": korisnic,
        "Adresa": adress,
        "Month": calendar.month_name[month],
        "Ukupno": KomunalnoPrice()[month],
    }
    results_msg = "\n".join(
        [f"{key}: {value}" for key, value in results.items()])

    msg = f'Komunalno:\n{results_msg}'
    return {'msg': msg}


class Scrapper:
    def __init__(self, url, method="GET", data=None, wait='TotalAmountNE'):
        opt = get_options()
        self.driver = webdriver.Firefox(options=opt)
        self.driver.set_window_size(200, 200)
        meth = method.upper()
        self.data = data
        self.driver.get(url)
        if meth == 'GET':
            ...
        elif meth == 'POST':
            marker = next(iter(data))
            WebDriverWait(self.driver, 1).until(
                EC.presence_of_element_located((By.ID, marker)))
            for _id, value in data.items():
                input_element = self.driver.find_element_by_id(_id)
                input_element.send_keys(value)
            input_element = self.driver.find_element_by_id('edit-submit')
            input_element.click()
        else:
            raise TypeError()
        if wait:
            try:
                WebDriverWait(self.driver, 1).until(
                    EC.presence_of_element_located((By.NAME, wait)))
            except TimeoutException:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, wait)))

    def open_page(self, url, until):
        # self.driver.set_timeoi
        self.driver.get(url)
        WebDriverWait(self.driver, 1).until(until)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.driver.quit()

    def get_by_name(self, field):
        return self.driver.find_element_by_name(field).get_attribute('value')

    def get_by_class(self, field):
        return self.driver.find_element_by_class_name(field).\
            find_element_by_class_name('value').get_attribute('innerHTML')


def pdf_page_loaded(driver):
    try:
        element = driver.find_element(
            By.CSS_SELECTOR, "*[data-page-number='2'][data-loaded='true']")
    except NoSuchElementException:
        return False
    res = element.get_attribute("data-loaded") == "true"
    return res


def get_options():
    options = Options()
    options.add_argument("--headless")
    # options.add_argument("--window-size=800,600")


    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", "/tmp/")
    options.set_preference("browser.download.useDownloadDir", True)
    options.set_preference("browser.download.alwaysOpenPanel", False)
    options.set_preference("browser.download.viewableInternally.enabledTypes", "")
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdftext/plainapplication/texttext/xmlapplication/xml")
    # options.set_preference("pdfjs.disabled", True)  # disable the built-in PDF viewer
    return options
