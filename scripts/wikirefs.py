import re
import sys
import time
import requests
import pandas as pd
import tldextract
from bs4 import BeautifulSoup
from urllib.parse import urlsplit, urlunsplit, unquote

API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "wiki-refs-class/0.1 (student project)"}

WIKIMEDIA = ("wikipedia.org", "wikimedia.org", "wikidata.org",
             "wmflabs.org", "toolforge.org", "mediawiki.org",
             "wikisource.org", "wikibooks.org", "wikiquote.org",
             "wiktionary.org", "wikinews.org", "wikiversity.org",
             "wikivoyage.org")

TRACKING = re.compile(r"^(utm_|fbclid$|gclid$)", re.I)
ext = tldextract.TLDExtract(suffix_list_urls=())


def api_get(params, tries=6):
    """Ask Wikipedia. If it says 'slow down' (429), wait and retry."""
    for _ in range(tries):
        r = requests.get(API, params=params, headers=HEADERS, timeout=60)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 30))
            print(f"  rate limited, waiting {wait}s")
            time.sleep(wait + 1)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("too many retries")


def get_html(title=None, pageid=None, oldid=None):
    """Return the rendered HTML of an article (by title, page id, or revision id)."""
    params = {"action": "parse", "prop": "text", "format": "json",
              "formatversion": 2, "disableeditsection": 1}
    if oldid:
        params["oldid"] = oldid
    elif pageid:
        params["pageid"] = pageid
    else:
        params["page"] = title
    return api_get(params)["parse"]["text"]


def random_articles(n):
    """Return n (pageid, title) pairs of random main-namespace articles."""
    found = {}
    while len(found) < n:
        j = api_get({"action": "query", "list": "random", "rnnamespace": 0,
                     "rnfilterredir": "nonredirects", "rnlimit": min(50, n),
                     "format": "json", "formatversion": 2})
        for p in j["query"]["random"]:
            found[p["id"]] = p["title"]
    return list(found.items())[:n]


def extract_links(html):
    """Return (url, location) for every external link in the article HTML."""
    soup = BeautifulSoup(html, "lxml")
    results = []
    for a in soup.select("a[href]"):
        href = a["href"]
        classes = a.get("class") or []
        if not href.startswith(("http://", "https://", "//")):
            continue
        if "external" not in classes:
            continue
        if a.find_parent(class_="infobox"):
            location = "infobox"
        elif a.find_parent("ol", class_="references") or a.find_parent(class_="reflist"):
            location = "references"
        else:
            location = "body"
        results.append((href, location))
    return results


def unwrap_archive(url):
    """web.archive.org/web/<digits>/<original>  ->  <original>"""
    m = re.search(r"web\.archive\.org/web/\d+[a-z_]*/(https?:?/*.+)$", url)
    if m:
        return re.sub(r"^(https?):/*", r"\1://", m.group(1))
    return url


def normalize(url):
    """One standard form per link, so duplicates are counted once."""
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    url = unwrap_archive(url)
    try:
        s = urlsplit(url)
    except ValueError:
        return None
    host = (s.hostname or "").lower().rstrip(".")
    if not host:
        return None
    if host.startswith("www."):
        host = host[4:]
    path = unquote(s.path).rstrip("/")
    query = "&".join(p for p in s.query.split("&")
                     if p and not TRACKING.match(p.split("=")[0]))
    return urlunsplit(("https", host, path, query, ""))


def is_wikimedia(host):
    return any(host == d or host.endswith("." + d) for d in WIKIMEDIA)


def domain_of(url):
    host = urlsplit(url).hostname or ""
    return ext(url).registered_domain or host


def run_tests():
    tests = [
        "https://web.archive.org/web/20120318165042/http://www.rutherfordjournal.org/article010111.html",
        "http://www.rutherfordjournal.org/article010111.html",
        "https://doi.org/10.1093%2Fref%3Aodnb%2F36578",
        "https://www.oxforddnb.com/help/subscribe#public",
        "https://wikipedialibrary.wmflabs.org/partners/88/",
    ]
    for t in tests:
        n = normalize(t)
        host = urlsplit(n).hostname
        print(n, "| wikimedia:", is_wikimedia(host), "| domain:", domain_of(n))


def run_step4(n=50):
    articles = random_articles(n)
    pd.DataFrame(articles, columns=["pageid", "title"]).to_csv(
        "data/sample_articles.csv", index=False)

    rows = []
    for i, (pid, title) in enumerate(articles, 1):
        try:
            html = get_html(pageid=pid)
        except Exception as e:
            print("skipping", pid, title, "->", e)
            continue
        for href, loc in extract_links(html):
            rows.append({"pageid": pid, "title": title,
                         "location": loc, "raw_url": href})
        time.sleep(0.5)
        if i % 10 == 0:
            print(i, "articles done")

    df = pd.DataFrame(rows)
    df.to_csv("data/current_links_raw.csv", index=False)

    funnel = {"raw links": len(df)}
    df["norm_url"] = df["raw_url"].map(normalize)
    df = df.dropna(subset=["norm_url"])
    df["host"] = df["norm_url"].map(lambda u: urlsplit(u).hostname or "")

    df = df[~df["host"].map(is_wikimedia)]
    funnel["after dropping Wikimedia sites"] = len(df)

    rank = {"infobox": 0, "references": 1, "body": 2}
    df = df.assign(rank=df["location"].map(rank)).sort_values("rank")
    df = df.drop_duplicates(subset=["pageid", "norm_url"]).drop(columns="rank")
    funnel["after removing duplicates within an article"] = len(df)

    df["domain"] = df["norm_url"].map(domain_of)
    df.to_csv("data/current_links_clean.csv", index=False)

    print()
    for k, v in funnel.items():
        print(f"{k}: {v}")
    print("Unique URLs:", df["norm_url"].nunique())
    print("Unique domains:", df["domain"].nunique())
    print()
    print(df["location"].value_counts())
    print()
    print(df["domain"].value_counts().head(15))


