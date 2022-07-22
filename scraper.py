import constants
import asyncio
import threading
import aiohttp
import requests
import pyodbc
import pandas as pd
from bs4 import BeautifulSoup

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
    animeData["cover"] = soup.select_one('.film_poster > img').get('src')
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
            
        else:
            animeData[key] = detail.select_one('.name').text
    with pyodbc.connect(constants.CNXN_STR) as connection:
        insert_details_sql = f""
        print("Inserting Details...")
        try:
            insert = connection.execute(insert_details_sql)
            insert.commit()
            title = animeData['title']
            select_sql = f"SELECT Id FROM Details WHERE Title= '{title}'"
            data = pd.read_sql(select_sql, connection)
            animeId = data['Id']
            for genre in g:
                insert_series_genre_sql = f""
                connection.execute(insert_series_genre_sql)
            
            connection.commit()
        except:
            print("Error Adding Data!!")
            return None
    get_episodes(soup, animeId)
        
        
        
    
def get_episodes(soup : BeautifulSoup, animeId):
    episodesLink = soup.select_one('.film-buttons .btn-play').get('href')
    episodesPage = requests.get(constants.BASEURL+episodesLink)
    episodesSoup = BeautifulSoup(episodesPage.text, PARSER)
    episodes = episodesSoup.select('.detail-infor-content>.ss-list> a')
    with pyodbc.connect(constants.CNXN_STR) as connection:
        for episode in episodes:
            episodeLink = episode.get('href')
            epNum = int(episode.text)
            episodePage = requests.get(constants.BASEURL+episodeLink)
            episodeSoup = BeautifulSoup(episodePage.text, PARSER)
            servers = episodeSoup.select('.ps__-list > .item > a')
            download = episodeSoup.select_one('a.pc-download').get('href')
            print("Inserting Episodes...")
            try:
                insert_episode_sql = f"INSERT INTO Episodes (SeriesId, Episode, Download) VALUES('{animeId}', '{epNum}', '{download}')"
                connection.execute(insert_episode_sql)
                for server in servers:
                    name = server.text
                    link = server.get('href')
                    insert_link_sql = f"INSERT INTO Links(SeriesId, Source, Link) VALUES('{animeId}', '{name}', '{link}')"
                    connection.execute(insert_link_sql)
                connection.commit()
            except:
                print("Couldn't Add Episode!!")
        
if __name__ == '__main__':
    main()