from bs4 import BeautifulSoup
import mechanize
import os.path
import logging
import sys
from optparse import OptionParser
import re
import csv

# 1. do search on dressage disipline
# 2. get number of page results
# 3. search with increment 'ctl00$PlaceHolderBottom$wcResult$gvcRes':'Page$X'
# 4. for each event find competitions
# 5. find competitors and judges for each event
# 6. find gender of competitors and judges
# 7. output in cvs file

SEARCH_URL = 'https://data.fei.org/Calendar/Search.aspx?resultMode=true'

# APPROVED
def events( uri, count ):
    
    evts = []
    
    for i in range(1, count+1):
        evts += event( uri, i )
    
    return evts

# APPROVED
def event( url, page ):
    
    response = search(url, page)
    
    soup = BeautifulSoup( response )
    
    firstrows = soup.select(".row")
    secondrows = soup.select(".altrow")
    
    rows = firstrows + secondrows
    
    results = []
    
    for row in rows:
        
        # check if there is any links for this event
        links = row.contents[5].find_all('a')
        country = row.contents[2].contents[0]
        
        if len(links) > 0:
            
            urls = []
            
            for link in links:
                 urls.append({'title':link.contents[0].strip(), 'url':link['href']} )
            
            results.append({'title':row.contents[1].a['title'], 'country': country, 'urls': urls })
    
    print "fetched -> %s on page %d" % ( url, page )
    
    return results

def pagecount(url):
    
    response = search(url)
    
    soup = BeautifulSoup( response )
    
    # filter out the page count
    pagecount = int(soup.select(".pager")[0].contents[1].table.td.text.split(" ")[0])
    
    return pagecount
    
# TODO
def competitions( url ):
    
    br = browse(url)
    
    response = br.response().read()
    
    soup = BeautifulSoup(response)
    
    tds = soup.select(".entrycrit")[0].find_all("td")
    
    info = { 'venue': tds[1].contents[0].strip(), 'nf': tds[6].contents[0].strip(), 'type': tds[8].contents[0].strip(), 'discipline': tds[10].contents[0].strip(), 'category':tds[12].contents[0].strip(), 'start_date': tds[16].contents[0].strip(), 'end_date' : tds[16].contents[2].strip(), 'indoor': tds[18].contents[0].strip(), 'code': tds[20].contents[0].strip(), 'prize_money': tds[32].contents[0].strip() }
    
    #print info
    
    #for i in range(0, len(tds)):
    #    if len(tds[i].contents[0].strip()) > 0:
    #        print "%d - %s" % (i, tds[i].contents[0].strip())
    
    firstrows = soup.select(".row")
    secondrows = soup.select(".altrow")
    
    rows = firstrows + secondrows
    
    results = []
    
    for row in rows:
        
        links = row.contents[7].find_all('a')
        
        if len(links) > 0:
            
            javascript = row.contents[7].a['href'].split('"')
            
            results.append( { 'url': url, 'page': javascript[1] } )
            
    return { 'info': info, 'competitions': results }

