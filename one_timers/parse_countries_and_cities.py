from bs4 import BeautifulSoup
import io
import csv
from db import mongo_db as db


def read_file(path, encoding="utf-8"):
    f = io.open(path, mode="r", encoding=encoding)
    text = f.read()
    f.close()
    return text


def get_soup(path):
    soup = BeautifulSoup(read_file(path), "html.parser")
    return soup


def country_table(tag):
    return tag.name == 'table' and tag.has_attr('class') and 'nix' in tag["class"]


# a country row has 3 cells of which the first contains a link
def country_row(tag):
    return tag.name == 'tr' and len(tag.find_all("td")) == 3 and tag.td.a


def get_eng_to_german_countries():
    eng_to_ger = {}
    soup = get_soup('/Users/roman/PycharmProjects/PersonalLifeCoach/static/countries_deu_eng.html')
    for table in soup.find_all(country_table):
        for row in table.find_all(country_row):
            eng_name = row.td.a.string
            ger_name = row.find_all("td")[1].string
            if eng_name and ger_name:
                eng_to_ger[eng_name] = ger_name
    return eng_to_ger


def country_codes_row(tag):
    return tag.name == 'tr' and len(tag.find_all("td")) == 5


def get_country_list():
    countries = []
    soup = get_soup('/Users/roman/PycharmProjects/PersonalLifeCoach/static/country_codes.html')
    for row in soup.table.find_all(country_codes_row):
        eng_name, alpha2_cd, alpha3_cd, un_cd = row.find_all("td")[1:]
        if eng_name.em:
            eng_name = eng_name.em.string
        elif eng_name.string:
            eng_name = eng_name.string
        elif eng_name.a:
            eng_name = eng_name.a.string
        if eng_name:
            countries.append({
                "eng_name": eng_name,
                "alpha2_cd": alpha2_cd.string,
                "alpha3_cd": alpha3_cd.string,
                "un_cd": un_cd.string,
            })
    return countries


def csv_row_to_dict(row):
    return {
        "country": row["Country"].upper(),
        "city": row["AccentCity"],
        "lat": row["Latitude"],
        "long": row["Longitude"]
    }


def insert_cities():
    f = io.open("/Users/roman/PycharmProjects/PersonalLifeCoach/static/all_cities.txt", mode="r", encoding="utf-8")
    csv_reader = csv.DictReader(f)
    for row in csv_reader:
        city = csv_row_to_dict(row)
        db.insert_city(city)
    f.close()

if __name__ == '__main__':
    eng_to_ger = get_eng_to_german_countries()
    print(eng_to_ger)
    country_list = get_country_list()

    for country in country_list:
        # add german name if existent
        if country["eng_name"] in eng_to_ger:
            country["ger_name"] = eng_to_ger[country["eng_name"]]
        db.insert_country(country)

    insert_cities()
