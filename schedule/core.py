import urllib

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options


def get_credentials(name):
    return{
        'vodovod': {
            'func': get_vodovod_data,
            'args': [64258, 'Racanovic Ljubo'],
        }
    }.get(name)


VODOVOD_URL = 'http://vodovodbudva.me/vodovodbudva/index.php/korisnici/provjera-zaduzenja'
POST_PATH = 'https://vodovodbudva.me/zaduzenje/indexp.php?idpot=64258&ime=Racanovic Ljubo'
fields = {
    'Ukupan dug': 'TotalAmountNE',
    'Iznos za plaćanje': 'TotalAmount',
}


async def get_vodovod_data(sifra, name, url=POST_PATH):
    params = urllib.parse.urlencode({'idpot': sifra, 'ime': name})
    full_url = f'{url}?{params}'
    return scraper(full_url)


def scraper(url):
    opt = get_options()
    print(f"open {url}")
    driver = webdriver.Firefox(options=opt)
    driver.get(url)
    WebDriverWait(driver, 1).until(EC.presence_of_element_located((
        By.NAME, 'TotalAmountNE')))
    output = {}
    for label, field in fields.items():
        value = driver.find_element_by_name(field).get_attribute('value')
        output[label] = value
    driver.quit()
    return output


def get_options():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=800,600")
    return options
