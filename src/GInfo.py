import re
import yaml
import sqlite3
import re
import os
import subprocess

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, StaleElementReferenceException
from contextlib import contextmanager

from pyvirtualdisplay import Display as PYDisplay
from os import popen, mkdir
from time import sleep
from typing import Optional,Any


from Config import DISTRICTS,DBVER,DBNAME, selenium_display,selenium_driver,class_has

def mkdb(dbname:str=DBNAME):
  with sqlite3.connect(dbname) as con:
    try:
      cur = con.cursor()
      cur.execute(" \
          CREATE TABLE Streets_GInfo( \
            Name TEXT PRIMARY KEY, \
            Link TEXT NOT NULL, \
            District TEXT, \
            Houses TEXT, \
            Version INT NOT NULL, \
            Screenshot TEXT)")
      con.commit()
    except sqlite3.OperationalError as err:
      print(err,'(Ignoring)')


# def addstreet(con, name:str, link:str):
#   with con:
#     try:
#       print(f'Adding street "{name}" ({link})')
#       con.execute('INSERT INTO Streets(Name, Link, Version) VALUES(?, ?, ?)',
#                   (name, link, DBVER))
#     except sqlite3.Error as err:
#       print("Sqlite error", str(err))


def format_md(dbname:str=DBNAME):
  with sqlite3.connect(dbname) as con:
    sql='''
    SELECT Name,District,Houses,Link
    FROM Streets_GInfo
    ORDER BY District,Name'''

    with open("Streets_GInfo.md","w") as f:
      f.write(f"|№|Район|Название|Дома|\n")
      f.write(f"|-|-|-|-|\n")
      for i,r in enumerate(con.execute(sql)):
        name = str(r[0])
        district = str(r[1])
        houses = str(r[2])
        link = str(r[3])

        f.write(f"|{i}|{district}|[{name}]({link})|{houses}|\n")


def scrap(close:bool=True, dbname:str=DBNAME):
  """ Open display and samples chat messages """

  with selenium_display(visible=True,close=close) as disp, \
       selenium_driver(close=close) as driver:

    url = f"http://spb.ginfo.ru/ulicy/"
    print('Navigating to', url)
    driver.get(url)

    print('Searching elements')
    els=driver.find_elements(By.XPATH, f"//div[{class_has('street_unit')}]/a")
    street_urls=[el.get_attribute('href') for el in els]
    print(f"Found {len(street_urls)} street links")

    with sqlite3.connect(dbname) as con:
      for url in street_urls:
        try:
          print('Navigating to', url)
          driver.get(url)
        except Exception as err:
          print(f'Cant navigate to {url} ({err})')
          continue

        try:
          elname=driver.find_elements(
            By.XPATH,
            f"//div[{class_has('h1_share')}]/h1")[0]
          name=re.sub(" в Санкт-Петербурге", "", elname.text)
        except Exception as err:
          print(f'Cant find name ({err}), skipping')
          continue

        try:
          eldistr=driver.find_elements(
            By.XPATH,
            f"//div[{class_has('opis_ulica')}]/a")[0]
          district=re.sub(' районе', '', eldistr.text)
          if "Курортн" in district or \
             "Петродвор" in district or \
             "Централ" in district:
            district = re.sub(r"ом", r"ый", district)
          else:
            district = re.sub(r"ом", r"ий", district)

          district = district if district in DISTRICTS else None
        except Exception as err:
          print(f'Cant find District ({err})')
          district=None

        try:
          houslist=[]
          eldoms=driver.find_elements(
            By.XPATH,
            f"//div[{class_has('dom_list')}]/div/a")
          for el in eldoms:
            houslist.append(el.text)
          houses=', '.join(houslist)
        except Exception as err:
          print(f'Cant find houses ({err})')
          houses=None

        print(f"Adding name '{name}'\ndistrict '{district}'\nhouses '{houses}'")
        try:
          con.execute('''
            INSERT INTO Streets_GInfo(Name, Link, District, Houses, Version)
            VALUES(?, ?, ?, ?, ?)''', (name, url, district, houses, DBVER))
        except sqlite3.Error as err:
          print("Sqlite error", str(err), "(ignoring)")


def scrap_screenshots(dbname:str=DBNAME):
  with selenium_display(visible=True,close=True) as disp, \
       selenium_driver(close=True) as driver:

    ret=subprocess.call(['convert','-version'])
    assert ret==0

    screenshotdir=os.path.dirname(os.path.abspath(__file__)) + '/../screenshots/'
    if not os.path.isdir(screenshotdir):
      os.mkdir(screenshotdir)

    with sqlite3.connect(dbname) as con:
      sql="SELECT Name,Link FROM Streets_GInfo WHERE Link is NOT NULL ORDER BY Name"
      for i,r in enumerate(con.execute(sql)):
        name = str(r[0])
        url = str(r[1])

        try:
          print('Navigating to', url)
          driver.get(url)
        except Exception as err:
          print(f'Cant navigate to {url} ({err})')
          continue

        try:
          print(f"Capturing {name}")
          els=driver.find_elements(
            By.XPATH,
            f"//div[{class_has('right_block_2')}]")
          if len(els)<1:
            continue

          screenshot_file="/tmp/street_screenshot.png"
          print(f"Saving {screenshot_file}")
          els[0].screenshot(screenshot_file)
          small_screenshot_filename=("small_screenshot_%04d.png" %(i,))
          small_screenshot_file=screenshotdir+'/'+small_screenshot_filename

          print(f"Converting to {small_screenshot_file}")
          ret=subprocess.call(['convert', '-resize', '192x192', screenshot_file, small_screenshot_file])
          if ret!=0:
            print(f"Error code is {ret} (!=0), skipping")
            continue

        except Exception as err:
          print(f'Cant prepare a screenshot ({err}), skipping')
          continue

        try:
          print(f"Updating name '{name}'\nscreenshot '{small_screenshot_filename}'\n")
          con.execute('''
            UPDATE Streets_GInfo SET Screenshot = ? WHERE Name = ?''',
            (small_screenshot_filename, name))
        except sqlite3.Error as err:
          print("Sqlite error", str(err), "(ignoring)")






