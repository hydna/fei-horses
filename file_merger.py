import csv

def read_rows(files):
    
    rows = []
    
    for f in files:
        reader = csv.reader(open(f, "rb"))
        
        firstline = True
        
        for row in reader:
            if firstline == False:
                rows.append(row)
            else:
                firstline = False
    
    return rows


def merge_files(files, filename, header):

    rows = read_rows(files)

    writer = csv.writer(open(filename, "wb"))
    writer.writerow( header )
    writer.writerows(rows)

def save_results(files, output="output/result_merged.csv"):
    
    merge_files( files, output, ['Event Venue', 'Event NF', 'Event Show Type', 'Event Discipline', 'Event Category', 'Event Starting Date', 'Event End Date', 'Event Indoor', 'Event code', 'Event Prize Money', 'Event Prize Money(CHF)', 'Competition Nr.', 'Competition Rule', 'Competition Name', 'Competition Date', 'Competition Prize Money','Competition Prize Money (CHF)', 'Judge Position', 'Judge First Name', 'Judge Family Name', 'Judge NF', 'Rider Final Position', 'Rider First Name', 'Rider Family Name', 'Rider NF', 'Horse Name', 'Rider Prize Money', 'Rider Prize Money (CHF)', 'Technical Score From Individual Judge', 'Artistic Score From Individual Judge', 'Final Score', 'Judge ID', 'Rider ID', 'Horse ID'] )


def save_riders(files, output="output/riders_merged.csv"):
    rows = read_rows(files)
    
    unique = uniquebyindex(rows, 0)
    
    writer = csv.writer(open(output, "wb"))
    writer.writerow( ['Rider ID', 'Rider Gender', 'Rider Family Name', 'Rider First Name', 'Rider Nationality', 'Rider Day of Birth', 'Rider Month of Birth', 'Rider Year of Birth', 'Rider Administering NF', 'Rider Competing For', 'Rider League'] )
    writer.writerows(unique)
    

def save_judges(files, output="output/judges_merged.csv"):
    
    rows = read_rows(files)
    
    unique = uniquebyindex(rows, 0)
    
    writer = csv.writer(open(output, "wb"))
    writer.writerow( ['Judge ID', 'Judge Gender','Judge Family Name', 'Judge First Name', 'Judge Nationality', 'Judge Day of Birth', 'Judge Month of Birth', 'Judge Year of Birth', 'Judge Administering NF' ] )
    
    writer.writerows(unique)

def uniquebyindex(items, index):
    unique = []
    for i in range(0, len(items)):
        count = len(unique)
        match = False
        for j in range(0, count):
            if items[i][index] == unique[j][index]:
                match = True

        if match == False:
            unique.append(items[i])

    return unique
    
def main():
    
    save_results(['output/results_0_10.csv', 'output/results_10_20.csv', 'output/results_20_30.csv', 'output/results_30_40.csv', 'output/results_40_50.csv','output/results_50_60.csv','output/results_60_70.csv','output/results_70_80.csv','output/results_80_90.csv','output/results_90_100.csv','output/results_100_110.csv','output/results_110_120.csv','output/results_120_130.csv','output/results_130_140.csv','output/results_140_150.csv','output/results_150_160.csv','output/results_160_170.csv','output/results_170_180.csv','output/results_180_190.csv','output/results_190_200.csv','output/results_200_210.csv','output/results_210_220.csv','output/results_220_230.csv','output/results_230_240.csv','output/results_240_250.csv','output/results_250_260.csv','output/results_260_270.csv','output/results_270_280.csv','output/results_280_290.csv','output/results_290_300.csv','output/results_300_301.csv','output/results_301_302.csv','output/results_302_303.csv','output/results_303_304.csv','output/results_304_305.csv','output/results_305_306.csv','output/results_306_316.csv','output/results_316_326.csv','output/results_326_336.csv','output/results_336_346.csv','output/results_346_356.csv','output/results_356_366.csv','output/results_366_376.csv','output/results_376_386.csv','output/results_386_396.csv','output/results_396_406.csv','output/results_406_416.csv','output/results_416_426.csv','output/results_426_436.csv','output/results_436_446.csv','output/results_446_456.csv','output/results_456_466.csv','output/results_466_476.csv','output/results_476_486.csv','output/results_486_496.csv','output/results_496_506.csv','output/results_506_516.csv','output/results_516_526.csv','output/results_526_536.csv','output/results_536_546.csv','output/results_546_556.csv','output/results_556_566.csv','output/results_566_576.csv','output/results_576_586.csv','output/results_586_587.csv'])
    
        save_judges(['output/judges.csv','output/judges_0_30.csv','output/judges_30_240-250.csv','output/judges_240_300.csv','output/judges_to_556.csv','output/judges_300_306.csv'])
    
    save_riders(['output/riders.csv','output/riders_0_30.csv','output/riders_240_300.csv','output/riders_30_240-250.csv','output/riders_300_306.csv','output/riders_to_516.csv'])
    
if __name__ == "__main__":
    main()
    