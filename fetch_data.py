from bs4 import BeautifulSoup
import mechanize
import os.path
import logging
import sys
from optparse import OptionParser
import re
import csv
import time
import urllib2
#time.sleep (.5); # sleep for .5 seconds

# 1. do search on dressage disipline
# 2. get number of page results
# 3. search with increment 'ctl00$PlaceHolderBottom$wcResult$gvcRes':'Page$X'
# 4. for each event find competitions
# 5. find competitors and judges for each event
# 6. find gender of competitors and judges
# 7. output in cvs file

SEARCH_URL = 'https://data.fei.org/Calendar/Search.aspx?resultMode=true'
JUDGE_URL = 'https://data.fei.org/Person/Search.aspx'
PERSON_URL = 'https://data.fei.org/Person/'

RIDERS = []
JUDGES = []

"""
events[title, country, urls, competitions[]]
    competitions[info, competitions[]]
        competitions[info, competitors[], judges[]]
            competitors[position, firstname, ...]
"""
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
            
            results.append({'title':row.contents[1].a['title'], 'country': country, 'urls': urls, 'competitions': [] })
    
    print "fetched -> %s on page %d" % ( url, page )
    
    return results

# APPROVED
def pagecount(url):
    
    response = search(url)
    
    soup = BeautifulSoup( response )
    
    # filter out the page count
    pagecount = int(soup.select(".pager")[0].contents[1].table.td.text.split(" ")[5])
    
    return pagecount
    
# APPROVED
def competitions( url ):
    
    br = browse(url)
    
    response = br.response().read()
    
    soup = BeautifulSoup(response)
    
    tds = soup.select(".entrycrit")[0].find_all("td")
    
    info = { 'venue': tds[1].contents[0].strip(), 'nf': tds[6].contents[0].strip(), 'type': tds[8].contents[0].strip(), 'discipline': tds[10].contents[0].strip(), 'category':tds[12].contents[0].strip(), 'start_date': tds[16].contents[0].strip(), 'end_date' : tds[16].contents[2].strip(), 'indoor': tds[18].contents[0].strip(), 'code': tds[20].contents[0].strip(), 'prize_money': clean_prize_money(tds[32].contents[0].strip()) }
    
    #for i in range(0, len(tds)):
    #    if len(tds[i].contents[0].strip()) > 0:
    #        print "%d - %s" % (i, tds[i].contents[0].strip())
    
    firstrows = soup.select(".row")
    secondrows = soup.select(".altrow")
    
    rows = firstrows + secondrows
    
    compresults = []
    
    for row in rows:
        
        links = row.contents[7].find_all('a')
        
        if len(links) > 0:
            
            javascript = row.contents[7].a['href'].split('"')
            
            compresults.append( { 'url': url, 'page': javascript[1], 'results': results( url, javascript[1] ) } )
            
    return { 'info': info, 'competitions': compresults }

