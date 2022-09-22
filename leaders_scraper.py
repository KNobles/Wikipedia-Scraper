import requests
from requests import Session
from bs4 import BeautifulSoup
import re
import json
import time

cache = {}
def hashable_cache(f):
    def inner(url, session):
        if url not in cache:
            cache[url] = f(url, session)
        return cache[url]
    return inner

@hashable_cache
def get_first_paragraph(wikipedia_url: str, session: Session):
    '''
    Returns the first paragraph of a wikipedia article. The article must be about a personality such as a country leader or a famous star
    @param wikipedia_url: must be a wikipedia url
    @param session: a Session object to make it go faster
    @return: the first paragraph of the given wikipedia url sanitazed with a regular expression
    '''
    print(wikipedia_url)
    first_paragraph = ""
    wikipedia_request = session.get(wikipedia_url)
    soup = BeautifulSoup(wikipedia_request.text, "html.parser")
    for paragraph in soup.find_all("p"):
        if paragraph.find("b"):
            first_paragraph = paragraph.text
            break
    return re.sub("\[(.*?)\]", "",first_paragraph).replace("\n", "")

def get_leaders():
    '''
    This function creates a dictionary of leaders from an API and by organizing them by their countries
    @return: a dictionary of countries containing a dictionary of their respective leaders and other informations about them 
    '''
    leaders_dict = {}
    root_url = "https://country-leaders.herokuapp.com"
    countries_url = root_url + "/countries"
    cookies_url = root_url + "/cookie"
    leaders_url = root_url + "/leaders"
    cookies = requests.get(cookies_url).cookies
    countries = requests.get(countries_url, cookies=cookies).json()
    with Session() as session:
        for country in countries:
            param_country = "country=" + country
            leaders = requests.get(leaders_url, cookies=cookies, params=param_country)
            i = 0
            while leaders.status_code == 403:
                print("Getting new cookies...")
                leaders = requests.get(leaders_url, cookies=cookies, params=param_country)
                i += 1
                if i == 3:
                    return {}
                time.sleep(2)
            for leader in leaders.json():
                leader['first_paragraph'] = get_first_paragraph(leader['wikipedia_url'], session)
                leaders_dict.setdefault(country, []).append(leader)
        return leaders_dict

def save(leaders: dict):
    with open("leaders.json", "w", encoding="utf-8") as leaders_file:
        leaders_file.write(json.dumps(leaders, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    leaders = get_leaders()
    save(leaders)
