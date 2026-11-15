# Notes: citable points and references

## Points to cite

### Piccardi et al. (WWW '21)

| Point (paraphrased) | Where | Use in project |
| --- | --- | --- |
| Links were taken from rendered article HTML, because parsing wikitext can miss links. Cites Mitrevski et al. (2020). | §3.3, p. 251 | Justifies using rendered HTML in Steps 1 and 2. |
| External links were split by position into infobox, article body and references. | §3.3, p. 251 | Justifies the location labels. |
| English Wikipedia counts: 63.1M external links, 49.8M unique URLs. By location: 56.0% references, 39.5% body, 4.5% infobox. | §3.3, Table 1, p. 251 | Benchmark for the shape of our results. |
| Data came from logs for 24 March to 21 April 2019, with all external-link clicks and a 33% sample of pageviews. | §3.1, p. 251 | Describes their data period (ours differs). |
| Infobox links were classified as official or not, using a random forest trained on 2,000 hand-labeled links (387 official, 1,613 other) and 10 features. F1 was about 0.98 in 5-fold cross-validation. | §3.4, p. 252 | Only if we reproduce or mention the official-link classifier. |
| Click-through rates were computed only for links shown on at least 300 pageviews. | §3.5, p. 252 | Shows how they filtered for reliability. Clicks are not part of our task. |

### Veselovsky et al. (Web2Wiki, ICWSM 2026)

| Point (paraphrased) | Where | Use in project |
| --- | --- | --- |
| Links were extracted from the February 2021 Common Crawl (about 2.7 billion pages) by matching `<a>` tags, yielding 90,805,367 links. | §3, pp. 2346–2347 | Shows the `<a>`-tag approach. |
| The English analysis excludes links to other Wikimedia projects (Wikiquote, Wikinews, etc.). The full dataset keeps them. | §3, p. 2347 | Justifies dropping Wikimedia targets in Step 3. |
| English subset: 48,829,702 links from 14,462,267 pages across 940,239 domains. | §3, Table 1, p. 2347 | Optional benchmark. |
| Links were assigned to boilerplate, main content or user-generated segments by hand-built rules that check the HTML tags and attributes of each link's ancestors. | §5 and Appendix B, pp. 2350, 2356 | Parallel for our location rule. Their rules target general web pages. |
| Rules were developed iteratively: sample and label, derive rules, test on a new sample, refine. Precision was checked on 100 links per class and recall on 500 random links. | Appendix B, p. 2356 | Supports checking our own rules by hand. |
| Top linking domains were inspected by hand, revealing blogging platforms, Wikipedia mirrors and likely spam. | Appendix D, p. 2357 | Justifies manual inspection of top domains in Step 7. |
| Common Crawl excludes sites that block crawlers, so the data covers the surface web only. | Appendix A, p. 2356 | A limitation of their data, not ours. |

### Our own methods (do not attribute to the papers)

- URL normalization: lowercase, strip `www.`, remove fragments, treat `http` and `https` as the same.
- Unwrapping `web.archive.org` links.
- Using (article, normalized URL) pairs as the unit of analysis.
- Yearly snapshots and cohorts.

Web2Wiki's public code (`clean_links.py`) normalizes titles and extracts domains with `tldextract`. It can be cited to the repository for that.

## Reference entries

- Piccardi, T., Redi, M., Colavizza, G., and West, R. 2021. *On the Value of Wikipedia as a Gateway to the Web.* In Proceedings of The Web Conference 2021 (WWW '21), Ljubljana, Slovenia. ACM. <https://doi.org/10.1145/3442381.3450136>
- Veselovsky, V., Piccardi, T., Anderson, A., West, R., and Arora, A. 2026. *Web2Wiki: Characterizing Wikipedia Linking Across the Web.* Proceedings of the Twentieth International AAAI Conference on Web and Social Media (ICWSM 2026). <https://ojs.aaai.org/index.php/ICWSM/article/view/42754/50314>
- Mitrevski, B., Piccardi, T., and West, R. 2020. *WikiHist.html: English Wikipedia's full revision history in HTML format.* ICWSM. (Cited by WWW '21 for the HTML point; not yet read.)

## Cautions

- The ICWSM PDF shows pages 2345–2357. The final published page numbers or DOI may differ, so take final citation details from the publisher's page.
- Only the data and methods sections were read closely. Cite only the points in the tables above unless the other sections have been read.
