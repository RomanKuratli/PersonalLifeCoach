from flask import Flask, render_template, request, redirect, url_for, flash
from db import mongo_db as db
import logging
from pymongo.errors import DuplicateKeyError
from datetime import datetime
import locale
app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
locale.setlocale(locale.LC_ALL, 'de_DE')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)


#date format for diary entries
def diary_date_format(date):
    return date.strftime("%A, %-d. %B. %Y")


app.jinja_env.filters["diary_date_format"] = diary_date_format


# ---------------- index page functions ------------------------


@app.route('/')
def index():
    quote = db.get_random_quote()
    good_day = db.get_good_day_entry()
    if not db.has_todays_diary_entry():
        flash("Für heute gibt es noch keinen Tagebucheintrag!", "error")
    return render_template('index.html', quote=quote, good_day=good_day)


@app.route('/insert_diary_entry', methods=["post"])
def insert_diary_entry():
    try:
        success = db.insert_diary_entry(
            datetime.strptime(request.form["entry_date"], "%Y-%m-%d"),
            request.form["entries"].split("\r\n")
        )
        if success:
            flash("Neuer Tagebucheintrag erfolgreich erstellt", "success")
        else:
            flash("Neuer Tagebucheintrag konnte nicht erstellt werden!", "error")
    except DuplicateKeyError:
        flash("Zu diesem Datum ist schon ein Tagebucheintrag vorhanden!", "error")
    return redirect(url_for("index"))


# ---------------- quote page functions ------------------------


@app.route('/quotes', methods=["get"])
def quotes():
    quotes_by_source = db.get_quotes_grouped_by_source()
    return render_template("pages/quotes_page.html", quotes_by_source=quotes_by_source)


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
    return render_template("pages/diary_page.html", diary=diary_entries)

if __name__ == '__main__':
    app.run()
