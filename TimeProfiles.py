'''This module provides functions that handle time and date operations for 
GreaterQf, as well as a list of known public holidays during the period 2005-
2008. The functions contained in this module are as follows:
DayOfWeek - Determines day of the week, returns integer. 
WeekSatSun - Finds if day is a weekday, Saturday or Sunday, returns integer. 
DailyFact - Assigns factor based on day of the week, returns factor.
WhatYear - Finds year of a date, returns integer. 
WhatSeason - Finds season, returns integer.
DateDiff - Finds the difference in days between two dates.
'''
import datetime as dt 
from datetime import date as dtd
from datetime import timedelta
import numpy as np
#import f90nml

GLOBAL_HOLS = []
#WattHour\Day\Month: [0]Domestic Unrestricted elec [1]Domestic Economy 7 elec\
#[2]Industrial elec [3]Domestic gas [4]Industrial gas [5]Other industrial\
#[6]total domestic buildings [7]total industrial buildings [8]total buildings\
#[9]motorcycles [10]taxis [11]cars [12]buses [13]LGVs [14]HGV Rigid \
#[15] HGV artic [16]total transport [17] Metabolism\
#[18]Everything; [8]+[16]+[17]

def easterLookup(year):
    # Return easter bank holiday dates for a year
    # Hard coded because parliament didn't set a constant date
    # Easter Monday bank holidays
    easters = {}
    easters[2000] = [dtd(2000, 04, 24)]
    easters[2001] = [dtd(2001, 04, 16)]
    easters[2002] = [dtd(2002, 04, 1)]
    easters[2003] = [dtd(2003, 04, 21)]
    easters[2004] = [dtd(2004, 04, 12)]
    easters[2005] = [dtd(2005, 03, 28)]
    easters[2006] = [dtd(2006, 04, 17)]
    easters[2007] = [dtd(2007, 04, 9)]
    easters[2008] = [dtd(2008, 03, 24)]
    easters[2009] = [dtd(2009, 04, 13)]
    easters[2010] = [dtd(2010, 04, 05)]
    easters[2011] = [dtd(2011, 04, 25)]
    easters[2012] = [dtd(2012, 04, 9)]
    easters[2013] = [dtd(2013, 04, 01)]
    easters[2014] = [dtd(2014, 04, 21)]
    easters[2015] = [dtd(2015, 04, 06)]
    easters[2016] = [dtd(2016, 03, 28)]
    easters[2017] = [dtd(2017, 04, 17)]
    easters[2018] = [dtd(2018, 04, 02)]
    easters[2019] = [dtd(2019, 04, 22)]
    easters[2020] = [dtd(2020, 04, 13)]

    # Can programatically get Good Friday from the above
    for y in easters.keys():
        easters[y].append(easters[y][0] - timedelta(3))

    return easters[year]

def generateHolidays(firstYear, finalYear):
    # UK public holidays (fixed points or easily defined) between specified years (inclusive)
    years = range(firstYear, finalYear + 1, 1)
    allHolidays = []
    for y in years:
        allHolidays.extend(holidaysForYear(y))

    return allHolidays

def holidaysForYear(year):
    # Generate public holidays (UK) for a given year
    # Christmas day/boxing day falling on weekend isn't included (assumed standard weekend)
    holidays = []
    # New year:
    holidays.append(dtd(year, 01, 01))
    # If 2 or 3 january is a monday, this is the bank holiday
    jan2 = dtd(year, 01, 02)
    jan3 = dtd(year, 01, 03)
    if jan2.weekday() == 0:
        holidays.append(jan2)
    if jan3.weekday() == 0:
        holidays.append(jan3)

    # Get easter monday and friday bank holidays from lookup function
    holidays.extend(easterLookup(year))
    # Early and late may
    may1 = dtd(year, 05, 01)
    may1 = may1 if may1.weekday() is 0 else may1 + timedelta(7 - may1.weekday())
    holidays.append(may1)
    holidays.append(dtd(year, 5, 31) - timedelta(dtd(year, 5, 31).weekday()))
    # Final monday in August
    holidays.append(dtd(year, 8, 31) - timedelta(dtd(year, 8, 31).weekday()))
    # Christmas bank holidays. Only add if on a week, because weekends are weekends anyway
    dec25 = dtd(year, 12, 25)
    dec26 = dtd(year, 12, 26)
    if dec25.weekday() < 6:  # only include if not Sunday
        holidays.append(dec25)
    if dec26.weekday() < 6:
        holidays.append(dec26)

    # If december 28 is a monday or tuesday, it must be displaced bank holiday because xmas day and/or boxing day fell on weekend
    dec27 = dtd(year, 12, 27)
    dec28 = dtd(year, 12, 28)
    if dec28.weekday() < 2:
        holidays.append(dec28)
    if dec27.weekday() < 2:
        holidays.append(dec27)
    return holidays

def DayOfWeek(x, holidays):  #weekday:Mon=0, Sun=6. isoweekday:Mon=1,Sun=7
    '''Determines day of the week and assigns integer. Mon=0, Sun=6.
    Public holidays are considered as Sundays.Takes one arguments, x, a 
    datetime object.'''
    # Inputs: x (the date in question); holidays: List of dates that are public holidays and should be treated as Sundays
    dayofweek=dtd.weekday(x)
    if x in holidays:
        dayofweek=6#change this if using isoweekday
    return dayofweek
    
def WeekSatSun(x, holidays):
    '''Determines if a day is a weekday, Saturday or Sunday and assigns an
    integer to each: weekday=0, Saturday=1, Sunday=2. Takes one arguments, x, a 
    datetime object. 
    '''
    if DayOfWeek(x, holidays) < 5: # Weekday
        k=0
    elif DayOfWeek(x, holidays)==5: # Saturday
        k=1
    elif DayOfWeek(x, holidays)==6: # Sunday
        k=2
    return k

def DailyFact(x, holidays):    #for now just for buildings. Later change for metab and transport, change name
    if DayOfWeek(x, holidays)<=4:
        dailyfact=0.792
    elif DayOfWeek(x, holidays)==5:
        dailyfact=1.108
    elif DayOfWeek(x, holidays)==6:
        dailyfact=1.78
    return dailyfact
        
def WhatYear(x):
    '''Assigns a number depending on the year of a given datetime object x;
    2005,0; 2006,1; 2007,2;2008,3. 
    This function takes one argument:
    x: datetime object
    '''
    if x.year==2005:
        year=0
    elif x.year==2006:
        year=1
    elif x.year==2007:
        year=2
    elif x.year==2008:
        year=3
    return year
        
def WhatSeason(x):
    '''Assigns a number depending on the season of a given datetime object x;
    Winter(DJF), 0; Spring(MAM), 3; Summer(JJ), 6; High summer(Aug), 8;
    Autumn(SON), 12. These numbers correspond to season columns in EnergyHourly.
    This function takes one argument:
    x: datetime object
    '''  
    if x.month in [12,1,2]:
        season=0
    elif x.month in [3,4,5]:
        season=3
    elif x.month in [6,7]:
        season =6
    elif x.month==8:
        season=9
    elif x.month in [9,10,11]:
        season=12
    return season
 
def DateDiff(start, end):
    '''Finds the difference in days between two dates. 
    '''
    diff=(end-start).days
    return diff

