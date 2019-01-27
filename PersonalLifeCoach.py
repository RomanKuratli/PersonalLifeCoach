import locale
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask.json import dumps, loads, JSONDecoder
from pymongo.errors import DuplicateKeyError
from db import mongo_db as db
from utils import logger, owm_client, activities as act_module, diary_picture_manager
from os import path
from dateutil import parser


app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
locale.setlocale(locale.LC_ALL, 'de_DE')
COUNTRIES = db.get_countries()
LOGGER = logger.get_logger("controller")


# date format for diary entries
def diary_date_format(date):
    return date.strftime("%A, %-d. %B. %Y")


def diary_gallery_id(date):
    return f"gallery_{date.year}_{date.month}_{date.day}"


app.jinja_env.filters["diary_date_format"] = diary_date_format
app.jinja_env.filters["diary_gallery_id"] = diary_gallery_id


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


def datetime_parser(dct):
    for key, value in dct.items():
        if isinstance(value, type("")) and "GMT" in value:
            dct[key] = parser.parse(value)
    return dct


@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'
# ---------------- index page functions ------------------------


@app.route('/')
def index():
    quote = db.get_random_quote()
    good_day = db.get_good_day_entry()
    if good_day:
        good_day["pictures"] = diary_picture_manager.get_pictures_for_entry(good_day["entry_date"])
    location = db.get_location()
    if not db.has_todays_diary_entry():
        flash("Für heute gibt es noch keinen Tagebucheintrag!", "error")
    return render_template('index.html', quote=quote, good_day=good_day, location=location)


@app.route('/insert_diary_entry', methods=["post"])
def insert_diary_entry():
    try:
        entries = [e for e in request.form["entries"].split("\r\n") if e]  # skip empty lines
        success = db.insert_diary_entry(
            datetime.strptime(request.form["entry_date"], "%Y-%m-%d"),
            entries
        )
        if success:
            flash("Neuer Tagebucheintrag erfolgreich erstellt", "success")
        else:
            flash("Neuer Tagebucheintrag konnte nicht erstellt werden!", "error")
    except DuplicateKeyError:
        flash("Zu diesem Datum ist schon ein Tagebucheintrag vorhanden!", "error")
    return redirect(url_for("index"))


@app.route('/upload_diary_picture', methods=["post"])  # ajax path
def upload_diary_picture():
    entry_date = datetime.strptime(request.form["entry_date"], "%Y-%m-%d")
    picture = request.files["picture"]
    if diary_picture_manager.add_picture(entry_date, picture):
        return jsonify({"success": True, "pictures": diary_picture_manager.get_pictures_for_entry(entry_date)})
    return jsonify({"success": False})


@app.route('/delete_diary_picture', methods=["delete"])  # ajax path
def delete_diary_picture():
    url = request.form["url"]
    filename = url[url.rfind("/") + 1:]
    # extract the date from the file name
    entry_date = datetime.strptime(filename[:filename.rfind("_")], "%Y_%m_%d")
    if diary_picture_manager.delete_picture(filename):
        return jsonify({"success": True, "pictures": diary_picture_manager.get_pictures_for_entry(entry_date)})
    return jsonify({"success": False})


@app.route('/weather', methods=["get"])
def weather():
    location = db.get_location()
    owm_key = db.get_owm_key()
    weather_data = owm_client.get_weather(owm_key, location["city"], location["alpha2_cd"]) if location and owm_key else None
    return jsonify(weather_data)

# ---------------- quote page functions ------------------------


@app.route('/quotes', methods=["get"])
def quotes():
    quotes_by_source = db.get_quotes_grouped_by_source()
    return render_template("pages/quotes_page.html", quotes_by_source=quotes_by_source)


@app.route('/insert_quote', methods=["post"])
def insert_quote():
    try:
        success = db.insert_quote(
            request.form["quote"],
            request.form["author"],
            request.form["source"],
            request.form["lang"]
        )
        if success:
            flash("Zitat wurde erfolgreich aufgenommen", "success")
        else:
            flash("Zitat konnte nicht aufgenommen werden", "error")
    except DuplicateKeyError:
        flash("Dieses Zitat ist schon gespeichert", "error")
    return redirect(url_for("quotes"))


@app.route('/delete_quote', methods=["post"])
def delete_quote():
    try:
        db.delete_quote(request.form["key"])
        flash("Zitat erfolgreich gelöscht", "success")
    except Exception:
        flash("Zitat konnte nicht gelöscht werden", "error")
    return redirect(url_for("quotes"))

