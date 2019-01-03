#!/usr/bin/python3
from bs4 import BeautifulSoup
from dateutil.parser import parse
import requests
import math
import csv
import getpass
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class Lab:
    def __init__(self, name):
        self.name = name
        self.skip = []
    skip = []
    date = ''
    name = ''


def is_date(string):
    date = string.split('/')
    try:
        if int(date[0]) > 12 or int(date[0]) < 1:
            return False
        if int(date[1]) > 31 or int(date[1]) < 1:
            return False
        return True
    except IndexError:
        return False


def score_limit(score):
    score = float(score)
    if score > 100:
        score = 100
    elif score < 0:
        score = 0
    return score


# this function will need to be modified to suit the professors late policy
def check_date(lab, page_text):
    try:
        if lab.date:
            completed = page_text.partition('Time:')[2].split()[1]
            if parse(completed) > parse(lab.date):
                return 0
        return 1
    except Exception:
        return 1


def read_config():
    f = open('config', 'r')
    lines = []
    for line in f:
        if line.strip()[0] != '#':
            lines.append(line.strip('\n'))
    f.close()

    course = lines[0]
    lines.remove(course)
    students = []
    labs = []

    # seperate cNumbers from lab info
    for line in lines:
        if line and line.strip()[0] == 'c' and line.strip()[1].isdigit():
            students.append(line)
        elif line and line.strip()[0].isdigit and line[0] != '#':
            lab_number = line.split()[0]
            new_lab = Lab(lab_number)
            for l in line.split()[1:]:
                if is_date(l):
                    new_lab.date = l
                else:
                    new_lab.skip.append(l)
            labs.append(new_lab)
    return course, students, labs


def score_by_ex(lab, soup):
    ex_number = 1
    ex_scores = []
    table = soup.findAll('table')
    rows = table[1].findAll('tr')
    for row in rows:
        if str(ex_number) not in lab.skip:
            # this might be a little questionable!
            data = str(row).partition(
                'color')[2].partition('>')[2].split()
            num = data[0]
            possible = data[2].split('<')[0]
            # check for no attempt made
            if num[0] == '-':
                num = '0'
                possible = 100
            score = (float(num)*100)/float(possible)
            score = score_limit(score)
            ex_scores.append(score)
            # average all scores for the exercise
    return str(math.ceil(sum(ex_scores) / float(len(ex_scores))))


def score_by_total(soup):
    score = str(soup).partition(
                'Lab Grade: ')[2].partition('>')[2].split()[0]
    if score[0] == '-':
        score = '0'
    if int(score[0]) > 100:
        score = '100'
    return score


def main():
    course, students, labs = read_config()

    # open our gradebook file
    outfile = open('gradebook.csv', mode='w')
    gb_writer = csv.writer(
        outfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    gb_writer.writerow([''] + [l.name for l in labs])

    # chunks of url to scrape
    url_1 = 'http://cslabserver2.cs.mtsu.edu/admin/studentScores.php?userID='
    url_2 = '&lab='
    url_3 = '&course='

    # begin session
    sesh = requests.Session()
    user = input('Username: ')
    password = getpass.getpass(prompt='Password: ', stream=None)
    sesh.auth = (user, password)

    # loop through students and lab
    for cNum in students:
        lab_scores = []
        lab_scores.append(cNum)
        for lab in labs:
            response = sesh.get(
                url_1 + cNum + url_2 + lab.name + url_3 + course)
            soup = BeautifulSoup(response.text, features="lxml")
            penalty = check_date(lab, response.text)
            if lab.skip:
                score = score_by_ex(lab, soup)
            # no labs were skipped so just take the total from the page
            else:
                score = score_by_total(soup)
            # append the score for the lab
            lab_scores.append(str(float(score)*penalty))
        # need to check for higher score already in file and write the highest
        gb_writer.writerow(lab_scores)
    outfile.close()


main()
