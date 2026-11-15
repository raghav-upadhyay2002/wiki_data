import requests
from bs4 import BeautifulSoup

API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "wiki-refs-class/0.1 (student project)"}

def get_html(title):
    params = {"action": "parse", "page": title, "prop": "text",
              "format": "json", "formatversion": 2, "disableeditsection": 1}
    r = requests.get(API, params=params, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.json()["parse"]["text"]

def extract_links(html):
    soup = BeautifulSoup(html, "lxml")      # turns the HTML into a searchable tree
    results = []
    for a in soup.select("a[href]"):        # every link on the page
        href = a["href"]
        classes = a.get("class") or []
        # keep only links that go to other websites
        if not href.startswith(("http://", "https://", "//")):
            continue
        if "external" not in classes:
            continue
        # decide where the link sits
        if a.find_parent(class_="infobox"):
            location = "infobox"
        elif a.find_parent("ol", class_="references") or a.find_parent(class_="reflist"):
            location = "references"
        else:
            location = "body"
        results.append((href, location))
    return results
