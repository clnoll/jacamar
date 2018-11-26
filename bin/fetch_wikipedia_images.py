import csv
import sqlite3
import sys
import time
from functools import partial

from clint.textui import colored
import requests
from bs4 import BeautifulSoup


green = partial(colored.green, bold=True)
red = partial(colored.red, bold=True)


def fetch_image_url(query):
    response = requests.get(f"https://en.wikipedia.org/w/index.php?title={query}")
    response.raise_for_status()
    html = response.content
    soup = BeautifulSoup(html, features="html5lib")
    image_url = soup.select_one("table.infobox").select_one("img")["src"]
    if not image_url.startswith("http"):
        image_url = "http:" + image_url
    return image_url


def fetch_image_urls(db_file, output_file):
    fieldnames = ["id", "url", "species_id"]

    with open(output_file, "r") as fp:
        reader = csv.DictReader(fp, fieldnames=fieldnames)
        rows = list(reader)
        if rows:
            species_ids = {int(row["species_id"]) for row in rows}
            image_id = max((int(row["id"]) for row in rows), default=0)

    with open(output_file, "a", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        cursor = sqlite3.connect(db_file).cursor()
        query = """
        select species.id, genus.name, species.name from species join genus on species.genus_id = genus.id
        """
        images = []
        for species_id, genus, species in cursor.execute(query):
            if species_id in species_ids:
                info(f"Already have image for {genus} {species}, skipping")
                continue
            try:
                url = fetch_image_url(f"{genus}_{species}")
            except Exception as ex:
                error(f"{type(ex).__name__}: {ex}")
                continue
            image_id += 1
            image = {"id": image_id, "species_id": species_id, "url": url}
            print(image)
            writer.writerow(image)
            fp.flush()
            species_ids.add(species_id)
            time.sleep(1)


def info(message):
    print(green(message), file=sys.stderr)


def error(msg):
    print(red(msg), file=sys.stderr)


if __name__ == "__main__":
    [db_file] = sys.argv[1:]
    output_file = "tables/image.tsv"
    fetch_image_urls(db_file, output_file)
