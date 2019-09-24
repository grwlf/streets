import re
import yaml
import sqlite3
import re

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, StaleElementReferenceException
from contextlib import contextmanager

from pyvirtualdisplay import Display as PYDisplay
from os import popen
from time import sleep
from typing import Optional,Any

DBNAME="Streets.db"
DBVER=1
DISTRICTS=[
    "Адмиралтейский", "Василеостровский", "Выборгский", "Калининский", "Кировский", "Колпинский",
    "Красногвардейский", "Красносельский", "Кронштадтский", "Курортный", "Московский", "Невский",
    "Петроградский", "Петродворцовый", "Приморский", "Пушкинский", "Фрунзенский", "Центральный"
    ]

@contextmanager
def selenium_driver(close:bool=True):
  opts = webdriver.ChromeOptions()
  opts.binary_location = popen('which chromium').read().strip()
  driver = webdriver.Chrome(chrome_options=opts)
  yield driver
  if not close:
    print('Leave driver unclosed')
  else:
    driver.quit()

@contextmanager
def selenium_display(visible:bool=False, close:bool=True):
  display=PYDisplay(visible=(1 if visible else 0), size=(1024, 768))
  display.start()
  yield display
  if not close:
    print('Leave display unclosed')
  else:
    display.stop()

def mkdb(dbname:str=DBNAME):
  with sqlite3.connect(dbname) as con:
    try:
      cur = con.cursor()
      cur.execute(" \
          CREATE TABLE Streets( \
            Name TEXT PRIMARY KEY, \
            Link TEXT NOT NULL, \
            District TEXT, \
            Houses TEXT, \
            Version INT NOT NULL)")
      con.commit()
    except sqlite3.OperationalError as err:
      print(err,'(Ignoring)')


def addstreet(con, name:str, link:str):
  with con:
    try:
      print(f'Adding street "{name}" ({link})')
      con.execute('INSERT INTO Streets(Name, Link, Version) VALUES(?, ?, ?)',
                  (name, link, DBVER))
    except sqlite3.Error as err:
      print("Sqlite error", str(err))

def _class_has(cls:str)->str:
  return f"contains(concat(' ',normalize-space(@class),' '),' {cls} ')"


def scrap_streets(close:bool=True, dbname:str=DBNAME):
  """ Open display and samples chat messages """

  with selenium_display(visible=True,close=close) as disp, \
       selenium_driver(close=close) as driver:

    for page in range(1,29):
      url = f"https://mapdata.ru/sankt-peterburg/ulicy/stranica-{page}/"
      print('Navigating to', url)
      driver.get(url)

      print('Searching elements')
      links=driver.find_elements(By.XPATH,
          f"//div[{_class_has('content-block')}]"+
          f"//div[{_class_has('content-item')}]"+
          f"/a")

      with sqlite3.connect(dbname) as con:
        try:
          for l in links:
            name=l.text
            link=l.get_attribute('href')
            addstreet(con,name,link)
        except Exception as err:
          print(f'Exception {err} ignored')


def locate_district(driver):

  els=driver.find_elements(By.XPATH,
      f"//ul[{_class_has('breadcrumb')}]"+
      f"//li[last()-1]//span")

  if len(els)!=1:
    return None

  el=els[0]
  district = el.text.split()[1]
  if "Курортн" in district or \
     "Петродвор" in district or \
     "Централ" in district:
    districtN = re.sub(r"ого", r"ый", district)
  else:
    districtN = re.sub(r"ого", r"ий", district)

  return districtN if districtN in DISTRICTS else None


def locate_houses(driver)->Optional[str]:
  els_b=driver.find_elements(By.XPATH,
      f"//ul[{_class_has('information')}]"+
      f"//li[last()]//b")
  if len(els_b)==1 and ('Номера' in els_b[0].text):
    els_span=driver.find_elements(By.XPATH,
        f"//ul[{_class_has('information')}]"+
        f"//li[last()]//span")
    if len(els_span)==1:
      return els_span[0].text
    else:
      return None
  else:
    return None

def scrap_details(close:bool=True, dbname:str=DBNAME):

  districts=[]
  with selenium_display(visible=True,close=close) as disp, \
       selenium_driver(close=close) as driver:

    with sqlite3.connect(dbname) as con:

      sql="SELECT Name,Link FROM Streets ORDER BY Name"
      for i,r in enumerate(con.execute(sql)):
        name = str(r[0])
        url = str(r[1])

        print('Navigating to', url)
        driver.get(url)

        print('Collecting district...', end='')
        district=locate_district(driver)
        print(district)

        print('Collecting houses...', end='')
        houses=locate_houses(driver)
        print(houses)