def results( url, page ):
    
    br = browse(url)
    
    br.select_form(nr=0)
    br.set_all_readonly(False)
    
    br.form["__EVENTTARGET"]=page
    br.form["__EVENTARGUMENT"]=""
    
    br.find_control("ctl00$PlaceHolderMain$btnReset").disabled = True
    
    try:
        br.submit()
    except urllib2.URLError as e:
        print e.reason
    
    # get result page
    response = br.response().read()
    
    soup = BeautifulSoup( response )
    
    tds = soup.find(id="PlaceHolderMain_fvDetail_ucDressageJudges_panJudges").find_all("td")
    
    judgeoffset = 5
    judgestart = 1
    judgecount = len(tds) / judgeoffset
    
    judge_e = { 'firstname': '', 'lastname': '', 'country': '', 'position': '' }
    judge_h = { 'firstname': '', 'lastname': '', 'country': '', 'position': '' }
    judge_c = { 'firstname': '', 'lastname': '', 'country': '', 'position': '' }
    judge_m = { 'firstname': '', 'lastname': '', 'country': '', 'position': '' }
    judge_b = { 'firstname': '', 'lastname': '', 'country': '', 'position': '' }
    
    for i in range(0, judgecount):
        
        index = (i*judgeoffset)+1
        
        pos = parse_judge_position( tds[index].contents[0].strip() )
        
        currentjudge = judge_e;
        
        if pos == "E":
            currentjudge = judge_e
        if pos == "H":
            currentjudge = judge_h
        if pos == "C":
            currentjudge = judge_c
        if pos == "M":
            currentjudge = judge_m
        if pos == "B":
            currentjudge = judge_b
        
        currentjudge['position'] = pos
        currentjudge['firstname'] = tds[index+1].contents[0].strip()
        currentjudge['lastname'] = tds[index+2].contents[0].strip()
        currentjudge['country'] = parse_country(tds[index+3].contents[0].strip()) 
        currentjudge['details'] = search_judge(currentjudge['firstname'].encode("utf-8"), currentjudge['lastname'].encode("utf-8") )
        
        #print currentjudge['details']
    
    tds = soup.select(".entrycrit")[0].findAll("td")
    
    info = { 'competition_nr': tds[4].contents[0].strip(), 'rule': tds[6].contents[0].strip(), 'name': tds[8].contents[0].strip(), 'date': tds[10].contents[0].strip(), 'prize_money': clean_prize_money(tds[12].contents[0].strip()), 'judge_e': judge_e, 'judge_h': judge_h ,'judge_c': judge_c, 'judge_m': judge_m, 'judge_b': judge_b }
    
    #print info
    
    #print tds[18].contents[0].strip()
    
    #for i in range(0, len(tds)):
    #    if len(tds[i].contents[0].strip()) > 0:
    #        print "%d - %s" % (i, tds[i].contents[0].strip())
    
    # get table results
    
    #return
    
    competitors = []
    
    firstrows = soup.select(".row")
    secondrows = soup.select(".altrow")
    
    rows = firstrows + secondrows
    
    for row in rows:
        
        rider = parse_name(row.contents[3].a.contents[0].strip())
        
        rider_details = fetch_rider_details(row.contents[3].a['href'])
        
        # sometimes there is not several scores listed
        if len(row.contents) > 9:
            
            rowoffset = 0
            
            if len(row.contents) == 15:
                rowoffset = 1
            elif len(row.contents) == 14:
                rowoffset = 0
            else:
                print "UNKNOWN SIZE OF TABLE, PLEASE REVISE %s" % url
            
            e_score = parse_score(row.contents[6+rowoffset].contents)
            h_score = parse_score(row.contents[7+rowoffset].contents)
            c_score = parse_score(row.contents[8+rowoffset].contents)
            m_score = parse_score(row.contents[9+rowoffset].contents)
            b_score = parse_score(row.contents[10+rowoffset].contents)
                
            competitors.append({'position': row.contents[1].a['title'], 'firstname': rider['firstname'], 'lastname': rider['lastname'], 'country': rider['country'], 'horse': row.contents[4].a.contents[0].strip(), 'prize_money': clean_prize_money(row.contents[5].contents[0].strip()), 'judge_e_score': e_score['tech'], 'judge_e_tech': e_score['tech'], 'judge_e_art': e_score['art'], 'judge_h_score': h_score['tech'], 'judge_h_tech': h_score['tech'], 'judge_h_art': h_score['art'], 'judge_c_score': c_score['tech'], 'judge_c_tech': c_score['tech'], 'judge_c_art': c_score['art'],'judge_m_score': m_score['tech'], 'judge_m_tech': m_score['tech'], 'judge_m_art': m_score['art'], 'judge_b_score': b_score['tech'], 'judge_b_tech': b_score['tech'], 'judge_b_art': b_score['art'], 'score': b_score['tech'], 'rider': rider_details })
            
        else:
            competitors.append({'position': row.contents[1].a['title'], 'firstname': rider['firstname'], 'lastname': rider['lastname'], 'country': rider['country'], 'horse': row.contents[4].a.contents[0].strip(), 'prize_money': clean_prize_money(row.contents[5].contents[0].strip()), 'judge_e_score': '', 'judge_e_tech': '', 'judge_e_art': '', 'judge_h_score': '', 'judge_h_tech': '', 'judge_h_art': '', 'judge_c_score': '', 'judge_c_tech': '', 'judge_m_score': '', 'judge_m_tech': '', 'judge_m_art': '', 'judge_b_score': '', 'judge_b_tech': '', 'judge_b_art': '', 'score': row.contents[7].contents[0].strip(), 'rider': rider_details })
            
        #print "score %s " % row.contents[12].contents[0].strip()
        #print row.contents[7].contents[0].strip()
        
        #print competitors
    
    return { 'info': info, 'competitors': competitors }

