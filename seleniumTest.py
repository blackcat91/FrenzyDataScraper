from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

chrome_options = Options()

chrome_options.add_argument("--headless")


driver = webdriver.Chrome(options=chrome_options, service=Service(ChromeDriverManager().install()))

driver.get("https://animefrenzy.net/watch/fullmetal-alchemist-brotherhood-episode-1")


servers = driver.find_elements(By.CSS_SELECTOR, "a.btn-server")
serverLinks=[]

for server in servers:
    href = server.get_attribute("href")
    name = server.text.lstrip().rstrip()
    serverLinks.append({'href': href, 'name': name})
print(serverLinks[0]['href'])

def get_server_links(epLink : str ) :
    chrome_options = Options()

    chrome_options.add_argument("--headless")


    driver = webdriver.Chrome(options=chrome_options, service=Service(ChromeDriverManager().install()))
    driver.get(epLink)


    servers = driver.find_elements(By.CSS_SELECTOR, "a.btn-server")
    serverLinks=[]

    for server in servers:
        href = server.get_attribute("href")
        name = server.text.lstrip().rstrip()
        serverLinks.append({'href': href, 'name': name})
    driver.close()
    return serverLinks