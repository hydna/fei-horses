from bs4 import BeautifulSoup
import mechanize
import os.path
import logging
import sys
from optparse import OptionParser

# 1. do search on dressage disipline
# 2. get number of page results
# 3. search with increment 'ctl00$PlaceHolderBottom$wcResult$gvcRes':'Page$8'
# 4. for each event find right competitions
# 5. find competitors and judges for each event
# 6. find gender of competitors and judges
# 7. output in cvs file

#def search():

START_URL = 'http://search.fei.org/Search_Centre/Result/Pages/Search.aspx?resultMode=true'
    

def fetch(url):
    
    br = mechanize.Browser()
    r = br.open(url)
    
    html = r.read()
    
    #print html
    
    #print br.title()
    
    #for f in br.forms():
    #    print f
    
    br.select_form(nr=0)
    
    br.form['ctl00$PlaceHolderMain$ddlCritDisciplines']=['2']
    
    br.submit()
    
    # get nr of result pages
    
    initialresp = br.response().read()
    
    soup = BeautifulSoup( initialresp )
    
    pagecount = int(soup.select(".pager")[0].contents[1].table.td.text.split(" ")[0])
    
    #print soup.select(".pager")[0].contents[1].table.td.text.split(" ")[5]
    
    print pagecount
    
    # get rows
    
    firstrows = soup.select(".row")
    secondrows = soup.select(".altrow")
    
    rows = firstrows + secondrows
    
    for row in rows:
        if row.contents[5].a:
            
            entry = {'city':row.contents[1].a['title'],'country':row.contents[2].contents[0],'link':row.contents[5].a['href']}
            
    #        print row.contents[1].a['title']
    #        print row.contents[2].contents[0]
    #        print row.contents[5].a['href']
    
    #for item in pager:
    #    print item.contents
    
    #print pager.contents
    
    #print table
    
    #print soup.title
    
    #br.select_form(name="aspnetForm")
    #br.set_value("2",name="ctl00$PlaceHolderMain$ddlCritDisciplines")
    #response = br.submit()
    
    #print br.form
    
    #print br.title
    
    print "Page$"+str(8)

def events( uri, count ):
    
    evts = []
    
    for i in range(1, count+1):
        evts += event( uri, i )
    
    return evts
    
def event( url, page ):
    
    # 3. search with increment 'ctl00$PlaceHolderBottom$wcResult$gvcRes':'Page$8'
    
    print 'fetching page %s' % (page)
    
    br = mechanize.Browser()
    
    r = br.open(url)
    
    html = r.read()
    
    br.select_form(nr=0)

    br.form['ctl00$PlaceHolderMain$ddlCritDisciplines']=['2']
    pageid = "Page$"+str(page)
    
    br.form.new_control('text', 'ctl00$PlaceHolderBottom$wcResult$gvcRes', {'value':''})
    br.form.fixup()
    br.form['ctl00$PlaceHolderBottom$wcResult$gvcRes']=pageid
    
    br.submit()
    
    resp = br.response().read()

    soup = BeautifulSoup( resp )
    
    firstrows = soup.select(".row")
    secondrows = soup.select(".altrow")
    
    rows = firstrows + secondrows
    
    results = []
    
    for row in rows:
        if row.contents[5].a:
            #print row.contents[1].a['title']
            #print row.contents[5].a['href']
            
            results.append({'title':row.contents[1].a['title'], 'url':row.contents[5].a['href']})
    
    
    return results

def pagecount(url):
    
    br = mechanize.Browser()
    
    br.open(url)
    
    br.select_form(nr=0)

    br.form['ctl00$PlaceHolderMain$ddlCritDisciplines']=['2']

    br.submit()

    # get nr of result pages

    initialresp = br.response().read()

    soup = BeautifulSoup( initialresp )

    #eventcount = int(soup.select(".pager")[0].contents[1].table.td.text.split(" ")[0])
    pagecount = int(soup.select(".pager")[0].contents[1].table.td.text.split(" ")[5])
    
    return pagecount
    
    
def competitions( url ):
    
    br = mechanize.Browser()
    
    r = br.open(url)
    
    html = r.read()
    
    soup = BeautifulSoup(html)
    
    firstrows = soup.select(".row")
    secondrows = soup.select(".altrow")
    
    rows = firstrows + secondrows
    
    for row in rows:
        #if row.contents[5].a:
        
        #title
        #print row.contents[3].span['title']
        #date
        #print row.contents[4].contents[0]
        if row.contents[7].a:
  
            javascript = row.contents[7].a['href'].split('"')
            print javascript[1] # so this is the postback
        #    print row.contents[7].a['href']
        #print row.contents[5].a['href']
            
    return None

def results( url, page ):
    
    logger = logging.getLogger("mechanize")
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.INFO)
    
    br = mechanize.Browser()
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    
    br.set_debug_redirects(True)
    br.set_handle_redirect(True)
    br.open(url)
    
    br.select_form(nr=0)
    br.set_all_readonly(False)
    
    br.form["__EVENTTARGET"]=page
    br.form["__EVENTARGUMENT"]=""
    
    br.find_control("ctl00$PlaceHolderMain$btnReset").disabled = True
    
    br.submit()

    # get result page

    initialresp = br.response().read()

    soup = BeautifulSoup( initialresp )
    
    print soup.title.contents[0].strip()
    
    ## get table row titles
    
    headers = []
    
    columns = soup.select(".headerr")
    
    for column in columns:
        name = column.contents[0].strip()
        if len(name) != 0:
            print name
    
    ## get judges
    
    #PlaceHolderMain_fvDetail_ucDressageJudges_panJudges
    
    judges = soup.find(id='PlaceHolderMain_fvDetail_ucDressageJudges_panJudges')
    
    tds = judges.find_all('td')
    
    for td in tds:
        print td
    
    #print judges.td
    
    
    ## get table results
    
    results = []
    
    firstrows = soup.select(".row")
    secondrows = soup.select(".altrow")
    
    rows = firstrows + secondrows
    
    for row in rows:
        
        print row.contents[1].a['title'] # position
        print row.contents[3].a.contents[0].strip() # competitor
        print row.contents[4].a.contents[0].strip() # horse 
        print row.contents[5].contents[0].strip() # prize money 
        
        print row.contents[7].contents[0].strip()
        print row.contents[8].contents[0].strip()
        print row.contents[9].contents[0].strip()
        print row.contents[10].contents[0].strip()
        #print row.contents[11].contents[0].strip()
        print row.contents[12].contents[0].strip()
    
    return None

def judgegender( url, judges ):
    return None

def ridergender( url, judges ):
    return None

def saveoutput( result, file ):
    
    
    return None

def main():
    
    #myevents = events( START_URL, pagecount(START_URL) )
    
    #print len(myevents)
    
    #mycompetitions = competitions( "http://search.fei.org/Search_Centre/Calendar/Pages/EventDetail.aspx?p=A7875F775FD231321FD325260B54B2EE" )
    
    #https://data.fei.org/Calendar/EventDetail.aspx?p=110BD1B7EAB6F342BA1E0ED0CD48D802
    mycompetitions = results( "https://data.fei.org/Calendar/EventDetail.aspx?p=110BD1B7EAB6F342BA1E0ED0CD48D802", "ctl00$PlaceHolderMain$gvCompetitions$ctl04$lbIndivResults" )
    
    #for evt in myevents:
    #    print evt.title
    
if __name__ == "__main__":
    main()
    