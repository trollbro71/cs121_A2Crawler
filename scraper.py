import re
from bs4 import BeautifulSoup
from time import sleep
from urllib.parse import urlparse, urlunparse


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]


def tokenize(html):
    
    tokens = []
    
    
    # idea write token to logs url - token list?, or make a new txt write to disk for each url (probably terrible idea)
    
    return tokens

    
def extract_next_links(url, resp):
    sleep(.5)
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    
    if resp.status != 200:
        print(f"ERROR: Status {resp.status} for {url}")
        return []  # Skip this URL if response is not 200
            

    # get links
    # print(resp.raw_response.content)
    
    
    # write to disk all links traveled too, also keep a list of the list travled to avoid rerunning links and 
    # also avoid inf traps.
    
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    # get data (tokenize)
    for element in soup(["script", "style", "meta", "noscript", "header", "footer", "aside"]):
        element.extract()

    # Get visible text
    text = soup.get_text(separator=" ")

    # Clean up whitespace and non-text characters
    text = re.sub(r'\s+', ' ', text).strip()
    
    
    print (text)
    # TOKENIZER HERE *************************************************************** [maybe move this after checking if valid html might fuck up the tokenizer]
    
    # compare tokens from other sites (?) see what is considered low data maybe if total token -common word is under x we just skip it and move to the next url
    
    
    print(f"Crawling: {resp.raw_response.url}")
    # get links
    evil_list_of_links = []
    
    for link in soup.find_all('a'):
        href = link.get('href')
        if not href:
            continue  # Skip NoneType links
        
        # Remove fragment
        parsed = urlparse(href)._replace(fragment="")
        clean_link = urlunparse(parsed)  # Convert ParseResult back to string
        
        if is_valid(clean_link):
            evil_list_of_links.append(clean_link)
    
    return evil_list_of_links
        
    
    

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    
    # ADD FILTERS HERE FOR SPECIFIC WEBSITES
    
    #  read worker.log 
    
    try:
        parsed = urlparse(url)
        # remove the fragment
        parsed = parsed._replace(fragment="")
        
        if parsed.scheme not in set(["http", "https"]):
            return False
        # woah so epic if wrong file type do not scrape sugoi.
        
        # in the name lel
        is_valid_file = not re.match( 
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
        # checks if awesome domain
        if (re.match(
            r"^(.*\.)?(ics|cs|informatics|stat)\.uci\.edu$", parsed.netloc.lower()) == None):
            is_valid_domain = False
        else:
            is_valid_domain = True
        
        
        return (is_valid_file and is_valid_domain)

    except TypeError:
        print ("TypeError for ", parsed)
        raise
