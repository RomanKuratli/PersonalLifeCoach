from urllib.request import urlopen
from bs4 import BeautifulSoup
from calendar import month_name as MONTH_NAMES
from datetime import date, datetime
from enum import Enum
BASE_URL_ASTRO = "https://www.astro.com/cgi/swetest.cgi?"
PARAM_ASTRO = "&n=1&s=1&p=p&e=-eswe&f=PLBRS&arg=-head+"
Element = Enum("Element", "Feuer Erde Wind Wasser")
ZODIAC_NAMES = ("Widder", "Stier", "Zwillinge", "Krebs", "Löwe", "Jungfrau",
                "Waage", "Skorpion", "Schütze", "Steinbock", "Wassermann", "Fische")
SAVE_PLANETS = {"sun": "Sonne", "moon": "Mond", "mercury": "Merkur", "venus": "Venus", "mars": "Mars",
                "jupiter": "Jupiter", "saturn": "Saturn", "uranus": "Uranus", "neptune": "Neptun", "pluto": "Pluto",
                "chiron": "Chiron", "true node": "Mondknoten"}
ZODIAC_SIGNS = [(ZODIAC_NAMES[i], (i % 4) + 1, i * 30) for i in range(len(ZODIAC_NAMES))]
MAIN_ASPECTS = (
    ("Konjunktion", 0, 8, "neutral"),
    ("Sextil", 60, 4, "harmonisch"),
    ("Quadrat", 90, 6, "gespannt"),
    ("Trigon", 120, 7, "harmonisch"),
    ("Opposition", 180, 10, "gespannt")
)


def parse_position_fyf(val):
    grad = int(val[:2])
    mins = int(val[5:])
    sign, element, sign_start_grad = ZODIAC_SIGNS[val[2:4]]
    total_min = ((grad + sign_start_grad) * 60) + mins
    return {
        "grad": grad,
        "mins": mins,
        "sign": sign,
        "element": element,
        "total_min": total_min
    }


def get_soup(url):
    try:
        with urlopen(url) as source:
            source = source.read()
            soup = BeautifulSoup(source, "html.parser")
            return soup
    except Exception as e:
        print(f"Exception making soup for {url}: {e}")


def pad_zero(i):
    return str(i) if i >= 10 else "0" + str(i)


def parse_pos(pos):
    grad_total, rest = pos.split("°")
    grad_total = int(grad_total)
    mins, rest = rest.split("'")
    mins = int(mins.strip())
    sec = int(rest.strip())
    if sec >= 30:
        mins += 1
        if mins == 60:
            grad_total += 1
            mins = 0
    total_min = (grad_total * 60) + mins

    for sign, element, sign_start_grad in ZODIAC_SIGNS:
        grad = grad_total - sign_start_grad
        if 30 > grad > -1:
            return {
                "grad": grad,
                "mins": mins,
                "sign": sign,
                "element": element,
                "total_min": total_min
            }


def get_ephemeris(t):
    soup = get_soup(
        f"{BASE_URL_ASTRO}b={t.day}.{t.month}.{t.year}{PARAM_ASTRO}-t{pad_zero(t.hour)}.{pad_zero(t.minute)}00"
    )
    if soup:
        ret = {}
        lines = [line.strip() for line in soup.pre.font.string.splitlines() if line.strip()]
        for line in lines:
            try:
                planet, pos = line[:16].strip().lower(), line[16:line.index(".", 16)].strip()
                if planet in SAVE_PLANETS:
                    ret[SAVE_PLANETS[planet]] = parse_pos(pos)
            except ValueError as e:
                print(f"problematic string: {line}: {e}")
        return ret


def aspect_already_collected(found_aspects, planet, planet2, asp_name):
    for found_aspect in found_aspects:
        if all((
            asp_name == found_aspect["aspect"],
            planet in (found_aspect["planet"], found_aspect["planet2"]),
            planet2 in (found_aspect["planet"], found_aspect["planet2"])
        )):
            return True
    return False


def get_distance_mts(pos_mts1, pos_mts_2):
    distance = abs(pos_mts1 - pos_mts_2)
    # distance cannot be more than 180° => take the shorter way which is the other part of the 360°
    if distance > (180 * 60):
        distance = (360 * 60) - distance
    return distance


def get_aspects(eph):
    found_aspects = []
    for planet, position in eph.items():
        for asp_name, asp_grad, asp_grad_orb, asp_harmony in MAIN_ASPECTS:
            asp_mts, asp_mts_orb = asp_grad * 60, asp_grad_orb * 60
            asp_range_mts_min = asp_mts - asp_mts_orb
            asp_range_mts_max = asp_mts + asp_mts_orb
            for planet2, position2 in eph.items():
                if any((planet == planet2, aspect_already_collected(found_aspects, planet, planet2, asp_name))):
                    continue
                distance_mts = get_distance_mts(position["total_min"], position2["total_min"])
                if asp_range_mts_min <= distance_mts <= asp_range_mts_max:
                    asp_diff = abs(distance_mts - asp_mts)
                    accuracy = round(100 - (asp_diff / asp_mts_orb * 100), 2)
                    found_aspects.append({
                        "planet": planet,
                        "aspect": asp_name,
                        "planet2": planet2,
                        "accuracy": accuracy
                    })
    return found_aspects


def get_transits(eph_bday, eph_now):
    found_aspects = []
    for planet_transit, pos_transit in eph_now.items():
        planet_transit += " (Transit)"
        for asp_name, asp_grad, asp_grad_orb, asp_harmony in MAIN_ASPECTS:
            asp_mts, asp_mts_orb = asp_grad * 60, asp_grad_orb * 60
            asp_range_mts_min = asp_mts - asp_mts_orb
            asp_range_mts_max = asp_mts + asp_mts_orb
            for planet_radix, pos_radix in eph_bday.items():
                planet_radix += " (Radix)"
                distance_mts = get_distance_mts(pos_transit["total_min"], pos_radix["total_min"])
                if asp_range_mts_min <= distance_mts <= asp_range_mts_max:
                    asp_diff = abs(distance_mts - asp_mts)
                    accuracy = round(100 - (asp_diff / asp_mts_orb * 100), 2)
                    found_aspects.append({
                        "planet": planet_transit,
                        "aspect": asp_name,
                        "planet2": planet_radix,
                        "accuracy": accuracy
                    })
    return found_aspects


if __name__ == "__main__":
    from db import mongo_db as db
    # print(get_ephemeris_fyf(date(year=1988, month=3, day=1)))
    ephemeris = get_ephemeris(datetime(year=1988, month=3, day=1, hour=4, minute=24))
    db.set_config_property("ephemeris", ephemeris)
    aspects = get_aspects(ephemeris)
    print(aspects)
    db.set_config_property("aspects", aspects)