# APPROVED
def clean_prize_money(prize):
    
    return prize.replace("\t", "").replace("\r\n", " ") 

# APPROVED
def parse_judge_position(judge):
    
    return judge[-1]
    

# APPROVED
def parse_name(name):
    
    parts = name.split(" ")
    
    return { 'firstname': parts[0], 'lastname': " ".join(parts[1:-1]), 'country': parse_country(parts[-1]) }

# APPROVED
def parse_judge_name(name):
    parts = name.split(", ")
    
    return {'firstname': parts[1], 'lastname': parts[0]}
    

# APPROVED
def parse_country(country):
    
    return country.replace("(", "").replace(")", "")

def parse_score(score):
    
    if len(score) > 1:
        return { 'tech': score[0].strip(), 'art': score[1].contents[0].strip() }
    
    return { 'tech': score[0].strip(), 'art': '' } 

def parse_dof(dof):
    
    parts = dof.split("/")
    
    return {'d': parts[0],'m': parts[1],'y': parts[2] }

def clean_output(data):
    
    return data.replace(",", "").replace("|", "")

def clean_row(row):
    
    for i in range(0,len(row)):
        row[i] = clean_output(row[i])
    
    return row
    
# APPROVED
def browse(url):
    
    br = mechanize.Browser()
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    
    br.set_debug_redirects(True)
    br.set_handle_redirect(True)
    
    try:
        br.open(url)
    except urllib2.URLError as e:
        print e.reason
        time.sleep (2);
        br.open(url)
        
    return br

def fetch_rider_details(url):
    
    br = browse(url)
    
    soup = BeautifulSoup(br.response().read())
    
    firstds = soup.find(id='PlaceHolderMain_fvDetail_panMain').select(".formleft")[0].find_all("td")
    
    details = { 'id': firstds[1].contents[0].strip(), 'gender': firstds[3].contents[0].strip(), 'lastname': firstds[7].input['title'], 'firstname': firstds[9].input['title'], 'nationality': firstds[13].contents[0].strip(), 'dof': {'d': '', 'm': '', 'y': ''}, 'nf': '', 'competingfor': '', 'league': '' }
    
    secondtds = soup.find(id='PlaceHolderMain_fvDetail_panMain').select(".formright")[0].find_all("td")
    
    details['dof'] = parse_dof(secondtds[3].contents[0].strip())
    
    details['nf'] = secondtds[12].div.contents[0].strip()
    details['competingfor'] = soup.find(id='PlaceHolderMain_fvDetail_panCompetitor').select(".formleft")[0].find_all("td")[1].contents[0].strip()
    details['league'] = soup.find(id='PlaceHolderMain_fvDetail_gvLeagues').find_all("td")[0].contents[0].strip()
    
    print details
    
    RIDERS.append(details)
    
    return details

# APPROVED
def fetch_judge_details( url ):
    
    br = browse(url)
    
    response = br.response().read()
    
    soup = BeautifulSoup(response)
    
    firstds = soup.find(id='PlaceHolderMain_fvDetail_panMain').findAll('td')
    
    #for i in range(0, len(firstds)):
    #    print "%d - %s" % (i,firstds[i] )
        
    dof = parse_dof( firstds[17].contents[0].strip() )
    
    details = {'id': firstds[1].contents[0].strip(), 'gender': firstds[3].contents[0].strip(), 'lastname': firstds[7].input['title'], 'firstname': firstds[9].input['title'], 'nationality': firstds[13].contents[0].strip(), 'dof': dof, 'nf': firstds[26].div.contents[0].strip() }
    
    JUDGES.append(details)
    
    return details
    