# ---------------- diary page functions ------------------------


@app.route('/diary', methods=["get"])
def diary():
    diary_entries = db.get_diary()
    # fetch the pictures for the diary entries
    for entry in diary_entries:
        entry["pictures"] = diary_picture_manager.get_pictures_for_entry(entry["entry_date"])
    return render_template("pages/diary_page.html", diary=diary_entries)

# ---------------- activity page functions ------------------------


@app.route('/activities', methods=["get"])
def activities():
    acts = db.get_activities()
    return render_template("pages/activity_page.html", activities=acts)


@app.route('/recommended_activities', methods=["get"])  # ajax path
def recommended_activities():
    act = act_module.get_recommended_activities(
        int(request.args["mentalEnergy"]),
        int(request.args["physicalEnergy"]),
        request.args["timeAtDisposal"]
    )
    return jsonify(recommended_activities=act)


@app.route('/insert_activity', methods=["post"])
def insert_activity():

    success = db.insert_activity(
        int(request.form["mentalEnergy"]),
        int(request.form["physicalEnergy"]),
        request.form["timeRequired"],
        True if "weatherRelevant" in request.form else False,
        request.form["activity"]
    )
    if success:
        flash("Aktivität erfolgreich eingefügt", "success")
    else:
        flash("Aktivität konnte nicht eingefügt werden", "error")
    return redirect(url_for("activities"))


@app.route('/delete_activity', methods=["post"])
def delete_activity():
    try:
        db.delete_activity(request.form["key"])
        flash("AKtivität erfolgreich gelöscht", "success")
    except Exception:
        flash("Aktivität konnte nicht gelöscht werden", "error")
    return redirect(url_for("activities"))

# ---------------- config page functions ------------------------


@app.route('/config', methods=["get"])
def config():
    return render_template("pages/config_page.html",
                           location=db.get_location(),
                           backup_collections=db.BACKUP_COLLECTIONS)


@app.route('/alpha2_cd')
def alpha2_cd():
    code = ""
    inp = request.args.get('input')
    for country in COUNTRIES:
        if inp.upper() == country["country_name"].upper():
            code = country["alpha2_cd"]
    return jsonify(alpha2_cd=code)


@app.route('/countries', methods=["get"])  # ajax path
def countries():
    inp = request.args.get('input')
    suggestions = [country for country in COUNTRIES if inp in country["country_name"]]
    return jsonify(suggestions=suggestions)


@app.route('/city')  # ajax path
def city():
    inp = request.args.get('input')
    country = request.args.get("country")
    cty = db.get_city(country, inp)
    if cty:
        return jsonify(found=True, city=cty)
    return jsonify(found=False)


@app.route('/cities', methods=["get"])  # ajax path
def cities():
    inp = request.args.get('input')
    country = request.args.get("country")
    suggestions = db.get_cities(country, inp)
    return jsonify(suggestions=suggestions)


@app.route('/set_location', methods=["post"])
def set_location():
    db.set_location(
        request.form["city"],
        request.form["country"],
        request.form["alpha2_cd"],
        request.form["latitude"],
        request.form["longitude"]
    )
    flash("Standort wurde erfolgreich angepasst", "success")
    return redirect(url_for("config"))


@app.route('/export_data', methods=["get"])
def export_data():
    save_collections = request.args.getlist("save_collections")
    LOGGER.debug(f"export data: {save_collections}")
    if save_collections:
        path_name = path.join(path.dirname(path.abspath(__file__)), "static")
        filename = path.join(path_name, "backup.json")
        with open(filename, "w") as target:
            buffer = {}
            for coll_name in save_collections:
                buffer[coll_name] = db.select_for_export(coll_name)
            target.write(dumps(buffer))
            return send_from_directory(path_name, "backup.json")
    else:
        flash("Mindestens eine Collection für das Backup muss angegeben werden", "error")
        return redirect(url_for("config"))


@app.route('/import_data', methods=["post"])
def import_data():
    file = request.files["import"]
    content = file.read()
    backup_json = loads(content, object_hook=datetime_parser)
    if db.import_from_backup(backup_json):
        flash("File erfolgreich importiert", "success")
    else:
        flash("Fehler beim Importieren der Datei", "error")
    return redirect(url_for("config"))


# ---------------- thanks page ------------------------
@app.route('/thanks')
def thanks():
    return render_template("pages/thanks.html")


if __name__ == '__main__':
    app.run()
