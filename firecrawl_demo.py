from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key="fc-28cce56afd4c4218852a6a700a2099d4")

def scrape_urls(urls):
  ret = []
  for url in urls:
    scrape_status = app.scrape_url(
      url, 
      params={'formats': ['markdown']}
    )
    ret.append(scrape_status)
  return ret

# Scrape a website:
print(scrape_urls(["https://www.regis.org/article?id=11851"]))