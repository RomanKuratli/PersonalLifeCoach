# returns a list of activities ranked with the best suited activity on top
from db import mongo_db as db
from utils import logging, owm_client
LOGGER = logging.get_logger("activities")


def get_minutes_from_time(time):
    splt = time.split(":")
    minutes = int(splt[0]) * 60 + int(splt[1])
    return minutes


def get_score(act, mental_energy, physical_energy, time_at_disposal):
    LOGGER.debug(f'fetching score for activity {act} ')
    factors = 1
    score = get_minutes_from_time(act["time_required"]) / get_minutes_from_time(time_at_disposal) * 100
    LOGGER.debug(f'score for time: {score}')
    if act["mental_energy"] - 1:  # energy needed more than low
        factors += 1
        mental_score = 100 if act["mental_energy"] == mental_energy else 50
        LOGGER.debug(f"score for mental energy: {mental_score}")
        score += mental_score
    if act["physical_energy"] - 1:  # energy needed more than low
        factors += 1
        physical_score = 100 if act["physical_energy"] == physical_energy else 50
        LOGGER.debug(f"score for mental energy: {physical_score}")
        score += physical_score
    if act["weather_relevant"] and owm_client.get_cashed_weather():
        #factors += 1
        # weather = owm_client.get_cashed_weather()
        # weather_s
        pass
    percent_score = round(score / factors)
    LOGGER.debug(f"{score} / {factors} = {percent_score}")
    return percent_score


def get_recommended_activities(mental_energy, physical_energy, time_at_disposal):
    LOGGER.debug(f"mental_energy:{mental_energy}, physical_energy: {physical_energy}, time_at_disposal: {time_at_disposal}")

    ret = []
    for act in db.get_activities():
        if all([
            mental_energy >= act["mental_energy"],
            physical_energy >= act["physical_energy"],
            get_minutes_from_time(time_at_disposal) >= get_minutes_from_time(act["time_required"])
        ]):  # TODO place from configuration should also be taken into account
            act["score"] = get_score(act, mental_energy, physical_energy, time_at_disposal)
            del act["_id"]
            ret.append(act)
    ret.sort(key=lambda activity: activity["score"], reverse=True)
    return ret