def search_judge(firstname, lastname):
    
    br = browse(JUDGE_URL)
    
    br.select_form(nr=0)
    br.set_all_readonly(False) 
    
    # select the right group 'Officials'
    br.form['ctl00$PlaceHolderMain$ddlCritPersonGroups']=['4']
    
    br.find_control("ctl00$PlaceHolderMain$btnReset").disabled = True

    br.submit()
    
    br.select_form(nr=0)
    br.set_all_readonly(False) 
    
    # select the right rider category 'Senior Rider'
    br.form['ctl00$PlaceHolderMain$ddlCritFunctions'] =['3']
    br.form['ctl00$PlaceHolderMain$txtCritName'] = lastname;
    br.find_control("ctl00$PlaceHolderMain$btnReset").disabled = True
    
    # simulate search click
    br.submit(name="ctl00$PlaceHolderMain$btnSearch") 
    
    response = br.response().read()
    
    soup = BeautifulSoup(response)
    
    firstrows = soup.select(".row")
    secondrows = soup.select(".altrow")
    
    rows = firstrows + secondrows
    
    for row in rows:
        option = parse_judge_name(row.a['title'])
        if option['firstname'].encode('utf-8') == firstname:
            option['id'] = row.span.contents[0];
            
            return fetch_judge_details("%s%s" % (PERSON_URL,row.a['href']))
    
    return {'id': '', 'gender': '', 'lastname': lastname, 'firstname': firstname, 'nationality': '', 'dof': '', 'nf': '' }

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
    
    # simulate search click
    br.submit(name="ctl00$PlaceHolderMain$btnSearch")
    
    # if we need to offset search results, add that option
    if offset > 0:
        
        pageid = "Page$"+str(offset)
        
        br.select_form(nr=0)
        br.set_all_readonly(False)
        
        br.find_control("ctl00$PlaceHolderMain$btnReset").disabled = True   
        
        br.form["__EVENTTARGET"]='ctl00$PlaceHolderBottom$wcResult$gvcRes'
        br.form["__EVENTARGUMENT"]=pageid
        
        br.submit()
    
    response = br.response().read()
    
    return response

def judgegender( url, judges ):
    return None

def ridergender( url, judges ):
    return None

