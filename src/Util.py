from os import popen

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, StaleElementReferenceException
from pyvirtualdisplay import Display as PYDisplay
from contextlib import contextmanager

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


def class_has(cls:str)->str:
  return f"contains(concat(' ',normalize-space(@class),' '),' {cls} ')"


