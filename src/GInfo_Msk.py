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
from textwrap import dedent


from Config_Msk import DBVER,DBNAME
from Util import selenium_display,selenium_driver,class_has

SCRIPT='''

function clearclass(item, cls) {
  item.classList.remove(cls);
}
function setclass(item, cls) {
  item.classList.add(cls);
}

function filter(predicate) {
  var nodelist = document.getElementById('data').getElementsByTagName('tr');
  var good = new Array()
  var bad = new Array()
  for (var i = 1; i < nodelist.length; i++) {
    var tr = nodelist.item(i);
    if (i % 100 == 0) {
      console.log('Processed '+i+' of '+nodelist.length)
    }
    if(predicate(tr)) {
      good.push(tr);
    }
    else {
      bad.push(tr);
    }
  }
  console.log('Collect '+good.length+' / '+bad.length)

  bad.forEach(function(el,index){
    el.style.display = "none";
  });
  good.forEach(function(el,index){
    el.style.display = "table-row";
  });

  console.log('Complete '+good.length+' / '+bad.length)
}

function matchtr(tr, record) {
  var tds = tr.getElementsByTagName('td');
  for(var j = 0 ; j <tds.length; j++) {
    <!-- console.log(tds[j].innerText.trim()) -->
    if (tds[j].innerHTML.trim() == record) {
      return true;
    }
  }
  return false
}

function trtext(tr) {
  var res = " ";
  var tds = tr.getElementsByTagName('td');
  for(var j = 0 ; j <tds.length; j++) {
    if (j!=0) res += " ; ";
    res += tds[j].innerText;
  }
  res += " ";
  return res
}

function matchre(record) {
  var re=RegExp(record,'i');
  return function(tr) {
    var ans=re.test(trtext(tr));
    if(ans>0)
      return true;
    else
      return false;
  };
}
'''

def format_html(dbname:str=DBNAME):
  with sqlite3.connect(dbname) as con:
    sql='''
    SELECT Name,District,Houses,Link
    FROM Streets_GInfo
    ORDER BY District,Name'''

    with open("Streets_GInfo_Msk.html","w") as f:
      f.write(dedent('''\
        <html>
        <head>
        <script>
        '''
        +SCRIPT+
        '''
        </script>
        </head>
        <body>
          <div>
            <p style="color:grey">
            Поиск видит строки таблицы как большие предложения, в которых текст
            колонок соединен символами ' ; ' (с пробелами). Поиск понимает
            регулярные выражения.  Регистр значения не имеет.
            </p>
            <p style="color:grey">
            Примеры:
            <ul style="color:grey">
            <li>'Верхний' - отфильтровать строки, в которых встречается строка Верхний</li>
            <li>'Верхний.* 4Б' - отфильтровать строки, в которых встречается слово
            Верхний, потом лбюбое количество любых символов, потом пробел, потом
            4Б</li>
            <li>'Профсоюзная|Вишнёвая' - отфильтровать строки, в которых
            находятся слово Профсоюзная или слово Вишнёвая</li>
            <li>'Вишнёвая.* 3|Профсоюзная' - отфильтровать строки, в которых
            находятся слова Профсоюзная или слово Вишнёвая-чтото-чтото-пробел-3</li>
            </ul>
            </p>
            <input type="text" size="45" id="input" onkeydown="
              if(event.keyCode == 13) {
                p=matchre(document.getElementById('input').value);
                filter(p);
                return false;
              }
              return true;
            "></input>
            <button onclick="
              p=matchre(document.getElementById('input').value);
              filter(p);
            ">Search!</button>
            <button onclick="filter(function(tr) { return true })" >Reset!</button>
          </div>
          <table id="data">
          <tr>
            <th>№</th>
            <th>Район</th>
            <th>Название</th>
            <th>Дома</th>
          </tr>
       '''))
      for i,r in enumerate(con.execute(sql)):
        name = str(r[0])
        district = str(r[1])
        houses = str(r[2])
        link = str(r[3])

        f.write(dedent(f'''
          <tr style="display:table-row">
            <td>{i}</td>
            <td>{district}</td>
            <td><a href='{link}'>{name}</a></td>
            <td>{houses}</td>
          </tr>
          '''))
      f.write(dedent('''
        </table>
        </body>
        </html>
        '''))

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
    sql=f'''
    SELECT Name,District,Houses,Link
    FROM Streets_GInfo
    ORDER BY District,Name'''

    with open("Streets_GInfo_Msk.md","w") as f:
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

  ret=subprocess.call(['convert','-version'])
  assert ret==0

  screenshotdir=os.path.dirname(os.path.abspath(__file__)) + '/../screenshots_msk/'
  if not os.path.isdir(screenshotdir):
    os.mkdir(screenshotdir)

  with selenium_display(visible=True,close=close) as disp, \
       selenium_driver(close=close) as driver:

    url = f"http://ginfo.ru/ulicy/"
    print('Navigating to', url)
    driver.get(url)

    print('Searching for elements')
    els=driver.find_elements(By.XPATH, f"//div[{class_has('street_unit')}]/a")
    street_urls=[el.get_attribute('href') for el in els]
    print(f"Found {len(street_urls)} street links")

    with sqlite3.connect(dbname) as con:
      for i,url in enumerate(street_urls):
        try:
          print('Navigating to', url)
          driver.get(url)
        except Exception as err:
          print(f'Cant navigate to {url} ({err})')
          continue

        try:
          elname=driver.find_elements(
            By.XPATH,
            f"//span[{class_has('this_page')}]")[0]
          name=elname.text
        except Exception as err:
          print(f'Cant find name ({err}), skipping')
          continue

        try:
          eldistr=driver.find_elements(
            By.XPATH,
            f"//div[{class_has('opis_ulica')}]/a")[0]
          district=re.sub('районе', 'район', eldistr.text)
          district=re.sub('поселении', 'поселение', district)
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

        try:
          print(f"Capturing screenshot of {name}")
          els=driver.find_elements(
            By.XPATH,
            f"//div[{class_has('right_block_2')}]")
          if len(els)!=1:
            raise ValueError('Cant find screenshot block ')

          screenshot_file="/tmp/street_screenshot.png"
          print(f"Saving {screenshot_file}")
          els[0].screenshot(screenshot_file)
          small_screenshot_filename=("small_screenshot_%04d.png" %(i,))
          small_screenshot_file=screenshotdir+'/'+small_screenshot_filename

          print(f"Converting to {small_screenshot_file}")
          ret=subprocess.call(['convert', '-resize', '192x192', screenshot_file, small_screenshot_file])
          if ret!=0:
            raise ValueError(f"Error code is {ret} (!=0), skipping")

        except Exception as err:
          print(f'Cant prepare a screenshot ({err}), skipping')
          small_screenshot_filename=None


        print(f"Adding name '{name}'\ndistrict '{district}'\nhouses '{houses}'")
        try:
          con.execute('''
            INSERT INTO Streets_GInfo(Name, Link, District, Houses, Screenshot, Version)
            VALUES                   (?,    ?,    ?,        ?,      ?,          ?)''',
                                     (name, url, district, houses, small_screenshot_filename, DBVER))
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



if __name__ == '__main__':
  scrap()