def saveresults( myevents, file='output/results.csv' ):
    
    writer = csv.writer(open(file, 'wb'), delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['Event Venue', 'Event NF', 'Event Show Type', 'Event Discipline', 'Event Category', 'Event Starting Date', 'Event End Date', 'Event Indoor', 'Event code', 'Event Prize Money', 'Event Prize Money(CHF)', 'Competition Nr.', 'Competition Rule', 'Competition Name', 'Competition Date', 'Competition Prize Money','Competition Prize Money (CHF)', 'Judge Position', 'Judge First Name', 'Judge Family Name', 'Judge NF', 'Rider Final Position', 'Rider First Name', 'Rider Family Name', 'Rider NF', 'Horse Name', 'Rider Prize Money', 'Rider Prize Money (CHF)', 'Technical Score From Individual Judge', 'Artistic Score From Individual Judge', 'Final Score', 'Judge ID', 'Rider ID'])
    
    
    for evt in myevents:
        print evt['title'].encode('utf-8')
        
        for complist in evt['competitions']:
            # here we have info on event
            #print complist['info']
            
            for comp in complist['competitions']:
                
                # here competition info
                #print comp['results']['info']
                
                for rider in comp['results']['competitors']:
                    
                    
                    #Event Venue', 'Event NF', 'Event Show Type', 'Event Discipline', 'Event Category', 'Event Starting Date', 'Event End Date', 'Event Indoor', 'Event code', 'Event Prize Money', 'Event Prize Money(CHF)', 'Competition Nr.', 'Competition Rule', 'Competition Name', 'Competition Date', 'Competition Prize Money','Competition Prize Money (CHF)', 'Judge Position', 'Judge First Name', 'Judge Family Name', 'Judge NF', 'Rider Final Position', 'Rider First Name', 'Rider Family Name', 'Rider NF', 'Horse Name', 'Rider Prize Money', 'Rider Prize Money (CHF)', 'Technical Score From Individual Judge', 'Artistic Score From Individual Judge', 'Final Score', 'Judge ID', 'Rider ID'
                    
                    #info = { 'venue': tds[1].contents[0].strip(), 'nf': tds[6].contents[0].strip(), 'type': tds[8].contents[0].strip(), 'discipline': tds[10].contents[0].strip(), 'category':tds[12].contents[0].strip(), 'start_date': tds[16].contents[0].strip(), 'end_date' : tds[16].contents[2].strip(), 'indoor': tds[18].contents[0].strip(), 'code': tds[20].contents[0].strip(), 'prize_money': tds[32].contents[0].strip() }
                    
                    #info = { 'competition_nr': tds[4].contents[0].strip(), 'rule': tds[6].contents[0].strip(), 'name': tds[8].contents[0].strip(), 'date': tds[10].contents[0].strip(), 'prize_money': clean_prize_money(tds[12].contents[0].strip()), 'judge_e': judge_e, 'judge_h': judge_h ,'judge_c': judge_c, 'judge_m': judge_m, 'judge_b': judge_b }     
                    
                    compinfo = [complist['info']['venue'].encode('utf-8'), complist['info']['nf'], complist['info']['type'], complist['info']['discipline'], complist['info']['category'], complist['info']['start_date'], complist['info']['end_date'], complist['info']['indoor'], complist['info']['code'], complist['info']['prize_money'], complist['info']['prize_money'], comp['results']['info']['competition_nr'], comp['results']['info']['rule'], comp['results']['info']['name'], comp['results']['info']['date'], comp['results']['info']['prize_money'], comp['results']['info']['prize_money'] ]
                    
                    # for each judge, output a line with score
                    
                    judge_e = compinfo + [ comp['results']['info']['judge_e']['position'], comp['results']['info']['judge_e']['firstname'].encode('utf-8'), comp['results']['info']['judge_e']['lastname'].encode('utf-8'), comp['results']['info']['judge_e']['details']['nf'], rider['position'], rider['firstname'].encode('utf-8'), rider['lastname'].encode('utf-8'), rider['rider']['nf'], rider['horse'].encode('utf-8'), rider['prize_money'], rider['prize_money'], rider['judge_e_tech'], rider['judge_e_art'], rider['score'], comp['results']['info']['judge_e']['details']['id'], rider['rider']['id'] ]
                    
                    judge_h = compinfo + [ comp['results']['info']['judge_h']['position'], comp['results']['info']['judge_h']['firstname'].encode('utf-8'), comp['results']['info']['judge_h']['lastname'].encode('utf-8'), comp['results']['info']['judge_h']['details']['nf'], rider['position'], rider['firstname'].encode('utf-8'), rider['lastname'].encode('utf-8'), rider['rider']['nf'], rider['horse'].encode('utf-8'), rider['prize_money'], rider['prize_money'], rider['judge_h_tech'], rider['judge_h_art'], rider['score'], comp['results']['info']['judge_h']['details']['id'], rider['rider']['id'] ]
                    
                    judge_c = compinfo + [ comp['results']['info']['judge_c']['position'], comp['results']['info']['judge_c']['firstname'].encode('utf-8'), comp['results']['info']['judge_c']['lastname'].encode('utf-8'), comp['results']['info']['judge_c']['details']['nf'], rider['position'], rider['firstname'].encode('utf-8'), rider['lastname'].encode('utf-8'), rider['rider']['nf'], rider['horse'].encode('utf-8'), rider['prize_money'], rider['prize_money'], rider['judge_c_tech'], rider['judge_c_art'], rider['score'], comp['results']['info']['judge_c']['details']['id'], rider['rider']['id'] ]
                    
                    judge_m = compinfo + [ comp['results']['info']['judge_m']['position'], comp['results']['info']['judge_m']['firstname'].encode('utf-8'), comp['results']['info']['judge_m']['lastname'].encode('utf-8'), comp['results']['info']['judge_m']['details']['nf'], rider['position'], rider['firstname'].encode('utf-8'), rider['lastname'].encode('utf-8'), rider['rider']['nf'], rider['horse'].encode('utf-8'), rider['prize_money'], rider['prize_money'], rider['judge_m_tech'], rider['judge_m_art'], rider['score'], comp['results']['info']['judge_m']['details']['id'], rider['rider']['id'] ] 
                    
                    judge_b = compinfo + [ comp['results']['info']['judge_b']['position'], comp['results']['info']['judge_b']['firstname'].encode('utf-8'), comp['results']['info']['judge_b']['lastname'].encode('utf-8'), comp['results']['info']['judge_b']['details']['nf'], rider['position'], rider['firstname'].encode('utf-8'), rider['lastname'].encode('utf-8'), rider['rider']['nf'], rider['horse'].encode('utf-8'), rider['prize_money'], rider['prize_money'], rider['judge_b_tech'], rider['judge_b_art'], rider['score'], comp['results']['info']['judge_b']['details']['id'], rider['rider']['id'] ]
                    
                    writer.writerow( clean_row(judge_e) )
                    writer.writerow( clean_row(judge_h) )
                    writer.writerow( clean_row(judge_c) )
                    writer.writerow( clean_row(judge_m) )
                    writer.writerow( clean_row(judge_b) )

