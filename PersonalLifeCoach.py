from flask import Flask, render_template, request, redirect, url_for, flash
from db import mongo_db as db
import logging
app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)


@app.route('/')
def hello_world():
    quote = db.get_random_quote()
    return render_template('index.html', quote=quote)


if __name__ == '__main__':
    app.run()
