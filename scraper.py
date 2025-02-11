import re
from bs4 import BeautifulSoup
from time import sleep
from urllib.parse import urlparse, urlunparse, unquote
import hashlib

# global
seen_simhashes = set()
most_words = {}
# this should have url,and number of tokens :D
Log_location = "/home/thomaht3/cs121_A2Crawler/Logs/REMOVED.LOG"   # please remove this after testing.. or not who cares

def tokenize(html_body):
    """
    Tokenizes the HTML content into words, cleans the text, and returns a list of tokens.
    """
    soup = BeautifulSoup(html_body, 'html.parser')
    text = soup.get_text().strip()  # Extract text from HTML
    #  had bad tokenization....
    for tag in soup(["header", "footer", "nav", "aside", "script", "style"]):
        tag.extract() 
    main_content = soup.find("main") or soup.find("article") or soup.find("div", class_="content")
    text = main_content.get_text(separator=" ") if main_content else soup.get_text(separator=" ")
    tokens = re.findall(r"\b\w+\b", text.lower())
    for x in tokens:
        print(x)
    return tokens #praying this fucking works

def compute_token_weights(tokens):
    """
    Computes the frequency of each token and returns a dictionary of token: weight.
    """
    token_map = {}
    for token in tokens:
        if token in token_map:
            token_map[token] += 1
        else:
            token_map[token] = 1
            
    # should probably compute the # of words and save the largest - link 
    # gobal var holding all the tokens.. when keyboard interupt write to disk all the tokens ordered at the end or have a counter every 100ish links we print out the top 50 tokens :D
    # or just print out top 50 tokens ignoring stop words
    stop_words = []
    return token_map


def is_similar(content, seen_simhashes, threshold=3):
    """
    Checks if the content is similar to any previously seen SimHash.
    """
    tokens = tokenize(content)
    token_weights = compute_token_weights(tokens)
    simhash = compute_simhash(tokens, token_weights)
    for seen_hash in seen_simhashes:
        hamming_distance = bin(simhash ^ seen_hash).count('1')
        if hamming_distance <= threshold:
            return True  # Similar content found
    seen_simhashes.add(simhash)
    return False  # No similar content found

def compute_simhash(tokens, token_weights):
    """
    Computes the SimHash fingerprint for a list of tokens and their weights.
    """
    vector = [0] * 64 
    for token, weight in token_weights.items():
        token_hash = int(hashlib.sha1(token.encode('utf-8')).hexdigest(), 16) & 0xFFFFFFFFFFFFFFFF
        for i in range(64):
            bit = (token_hash >> i) & 1
            if bit == 1:
                vector[i] += weight
            else:
                vector[i] -= weight
    simhash = 0
    for i in range(64):
        if vector[i] > 0:
            simhash |= 1 << i
    return simhash

