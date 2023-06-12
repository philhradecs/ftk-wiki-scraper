from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager

import json

options = ChromeOptions()
options.add_argument("--headless=new")
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)

base_url = "https://fortheking.fandom.com/wiki/"
lists = [
  "List_of_arcane_weapons",
  "List_of_blades",
  "List_of_blunt_weapons",
  "List_of_bows",
  "List_of_instruments",
  "List_of_polearms",
  "List_of_staves"
]

def flatten(l):
  return [item for sublist in l for item in sublist]

def chunks(lst, n):
  for i in range(0, len(lst), n):
    yield lst[i:i + n]

def extract_table(table):

  # get rows without headers
  rows = table.find_all('tr')[1:]
  rowsData = []

  def is_new_group(row):
    return len(row.find_all('td')) > 6

  weapon_groups = []
  for row in rows:
    if is_new_group(row):
      weapon_groups.append([row])
    else:
      last_group = weapon_groups[-1]
      last_group.append(row)

  for weapon_rows in weapon_groups:
    weapon = None
    for row in weapon_rows:
      cells = row.find_all('td')

      if len(cells) < 4:
        continue

      if len(cells) > 6:
        a = cells[0].a
        weapon_image = a.img['data-src'].split('/revision')[0] if a and a.img else "no image"
        weapon_name = a['title'] if a else 'no name'
        weapon_type = cells[1].a['title']
        weapon_skill = cells[2].a['title']
        rarity = cells[10].text
        weapon =  { 
          'weapon_name': weapon_name.strip(),
          'weapon_skill': weapon_skill.strip(),
          'weapon_type': weapon_type.strip(),
          'weapon_image': weapon_image.strip(),
          'rarity': rarity.strip(),
          'attacks': []
        }

        cells = cells[5:9]
      
      attack_name = cells[0].text
      diceImgIdx = len(cells[1].find_all('img')) - 1
      dice = int(cells[1].find_all('img')[diceImgIdx]['alt'])
      dmg = cells[2].text.strip().replace(' dmg', '').split('/')[0]
      weapon['attacks'].append({
        'attack_name': attack_name.strip(),
        'dice': dice,
        'dmg': int(dmg) if dmg.isnumeric() else 0
      })

    if weapon:
      rowsData.append(weapon)

  return rowsData

def scrape_url(url):
  driver.get(url)

  WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "infobox")))

  html = driver.page_source

  list_page = BeautifulSoup(html, "html.parser")

  # get weapon tables 
  weapon_tables = list_page.find_all('table')[1:]

  list_weapons = flatten([extract_table(table) for table in weapon_tables])

  return list_weapons

try:
  list_weapons = []

  for weapon_list in lists: 
    url = base_url + weapon_list
    print ('scraping {}'.format(weapon_list))
    scraped = scrape_url(url)
    list_weapons.append(scraped)
    print ('extracted {} weapons from {}'.format(len(scraped), url.split('/')[-1]), end='\n\n')

  weapons = flatten(list_weapons)

  with open('ftk_weapons.json', 'w', encoding='utf-8') as f:
    json.dump(weapons, f, ensure_ascii=False)

finally:
  driver.quit()
  print ("done")




