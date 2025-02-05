import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    
    
    if (resp.status != 200):
        i = 0
        while i < 10:
            print("ERROR")  
            i += 1
            # maybe just skip link if not 200?
            

    # get links
    # print(resp.raw_response.content)
    
    
    # write to disk all links traveled too, also keep a list of the list travled to avoid rerunning links and 
    # also avoid inf traps.
    
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    # get data (tokenize)

    
    
    # compare tokens from other sites (?) see what is considered low data maybe if total token -common word is under x we just skip it and move to the next url
    
    
    
    # get links
    for link in soup.find_all('a'):
        print(link.get('href'))
        print(is_valid(link.get('href')))
        # maybe transform the link here
    
    
    # heh chill asf
    # probably have a list of scrapped sites
    # if site comes up again stop scraping it lol
    # write to disk like links.txt or some stuff
    # sugoi
    return list()

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        # woah so epic if wrong file type do not scrape sugoi.
        
        return not re.match( 
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
