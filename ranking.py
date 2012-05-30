#!/usr/bin/python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from fetch_data import browse, parse_dof, clean_output, fix_encoding
from file_merger import read_rows
import csv
import sys

YEARS = ["-2009","-2010","-2011","-2012"]
SEARCH_URL = "https://data.fei.org/Ranking/Search.aspx?rankingCode=D_WR"

"""
1. Open results dataset
2. Fetch all riderid and horseid pairs
3. Merge to unique, save as file
4. For each pair
    1. Select year [2009-2012]
        * get period nrs
    2. Select period nr
    3. enter pair ids
    4. read results
"""

def parse_name(name):
    
    if len(name) > 0:
        
        parts = name.split(",")
        
        if len(parts) > 1:
    
            return {'first':parts[0].strip(), 'last':parts[1].strip()}
    
    return {'first':'', 'last': ''}

def parse_nr(title):
    divider_index = title.find("-")
    return title[3:(divider_index-1)]

def parse_date(title):
    
    from_date_index = title.find("from ")
    from_date = parse_dof(title[(from_date_index+len("from ")):(from_date_index+15)])
    #print from_date
    
    to_date_index = title.find("to ")
    to_date = parse_dof(title[(to_date_index+len("to ")):(to_date_index+15)])
    #print to_date
    
    return {'from':from_date, 'to': to_date}
    
def main(offset):
    
    #print "lets rank this shit"
    
    horse_rider = read_rows(['final/riderhorse.csv'])
    
    #print len(horse_rider)
    
    index = offset
    
    total = len(horse_rider)
    
    for i in range(index, total):
        entry = {'rider': horse_rider[i][0],'horse': horse_rider[i][1], 'years': []}
        for year in YEARS:
            entry['years'].append({'year': year, 'periods': search(year, horse_rider[i][0], horse_rider[i][1])})
        
        index += 1
        save(entry, "ranking/%d_rider_horse_%s_%s.csv" % (index, horse_rider[i][0], horse_rider[i][1]))
        print index

def save(data, filename):
    writer = csv.writer(open(filename, "wb"))
    
    header = ['Rider First Name', 'Rider Family Name', 'Horse Name', 'Rider ID', 'Horse ID']
    
    row = ['unknown', 'unknown', 'unknown', data['rider'], data['horse']]
    
    for year in data['years']:
        for period in year['periods']:
            header.append("Ranking no %s (%s/%s/%s to %s/%s/%s)" % (period['nr'], period['period']['from']['d'], period['period']['from']['m'],period['period']['from']['y'],period['period']['to']['d'], period['period']['to']['m'],period['period']['to']['y']))
            
            if len(period['results']) > 0:
                row[0] = fix_encoding(clean_output(period['results'][0]['rider_name']['first']))
                row[1] = fix_encoding(clean_output(period['results'][0]['rider_name']['last']))
                row[2] = fix_encoding(clean_output(period['results'][0]['horse_name']))
                row.append(period['results'][0]['rank'])
            else:
                row.append("0")
    
    writer.writerow(header)
    writer.writerow(row)

def search(year='-2012', rider='10000024', horse='NED42211'):
    
    br = browse(SEARCH_URL)
    
    br.select_form(nr=0)
    br.set_all_readonly(False) 
    
    # select the year
    br.form['ctl00$PlaceHolderMain$ddlSeason']=[year]
    
    br.find_control("ctl00$PlaceHolderMain$btnReset").disabled = True
    
    # when we submit, we get the periods
    try:
        br.submit()
    except urllib2.URLError as e:
        print e.reason
    
    # periods retreive
    soup = BeautifulSoup(br.response().read())
    
    select = soup.select('#PlaceHolderMain_ddlNumber')
    options = select[0].find_all('option')
    
    periods = []
    
    for option in options:
        if option['value'] != "-1":
            periods.append({'id': option['value'], 'title': option.contents[0], 'nr': parse_nr(option.contents[0]), 'period': parse_date(option.contents[0]), 'results':[]})
    
    # now for all periods, select drop, submit and search
    for period in periods:
        br.select_form(nr=0)
        br.set_all_readonly(False)
    
        br.form['ctl00$PlaceHolderMain$ddlNumber']=[period['id']]
        br.find_control("ctl00$PlaceHolderMain$btnReset").disabled = True
    
        br.submit()
    
        #
        
        br.select_form(nr=0)
        br.set_all_readonly(False)
    
        br.form['ctl00$PlaceHolderMain$txtCritCompetitorFEIID']=rider
        br.form['ctl00$PlaceHolderMain$txtCritHorseFEIID']=horse
        br.find_control("ctl00$PlaceHolderMain$btnReset").disabled = True
    
        br.submit(name="ctl00$PlaceHolderMain$btnSearch")
    
        soup =  BeautifulSoup(br.response().read())
    
        table = soup.find(id="PlaceHolderBottom_gvcResults")

        firstrows = table.select(".row")
        secondrows = table.select(".altrow")
    
        rows = firstrows + secondrows
        
        results = []
    
        for row in rows:
            
            results.append({'rank':row.contents[1].contents[0].strip(), 'previous': row.contents[2].contents[0].strip(), 'rider_name':parse_name(row.contents[3].contents[0].strip()),'rider_id':rider, 'horse_name':row.contents[4].contents[0].strip(), 'horse_id':horse, 'nf': row.contents[5].contents[0].strip(), 'points': row.contents[6].find('a').contents[0].strip()})
    
        period['results'] = results
    
    return periods

def fetch_pairs(file, output='final/riderhorse.csv'):
    rows = read_rows([file])
    # 32:rider, 33:horse
    merged = []
    for row in rows:
        merged.append({'rider':row[32],'horse':row[33]})
    unique = unique_pairs(merged)
    
    writer = csv.writer(open(output, "wb"))
    writer.writerow( ['Rider ID', 'Horse ID'] )
    
    writer.writerows(unique)
    
    print len(unique)

def unique_pairs(pairs):
    
    unique = []
    
    for i in range(0, len(pairs)):
        count = len(unique)
        match = False
        for j in range(0, count):
            if pairs[i]['rider'] == unique[j][0] and pairs[i]['horse'] == unique[j][1]:
                match = True
        if match == False:
            unique.append([pairs[i]['rider'], pairs[i]['horse']])
    
    return unique
    

if __name__ == "__main__":
    
    offset = 0
    
    if (len(sys.argv) > 1):
        if sys.argv[1].isdigit():
            offset = int(sys.argv[1])
    
    main(offset)