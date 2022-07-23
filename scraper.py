import constants
import html
import threading
import requests
import pyodbc
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

PARSER = 'html.parser'

animeCounter = 1



def main():
    threads = [];
    for page in range(1, constants.MAX_PAGES):
        t = threading.Thread(target=get_session, args=(str(page),))
        t.start()
        
    
 

            
def get_session(page):

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
    animeData = dict()
    animeData["cover"] = soup.select_one('.film-poster >img').get('src')
    animeData["title"] = soup.select_one('.film-name').text
    
    animeDetails = soup.select('.anisc-info .item')
    g = []
    global animeId
    for detail in animeDetails:
        key = detail.select_one('.item-head').text
        if "Overview" in key:
            
            animeData[key] = detail.select_one('.text').text
            
        elif "Genres" in key:
            
            genres= detail.select('a')
            for genre in genres:
                g.append(genre.text)
        elif "Status" in key:
            animeData[key] = detail.select_one('a').text
            
        else:
            animeData[key] = detail.select_one('.name').text
    with pyodbc.connect(constants.CNXN_STR) as connection:
        title = html.escape(animeData['title'])
        cover = html.escape(animeData["cover"])
        overview = html.escape(animeData['Overview:'])
        otherNames = html.escape(animeData['Other names:'])
        language = animeData['Language:']
        episodeTotal = html.escape(animeData['Episodes:'])
        views = html.escape(animeData['Views:'])
        timeformat = "%Y-%m-%d %H:%M:%S"
        lastAdded = datetime.strptime(animeData['Last Added:'], timeformat)
        release = int(animeData['Release Year:'])
        animetype = html.escape(animeData['Type:'])
        status = html.escape(animeData['Status:'])
        insert_details_sql = f"INSERT INTO Details VALUES('{title}', '{cover}', '{overview}', '{otherNames}', '{language}', '{episodeTotal}', '{views}', '{lastAdded}', '{release}', '{animetype}', '{status}')"
    
        
        insert = connection.execute(insert_details_sql)
        insert.commit()
        
        select_sql = f"SELECT Id FROM Details WHERE Title= '{title}'"
        data = pd.read_sql_query(select_sql, connection)
        animeId = data['Id'][0]
      
        for genre in g:
            genre = genre.rstrip().lstrip()
            select_sql = f"SELECT Id FROM Genres WHERE Name= '{genre}'"
            gData = pd.read_sql_query(select_sql, connection)
            try:
                gId = gData['Id'][0]
            except Exception:
                gId = insert_genre(connection, genre)
            insert_series_genre_sql = f"INSERT INTO SeriesGenres  VALUES('{animeId}', '{gId}')"
            connection.execute(insert_series_genre_sql)
            
        
        connection.commit()
      
    get_episodes(soup, animeId)
        

def insert_genre(connection: pyodbc.Connection, genre):
    insert_genre = f"INSERT INTO Genres VALUES('{genre}')"
    insert = connection.execute(insert_genre)
    insert.commit()
    select_sql = f"SELECT Id FROM Genres WHERE Name= '{genre}'"
    gData = pd.read_sql_query(select_sql, connection)
    return gData['Id'][0]
    
def get_episodes(soup : BeautifulSoup, animeId):
    episodesLink = soup.select_one('.film-buttons .btn-play').get('href')
    episodesPage = requests.get(constants.BASEURL+episodesLink)
    episodesSoup = BeautifulSoup(episodesPage.text, PARSER)
    episodes = episodesSoup.select('.detail-infor-content>.ss-list> a')
    with pyodbc.connect(constants.CNXN_STR) as connection:
        print("Inserting Episodes...")
        for episode in episodes:
            episodeLink = constants.BASEURL+episode.get('href')
            try:
                epNum = int(episode.text)
            except:
                epNum = int(episode.text.lstrip().rstrip().split("-")[0])
            episodePage = requests.get(episodeLink)
            episodeSoup = BeautifulSoup(episodePage.text, PARSER)
            
            download = episodeSoup.select_one('a.pc-download').get('href')
            
            
            insert_episode_sql = f"INSERT INTO Episodes  VALUES('{animeId}', '{epNum}', '{download}')"
            connection.execute(insert_episode_sql)
            connection.commit()
        print("Insert Completed")
                

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
        
if __name__ == '__main__':
    main()