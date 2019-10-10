import re
import yaml
import sqlite3
import re
import os
import subprocess

from os import popen, mkdir
from time import sleep
from typing import Optional,Any
from textwrap import dedent

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

def print(out_filename, iterator):
  with open(out_filename,"w") as f:
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
    for i,(name,district,houses,link) in enumerate(iterator):
      f.write(dedent(f'''
        <tr style="display:table-row">
          <td>{i}</td>
          <td>район {district}</td>
          <td><a href='{link}'>{name}</a></td>
          <td>{houses}</td>
        </tr>
        '''))
    f.write(dedent('''
      </table>
      </body>
      </html>
      '''))