def savejudges( file='output/judges.csv' ):

    writer = csv.writer(open(file, 'wb'), delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['Judge ID', 'Judge Gender','Judge Family Name', 'Judge First Name', 'Judge Nationality', 'Judge Day of Birth', 'Judge Month of Birth', 'Judge Year of Birth', 'Judge Administering NF' ])
    
    unique = uniquebyid(JUDGES)
    
    for judge in unique:
       writer.writerow(clean_row([ judge['id'], judge['gender'], judge['lastname'], judge['firstname'], judge['nationality'], judge['dof']['d'], judge['dof']['m'], judge['dof']['y'], judge['nf'] ])) 

def saveriders( file='output/riders.csv' ):
    
    writer = csv.writer(open(file, 'wb'), delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['Rider ID', 'Rider Gender', 'Rider Family Name', 'Rider First Name', 'Rider Nationality', 'Rider Day of Birth', 'Rider Month of Birth', 'Rider Year of Birth', 'Rider Administering NF', 'Rider Competing For', 'Rider League'])
    
    unique = uniquebyid(RIDERS)
    
    for rider in unique:
        writer.writerow(clean_row([rider['id'], rider['gender'], rider['lastname'].encode('utf-8'), rider['firstname'].encode('utf-8'), rider['nationality'], rider['dof']['d'], rider['dof']['m'], rider['dof']['y'], rider['nf'], rider['competingfor'], rider['league'] ]))

def uniquebyid(items):
    unique = []
    for i in range(0, len(items)):
        count = len(unique)
        match = False
        for j in range(0, count):
            if items[i]['id'] == unique[j]['id']:
                match = True
        
        if match == False:
            unique.append(items[i])
    
    return unique
        
def fetchall(url):
    
    count = pagecount(SEARCH_URL)
    
    myevents = events(SEARCH_URL, 1)
    
    print "fetched -> %d events" % len(myevents)
    
    for i in range(0, len(myevents)):
       print myevents[i]['title'].encode('utf-8')
       
       for pageurl in myevents[i]['urls']:
           myevents[i]['competitions'].append( competitions( pageurl['url'] ) )
    
    return myevents

def main():
    
    myevents = fetchall(SEARCH_URL)
    
    saveresults(myevents)
    
    #comps = competitions('https://data.fei.org/Calendar/EventDetail.aspx?p=A37A41ABD93704BE0C58F4E6F1F4F3C2')
    #comps = competitions('https://data.fei.org/Calendar/EventDetail.aspx?p=21E1D66E5EAF3EFA6C8A9438A68DDBF6')
    #comps = competitions('https://data.fei.org/Calendar/EventDetail.aspx?p=80979162F60932B56985630881496C43')
    #https://data.fei.org/Calendar/EventDetail.aspx?p=A37A41ABD93704BE0C58F4E6F1F4F3C2
    
    #https://data.fei.org/Result/ResultList.aspx?p=FD61305C26C56C44D057820205C56F91398B97560726BEDF84FB277F5BB21799
    
    #details = fetch_rider_details('https://data.fei.org/Person/Detail.aspx?p=A77A9DEDEC6686C3865DF12347853E2E')         
    
    saveriders()
    savejudges()
    
    print '\a'
    
if __name__ == "__main__":
    main()
    