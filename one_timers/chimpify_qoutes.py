from urllib.request import urlopen
from bs4 import BeautifulSoup
from db import mongo_db as db
url = "https://www.chimpify.de/marketing/101-motivierende-zitate-und-sprueche-fur-deinen-erfolg/"

if __name__ == "__main__":
    db.delete_quotes_from_source(url)
    with urlopen(url) as source:
        source = source.read()
        soup = BeautifulSoup(source, "html.parser")
        ol_tag = soup.find("ol")
        for quote in ol_tag.find_all("li"):
            quote_text = quote.get_text().split(" – ")[0]
            author = quote.em.get_text()
            db.insert_quote(quote_text, author, url, "de")