def results( url, page ):
    
    br = browse(url)
    
    br.select_form(nr=0)
    br.set_all_readonly(False)
    
    br.form["__EVENTTARGET"]=page
    br.form["__EVENTARGUMENT"]=""
    
    br.find_control("ctl00$PlaceHolderMain$btnReset").disabled = True
    
    br.submit()
    
    # get result page
    response = br.response().read()
    
    soup = BeautifulSoup( response )
    
    tds = soup.select(".entrycrit")[0].find_all("td")
    
    judge_e = { 'firstname': tds[17].contents[0].strip(), 'lastname': tds[18].contents[0].strip(), 'country': parse_country(tds[19].contents[0].strip()) }
    judge_h = { 'firstname': tds[22].contents[0].strip(), 'lastname': tds[23].contents[0].strip(), 'country': parse_country(tds[24].contents[0].strip()) }
    judge_c = { 'firstname': tds[27].contents[0].strip(), 'lastname': tds[28].contents[0].strip(), 'country': parse_country(tds[29].contents[0].strip()) }
    judge_m = { 'firstname': tds[32].contents[0].strip(), 'lastname': tds[33].contents[0].strip(), 'country': parse_country(tds[34].contents[0].strip()) }
    judge_b = { 'firstname': tds[37].contents[0].strip(), 'lastname': tds[38].contents[0].strip(), 'country': parse_country(tds[39].contents[0].strip()) }
    
    info = { 'competition_nr': tds[4].contents[0].strip(), 'rule': tds[6].contents[0].strip(), 'name': tds[8].contents[0].strip(), 'date': tds[10].contents[0].strip(), 'prize_money': tds[12].contents[0].strip(), 'judge_e': judge_e, 'judge_h': judge_h ,'judge_c': judge_c, 'judge_m': judge_m, 'judge_b': judge_b }
    
    print info
    
    #print tds[18].contents[0].strip()
    
    #for i in range(0, len(tds)):
    #    if len(tds[i].contents[0].strip()) > 0:
    #        print "%d - %s" % (i, tds[i].contents[0].strip())
    
    # get table results
    
    competitors = []
    
    firstrows = soup.select(".row")
    secondrows = soup.select(".altrow")
    
    rows = firstrows + secondrows
    
    for row in rows:
        
        #print row.contents[1].a['title'] # position
        #print row.contents[3].a.contents[0].strip().encode('utf-8')  # competitor
        
        rider = parse_name(row.contents[3].a.contents[0].strip())
        
        #print row.contents[4].a.contents[0].strip() # horse 
        #print row.contents[5].contents[0].strip() # prize money 
        #print row.contents[6].contents[0].strip() # judge e 
        #print row.contents[7].contents[0].strip() # judge h
        #print row.contents[8].contents[0].strip() # judge c
        #print row.contents[9].contents[0].strip() # judge m
        #print row.contents[10].contents[0].strip() # judge b
        #print row.contents[11].contents[0].strip()
        #print row.contents[12].contents[0].strip() # score
        
        competitors.append({'position': row.contents[1].a['title'], 'firstname': rider['firstname'], 'lastname': rider['lastname'], 'country': rider['country'], 'horse': row.contents[4].a.contents[0].strip(), 'prize_money': row.contents[5].contents[0].strip(), 'judge_e_score': row.contents[6].contents[0].strip(), 'judge_e_tech': row.contents[6].contents[0].strip(), 'judge_e_art': row.contents[6].contents[0].strip(), 'judge_h_score': row.contents[7].contents[0].strip(), 'judge_h_tech': row.contents[7].contents[0].strip(), 'judge_h_art': row.contents[7].contents[0].strip(), 'judge_c_score': row.contents[8].contents[0].strip(), 'judge_c_tech': row.contents[8].contents[0].strip(), 'judge_m_score': row.contents[9].contents[0].strip(), 'judge_m_tech': row.contents[9].contents[0].strip(), 'judge_m_art': row.contents[9].contents[0].strip(), 'judge_b_score': row.contents[10].contents[0].strip(), 'judge_b_tech': row.contents[10].contents[0].strip(), 'judge_b_art': row.contents[10].contents[0].strip(), 'score': row.contents[12].contents[0].strip() })
        
        #print competitors
    
    
    return { 'info': info, 'competitors': competitors }

# APPROVED
def parse_name(name):
    
    parts = name.split(" ")
    
    return { 'firstname': parts[0], 'lastname': " ".join(parts[1:-1]), 'country': parse_country(parts[-1]) }

# APPROVED
def parse_country(country):
    
    return country.replace("(", "").replace(")", "")

# APPROVED
def browse(url):
    
    br = mechanize.Browser()
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    
    br.set_debug_redirects(True)
    br.set_handle_redirect(True)
    br.open(url, "rt")
    
    return br

# APPROVED
def search(url, offset=0):
    
    br = browse(url)
    
    br.select_form(nr=0)
    br.set_all_readonly(False) 
    
    # select the right discipline select box 'Dressage'
    br.form['ctl00$PlaceHolderMain$ddlCritDisciplines']=['2']
    
    br.find_control("ctl00$PlaceHolderMain$btnReset").disabled = True

    br.submit()
    
    br.select_form(nr=0)
    br.set_all_readonly(False) 
    
    # select the right rider category 'Senior Rider'
    br.form['ctl00$PlaceHolderMain$ddlCritCategories'] =['1'] 
    br.find_control("ctl00$PlaceHolderMain$btnReset").disabled = True
    
    
        
    #    br.submit()
    #else:
        # simulate search click
    br.submit(name="ctl00$PlaceHolderMain$btnSearch")
    
    # if we need to offset search results, add that option
    if offset > 0:
        pageid = "Page$"+str(offset)
        
        br.select_form(nr=0)
        br.set_all_readonly(False)
    
        br.form.new_control('text', 'ctl00$PlaceHolderBottom$wcResult$gvcRes', {'value':''})
        br.form.fixup()
        br.form['ctl00$PlaceHolderBottom$wcResult$gvcRes']=pageid
        
        br.submit()
    
    response = br.response().read()
    
    return response

def judgegender( url, judges ):
    return None

def ridergender( url, judges ):
    return None

def saveresult( result, file='test.csv' ):
    
    writer = csv.writer(open(file, 'wb'), delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['Spam', 'Lovely Spam', 'Wonderful Spam'])
    
    return None

def main():
    
    count = pagecount(SEARCH_URL)
    
    myevent = event(SEARCH_URL, 2)
    
    for evt in myevent:
        print evt['title'].encode('utf-8')
    
    #print myevent[0]['urls'][0]['url']
    
    #mycomps = competitions(myevent[0]['urls'][0]['url'])
    
    #print mycomps['info']
    
    #mycomps = competitions("https://data.fei.org/Calendar/EventDetail.aspx?p=6FABEE84DFB9A49A89CC21BD08A37D0C")
    
    #results(mycomps['competitions'][0]['url'], mycomps['competitions'][0]['page'])
    
   #for comp in mycomps:
   #     print "%s - %s" % (comp['url'], comp['page'])
   #     results()
    
if __name__ == "__main__":
    main()
    