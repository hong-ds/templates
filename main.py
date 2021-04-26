import requests
from bs4 import BeautifulSoup
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from decouple import config

HOMEPAGE = "https://www.hermes.com"
HTML = "https://www.hermes.com/uk/en/category/women/bags-and-small-leather-goods/bags-and-clutches/#||Line"
GSHEET = "hermes-scrapper"
FUZZY_MATCH_RATE = 0.5


def scrapper():
    """Scrap from html, return dictionary"""
    responses = requests.get(HTML)
    soup = BeautifulSoup(responses.text, 'html.parser')

    items = {}

    item_htmls = soup.find_all("a", href=True)

    for item in item_htmls:
        link = HOMEPAGE + item['href']

        if item.find_all("h3", "product-item-name"):
            tag = item.find_all("h3", "product-item-name")[0]
            items[tag.contents[0]] = link

    return items


def connect_gsheet():
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('env/sa/sa.json', scope)
    client = gspread.authorize(creds)
    return client


def get_search_term(client):

    sheet = client.open(GSHEET)
    sheet_instance = sheet.get_worksheet(0)
    sheet_instance.col_count
    records_data = sheet_instance.get_all_values()
    return records_data



def get_fuzzy_matches(items, search_terms, match_threshold):
    """"Match items from scrapping and search terms with fuzzy match rate. """

    matches = {}
    for scrap, v in items.items():
        scrap_set = set(scrap.lower().split(' '))
        for term in search_terms:
            term_set = set(term[0].lower().split(' '))

            match_rate = len(term_set & scrap_set) / len(term_set)
            if match_rate > match_threshold:
                matches[scrap] = v
    return matches




items = scrapper()
client = connect_gsheet()
search_terms = get_search_term(client)

matches = get_fuzzy_matches(items, search_terms, FUZZY_MATCH_RATE)

sheet = client.open(GSHEET)
sheet_instance = sheet.get_worksheet(1)
cell_list = sheet_instance.range("A1:B1000")
for cell in cell_list:
    cell.value = ''

# Update in batch
sheet_instance.update_cells(cell_list)
