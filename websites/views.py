from django.shortcuts import render, redirect
from .models import *
from .forms import *
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
import re
import time
import pprint

# Fix bugs, get the rows to be searched by word for just the description not everything like the address
# fix data

# Create your views here.
def home(request):
    return render(request, 'index.html', {})

def test(request):
	if request.method == 'POST':
		datesdict = request.POST.dict()
		startdate = datesdict['startdate']
		enddate = datesdict['enddate']
       
		list = scraper(startdate, enddate)

	context = {
		'list': list,
	}
		

	return render(request, 'test.html', context)


def richmond(request):
    words = Word.objects.all()
    form = WordForm()
    dateform = DateForm()

    if request.method == 'POST':
        print(request.POST)
        form = WordForm(request.POST or None)
        if form.is_valid():
            print(form)
            form.save()
        return redirect('richmond')

    context = {
        'form': form,
        'words': words,
        'dateform': dateform,
    }
    return render(request, 'richmond.html', context)


def get_word_objects():
	words = Word.objects.values_list('word', flat=True)
	objectlist = list(words)

	return objectlist


def convert(s):
 
    # initialization of string to ""
    new = ""
 
    # traverse in the string
    for x in s:
        new = new + x + '|'
 
    # return string
    return new


row_list = []
address_list = []
name_list = []
data = []

def format_address(addresss):
    formatted_address = addresss.replace('\n', ' ')
    address_list.append(formatted_address)


def scraper(startdate, enddate):
   
    wordlist = ['rear']
    words = convert(wordlist)
    words_search_for = words.rstrip(words[-1])


    # Set up the WebDriver (you may need to provide the path to your chromedriver executable)
    driver = webdriver.Chrome()

    url = 'https://www2.richmond.gov.uk/lbrplanning/Planning_Report.aspx'
    driver.get(url)

    # alldates = pd.date_range(start=f"{startdate}", end=f"{enddate}").strftime("%Y-%m-%d")
    # print(alldates)
    # alldateslist = list(alldates)
    print(startdate)[::-1]
    print(enddate)[::-1]
    print(enddate[::-1])



    # Input start and end dates
    input_element1 = driver.find_element(By.ID, 'ctl00_PageContent_dpValFrom')
    input_element2 = driver.find_element(By.ID, 'ctl00_PageContent_dpValTo')
    input_element1.send_keys('01/01/2024')
    input_element2.send_keys('02/01/2024')
    # Click the search button
    search_element = driver.find_element(By.CLASS_NAME, 'btn-primary')


    # Wait for the cookie consent popup to appear
    wait = WebDriverWait(driver, 10)
    cookie_popup = wait.until(EC.presence_of_element_located((By.ID, 'ccc-end')))

    # Locate and click the "Accept" button
    accept_button = cookie_popup.find_element(By.ID, 'ccc-dismiss-button')
    accept_button.click()

    # Select 500 to show max results
    num_results_element = Select(driver.find_element(By.ID, 'ctl00_PageContent_ddLimit'))
    num_results_element.select_by_visible_text('500')

    # Click submit for advanced results page
    search_element.click()

    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'infocontent')))


    # Get the page source after the search
    page_source = driver.page_source

    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')


    span_div = driver.find_element(By.ID, 'ctl00_PageContent_lbl_APPS')
    num_results = span_div.find_element(By.TAG_NAME, 'strong')

    if (int(num_results.text) == 500):
        print('Results over 500 please alter your search results')
        driver.quit()
    else:
        print('Number of results for this search is: ' + num_results.text)


    searchResultsPage = soup.find('ul', class_='planning-apps')
    searchResults = searchResultsPage.find_all('li')

    for row in searchResults:

        if (re.search(words_search_for, row.text, flags=re.I)):
            row_list.append(row)

    
    for row in row_list:

        # Find the address and add to address_list
        address_div = row.find('h3')
        address = address_div.text.strip()
        format_address(address)
        
        a_tag = row.find('a')
        link_text = a_tag.get_text(strip=True)
        element = driver.find_element(By.LINK_TEXT, link_text)

        element.click()
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.ID, 'ctl00_PageContent_btnShowApplicantDetails')))

        subtab = driver.find_element(By.ID, 'ctl00_PageContent_btnShowApplicantDetails')
        subtab.click()

        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.ID, 'ctl00_PageContent_lbl_Applic_Name')))
        name_page_source = driver.page_source
        name_soup = BeautifulSoup(name_page_source, 'html.parser')


        name = name_soup.find('span', id='ctl00_PageContent_lbl_Applic_Name')
        
        name_list.append(name.text.strip())
        driver.back()
        driver.back()


    merge_data = zip(name_list, address_list)

    for item in merge_data:
        data.append(item)

    print(data)

    # Close the browser window
    driver.quit()
    return data