DATES = ["2017-11-30", "2018-11-30", "2019-11-30",
         "2020-11-30", "2021-11-30", "2022-11-30"]


def revision_at(pageid, date):
    """Return the revision ID that was live at the end of `date`, or None."""
    data = api_get({
        "action": "query", "prop": "revisions", "pageids": pageid,
        "rvlimit": 1, "rvdir": "older", "rvstart": date + "T23:59:59Z",
        "rvprop": "ids|timestamp", "format": "json", "formatversion": 2,
    })
    revs = data["query"]["pages"][0].get("revisions")
    return revs[0]["revid"] if revs else None


def links_at_dates(pageid):
    """For one article, return {date: list of links} for each date in DATES."""
    out = {}
    for d in DATES:
        rev = revision_at(pageid, d)
        if rev is None:
            out[d] = None          # article did not exist yet
            continue
        html = get_html(oldid=rev)
        out[d] = extract_links(html)
    return out


import os
RANK = {"infobox": 0, "references": 1, "body": 2}
HIST_OUT = "data/history_links.csv"


def clean_snapshot(links):
    """links = [(url, location), ...]  ->  {norm_url: location}"""
    best = {}
    for url, loc in links:
        n = normalize(url)
        if not n:
            continue
        if is_wikimedia(urlsplit(n).hostname or ""):
            continue
        if n not in best or RANK[loc] < RANK[best[n]]:
            best[n] = loc          # keep infobox > references > body
    return best


def run_history(n=10):
    arts = pd.read_csv("data/sample_articles.csv").head(n)
    done = set(pd.read_csv(HIST_OUT)["pageid"]) if os.path.exists(HIST_OUT) else set()
    for _, a in arts.iterrows():
        pid = int(a["pageid"])
        if pid in done:
            continue
        snaps = links_at_dates(pid)
        snaps["now"] = extract_links(get_html(pageid=pid))
        rows = []
        for d, links in snaps.items():
            if links is None:
                continue
            for u, loc in clean_snapshot(links).items():
                rows.append({"pageid": pid, "title": a["title"], "snapshot": d,
                             "location": loc, "norm_url": u, "domain": domain_of(u)})
        if rows:
            pd.DataFrame(rows).to_csv(HIST_OUT, mode="a", index=False,
                                      header=not os.path.exists(HIST_OUT))
        print("done", pid, a["title"], len(rows), "rows")
    h = pd.read_csv(HIST_OUT)
    print(h.groupby("snapshot")["norm_url"].count())


ORDER = ["2017-11-30", "2018-11-30", "2019-11-30", "2020-11-30",
         "2021-11-30", "2022-11-30", "now"]


def run_cohorts():
    h = pd.read_csv(HIST_OUT)
    h["step"] = h["snapshot"].map({s: i for i, s in enumerate(ORDER)})
    g = h.groupby(["pageid", "norm_url"])
    c = pd.concat([
        g["step"].min().rename("first_step"),
        g["snapshot"].apply(lambda s: "now" in set(s)).rename("alive_now"),
    ], axis=1).reset_index()
    c["cohort"] = c["first_step"].map(lambda i: ORDER[i])
    c.to_csv("data/link_cohorts.csv", index=False)
    out = c.groupby("cohort").agg(links=("norm_url", "count"),
                                  still_there=("alive_now", "sum"))
    out["pct_still_there"] = (100 * out["still_there"] / out["links"]).round(1)
    print(out.reindex([s for s in ORDER if s in out.index]))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_tests()
    elif len(sys.argv) > 1 and sys.argv[1] == "cohorts":
        run_cohorts()
    elif len(sys.argv) > 1 and sys.argv[1] == "history":
        run_history(int(sys.argv[2]) if len(sys.argv) > 2 else 10)
    elif len(sys.argv) > 1 and sys.argv[1] == "rev":
        pid = int(sys.argv[2])
        for d in DATES:
            print(d, revision_at(pid, d))
    elif len(sys.argv) > 1 and sys.argv[1] == "hist":
        res = links_at_dates(int(sys.argv[2]))
        for d, links in res.items():
            print(d, "no article" if links is None else len(links))
        first = next((l for l in res.values() if l), None)
        print(first[:2] if first else "no links found")
    else:
        run_step4()