def scraper(url, resp):
    print(f"innit crawling {url}")
    print(resp.status//100)
    if (resp.status//100 ==6 or resp.status//100 ==4):
        print(f"BAD RESPONSE {resp.status//100}")
        return []
    if (is_valid(resp.raw_response.url)):
            print(f"innit crawling {resp.raw_response.url}")
            links = extract_next_links(url, resp)
            return [link for link in links if is_valid(link)] 
    else:
        return []

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
    # we can assume that links that arrive here are perfect and have went through the init filter! maybe do some hashing and stuff here and use it to match maybe write a json? or just keep a big ass hash table
    # hmm and then from there we go to is_valid or something and we also do a check if the hash is good?
    # Check for similar content
    if (url not in ["https://www.ics.uci.edu", "https://www.cs.uci.edu", "https://www.stat.uci.edu"]):
        if is_similar(resp.raw_response.content, seen_simhashes):
            print(f"Similar content detected for {url}")
            with open(Log_location, "a") as my_file:
                my_file.write(f"{url} has similar content alr looked at..\n")
                my_file.close()
            return []
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    print(f"CRAWLING: {resp.raw_response.url}")
    evil_list_of_links = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if not href:
            continue
        parsed = urlparse(href)._replace(fragment="")
        clean_link = urlunparse(parsed)
        evil_list_of_links.append(clean_link)  
    print(f"found {len(evil_list_of_links)} links from {resp.raw_response.url}")
    return evil_list_of_links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    # ADD FILTERS HERE FOR SPECIFIC WEBSITES
            # checks if awesome domain
    try:   
        pattern = (
            r"\.(css|js|bmp|gif|jpe?g|ico|png|tiff?|mid|mp2|mp3|mp4|"
            r"wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|ps|eps|tex|ppt|"
            r"pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|"
            r"7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1|thmx|mso|arff|rtf|jar|ppsx|"
            r"csv|rm|smil|wmv|swf|wma|zip|rar|gz|txt|svg|apk|webp|php)$"
        )
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        # woah so epic if wrong file type do not scrape sugoi.
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        parsed_path = unquote(parsed.path.lower())
        parsed_query = unquote(parsed.query.lower())
        
        print(domain, path)

        # checks for the valid file type
        if re.search(pattern, parsed_path) or re.search(pattern, parsed_query):
            print(f"XXXXXXXXXXXXXXXXXXXXXXXXXXXXRejected file: {parsed.path.lower()}")
            is_valid_file = False
        else:
            is_valid_file = True
        # check domain :D
        if (re.match(
            r"^(.*\.)?(ics|cs|informatics|stat)\.uci\.edu$", parsed.netloc.lower()) == None):
            is_valid_domain = False
        else:
            is_valid_domain = True

        # ok so like from here maybe we should automatically check for the robotx.txt :DDD
        # Filters for ics.uci.edu
        if domain == "ics.uci.edu":
            if path.startswith("/people") or path.startswith("/happening"):
                print(f"Blocked by hardcoded filter (ics.uci.edu): {url}")
                with open("/home/thomaht3/cs121_A2Crawler/Logs/REMOVED.LOG", "a") as my_file:
                    my_file.write(f"Blocked by hardcoded filter (ics.uci.edu): {url} path: {path}\n")
                return False

        # Filters for cs.uci.edu
        elif domain == "cs.uci.edu":
            if path.startswith("/people") or path.startswith("/happening"):
                print(f"Blocked by hardcoded filter (cs.uci.edu): {url}")
                with open("/home/thomaht3/cs121_A2Crawler/Logs/REMOVED.LOG", "a") as my_file:
                    my_file.write(f"Blocked by hardcoded filter (cs.uci.edu): {url} path: {path}\n")
                return False

        # Filters for informatics.uci.edu
        elif domain == "informatics.uci.edu":
            if path.startswith("/wp-admin/"):
                print(f"Blocked by hardcoded filter (informatics.uci.edu): {url}")
                with open("/home/thomaht3/cs121_A2Crawler/Logs/REMOVED.LOG", "a") as my_file:
                    my_file.write(f"Blocked by hardcoded filter (informatics.uci.edu): {url} path: {path}\n")
                return False

        # Filters for stat.uci.edu
        elif domain == "stat.uci.edu":
            if path.startswith("/wp-admin/"):
                if (path.startswith("/wp-admin/admin-ajax.php")):
                    return True
                print(f"Blocked by hardcoded filter (stat.uci.edu): {url}")
                with open("/home/thomaht3/cs121_A2Crawler/Logs/REMOVED.LOG", "a") as my_file:
                    my_file.write(f"Blocked by hardcoded filter (stat.uci.edu): {url} path: {path}\n")
                return False
            # Allow specific research paths
            if path.startswith("/research/"):
                allowed_research_paths = [
                    "/research/labs-centers/",
                    "/research/areas-of-expertise/",
                    "/research/example-research-projects/",
                    "/research/phd-research/",
                    "/research/past-dissertations/",
                    "/research/masters-research/",
                    "/research/undergraduate-research/",
                    "/research/gifts-grants/",
                ]
                if not any(path.startswith(allowed_path) for allowed_path in allowed_research_paths):
                    print(f"Blocked by hardcoded filter (stat.uci.edu): {url} path: {path} ")
                    with open("/home/thomaht3/cs121_A2Crawler/Logs/REMOVED.LOG", "a") as my_file:
                        my_file.write(f"Blocked by hardcoded filter (stat.uci.edu): {url}\n")
                    return False

        if (is_valid_file and is_valid_domain == False):
            with open("/home/thomaht3/cs121_A2Crawler/Logs/REMOVED.LOG", "a") as my_file:
                my_file.write(f"FILE: {url} | valid file: {is_valid_file}; valid domain : {is_valid_domain}\n")
        return (is_valid_file and is_valid_domain)

    except TypeError:
        print ("TypeError for ", parsed)
        raise