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
import html
import re
from bs4 import BeautifulSoup

PARSER = 'html.parser'

def main():
 
    for page in range(1, constants.MAX_PAGES):
        with requests.get(constants.PAGEURL+str(page)) as response:
            html = response.text
        
        soup = BeautifulSoup(html, PARSER)
        animes = soup.select('.flw-item > .film-poster > a')
        
        for anime in animes:
            link = anime.get('href')
            animePage = requests.get(constants.BASEURL+link)
            animeSoup = BeautifulSoup(animePage.text, PARSER)
            
            get_details(animeSoup)
           
        

def get_details(soup : BeautifulSoup):
    chrome_options = Options()

    chrome_options.add_argument("--headless")


    driver = webdriver.Chrome(options=chrome_options, service=Service(ChromeDriverManager().install()))
   
    title = html.escape(soup.select_one('.film-name').text)
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
            try:
                epNum = int(episode.text)
            except:
                epNum = int(episode.text.lstrip().rstrip().split("-")[0])
            episodeLink = constants.BASEURL+episode.get('href')
            get_server_links(episodeLink, animeId,epNum, connection, driver)
    driver.close()
 
        
        

def get_server_links(epLink : str, animeId,epNum: int,  connection: pyodbc.Connection, driver : webdriver.Chrome ) :
    
    driver.get(epLink)


    servers = driver.find_elements(By.CSS_SELECTOR, "a.btn-server")
    

    
    print("Creating Servers...")
    for server in servers:
        href = server.get_attribute("href")
        name = server.text.lstrip().rstrip()
        insert_episode_sql = f"INSERT INTO Links  VALUES('{animeId}', '{epNum}', '{name}', '{href}')"
        connection.execute(insert_episode_sql)
        
    connection.commit()
    print("Servers Added!")
            
  
    
    
if __name__ == '__main__':
    main()