# Forked from Anna PS's Rightmove scraper, simplified because we're only
# looking in one place.
from lxml import etree
from lxml.etree import tostring
from datetime import datetime
import scraperwiki
import StringIO

MIN_PRICE = 0
MAX_PRICE = 250000
MIN_BEDROOMS = 2
RADIUS_MILES = 3.0
SEARCH_PHRASES = [ 
    # Houses needing work
    "in need of updating", 
    "in need of some updating",
    "requiring updating", 
    "requiring some updating", 
    "in need of modernisation",
    "in need of some modernisation", 
    "requiring modernisation",
    "requiring some modernisation",
    "in need of renovation", 
    "in need of some renovation", 
    "requiring renovation", 
    "requiring some renovation", 
    "renovation project",
    # Houses with Land
    "acre", 
    "additional land", 
    "very large garden", 
    "extremely large garden", 
    "paddock" 
]
DOMAIN = 'http://www.rightmove.co.uk'

def scrape_individual_house(house_url):
    HOUSE_URL = (DOMAIN + house_url).split('/svr/')[0]
    print 'Scraping %s' % HOUSE_URL
    house_html = scraperwiki.scrape(HOUSE_URL)
    house_parser = etree.HTMLParser()
    house_tree = etree.parse(StringIO.StringIO(house_html), house_parser)
    house_text = house_tree.xpath('string(//div[@class="propertyDetailDescription"])')
    title = house_tree.xpath('string(//h1[@id="propertytype"])')
    # Check for search phrases
    for sp in SEARCH_PHRASES:
        if sp in house_text.lower() or sp in title.lower():
            house = {}
            image_url = tostring(house_tree.xpath('//img[@id="mainphoto"]')[0])
            price = house_tree.xpath('string(//div[@id="amount"])')
            map_img = house_tree.xpath('//a[@id="minimapwrapper"]/img')
            if map_img:
                map_img = tostring(house_tree.xpath('//a[@id="minimapwrapper"]/img')[0])
            else:
                map_img = ''
            location = house_tree.xpath('string(//div[@id="addresscontainer"]/h2)')
            house['title'] = "%s - %s - %s" % (title, location, price)
            print 'HOUSE FOUND! %s, %s ' % (house['title'], HOUSE_URL)
            item_text = '<a href="' + HOUSE_URL + '">' + image_url + '</a>'
            item_text += '<a href="' + HOUSE_URL + '">' + map_img + '</a>'
            item_text += house_text
            house['description'] = item_text.replace(sp,"<span style='font-weight:bold;color:red;'>%s</span>" % sp)
            house['link'] = HOUSE_URL
            house['pubDate'] = datetime.now()
            scraperwiki.sqlite.save(['link'], house)

# Gather list of results for an individual station.
def scrape_results_page(results_url, initial=False):
    results_url = DOMAIN + results_url
    html = scraperwiki.scrape(results_url)
    parser = etree.HTMLParser()
    tree = etree.parse(StringIO.StringIO(html), parser)
    house_links = tree.xpath('//ol[@id="summaries"]//a[starts-with(text(), "More details")]/@href')
    for house_link in house_links:
        scrape_individual_house(house_link)
    if initial:
        results_links = tree.xpath('//ul[@class="items"]//a/@href')
        for r in results_links:
            scrape_results_page(r)

# Do the actual scraping
for property_type in ('houses', 'land'):
    url1 = '/property-for-sale/find.html?locationIdentifier=REGION^494&minPrice=%s&maxPrice=%s' % (MIN_PRICE, MAX_PRICE)
    url2 = '&radius=%s&displayPropertyType=%s&numberOfPropertiesPerPage=50' % (RADIUS_MILES, property_type)
    INITIAL_URL = url1 + url2
    scrape_results_page(INITIAL_URL, initial=True)
