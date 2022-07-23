import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pyodbc
import requests
import constants
from bs4 import BeautifulSoup

PARSER = 'html.parser'

def main():
 
    for page in range(1, constants.MAX_PAGES):
        with requests.get(constants.PAGEURL+page) as response:
            html = response.text
        
        soup = BeautifulSoup(html, PARSER)
        animes = soup.select('.flw-item > .film-poster > a')
        
        for anime in animes:
            link = anime.get('href')
            animePage = requests.get(constants.BASEURL+link)
            animeSoup = BeautifulSoup(animePage.text, PARSER)
            
            get_details(animeSoup)
           
        

def get_details(soup : BeautifulSoup):
    title = soup.select_one('.film-name').text
    select_sql = f"SELECT Id FROM Details WHERE Title= '{title}'"
    with pyodbc.connect(constants.CNXN_STR) as connection:
        data = pd.read_sql_query(select_sql, connection)
        animeId = data['Id'][0]
    episodesLink = soup.select_one('.film-buttons .btn-play').get('href')
    episodesPage = requests.get(constants.BASEURL+episodesLink)
    episodesSoup = BeautifulSoup(episodesPage.text, PARSER)
    episodes = episodesSoup.select('.detail-infor-content>.ss-list> a')
    with pyodbc.connect(constants.CNXN_STR) as connection:
        for episode in episodes:
            episodeLink = constants.BASEURL+episode.get('href')
            get_server_links(episodeLink, animeId)
     

def get_server_links(epLink : str, animeId ) :
    chrome_options = Options()

    chrome_options.add_argument("--headless")


    driver = webdriver.Chrome(options=chrome_options, service=Service(ChromeDriverManager().install()))
    driver.get(epLink)


    servers = driver.find_elements(By.CSS_SELECTOR, "a.btn-server")
    

    with pyodbc.connect(constants.CNXN_STR) as connection:
        print("Creating Servers...")
        for server in servers:
            href = server.get_attribute("href")
            name = server.text.lstrip().rstrip()
            insert_episode_sql = f"INSERT INTO Links  VALUES('{animeId}', '{name}', '{href}')"
            connection.execute(insert_episode_sql)
        
        connection.commit()
        print("Servers Added!")
            
    driver.close()
    
    
    if __name__ == '__main__':
        main()