import cloudscraper

scraper = cloudscraper.create_scraper()
html = scraper.get("https://www.fastpeoplesearch.com/name/michael-guo_michigan")

print(html.text)