import re
from bs4 import BeautifulSoup
from time import sleep
from urllib.parse import urlparse, urlunparse, unquote
import hashlib

# global
seen_simhashes = set()
most_words = {}
top_page  = ["", 0]
DEL_LOG_LOCATION = "/home/thomaht3/cs121_A2Crawler/Logs/REMOVED.LOG"
seed_sites = ["https://www.ics.uci.edu", "https://www.cs.uci.edu", "https://www.stat.uci.edu"]


def del_log_message(reason, url, log_file = DEL_LOG_LOCATION) -> None:
    """Helper function for del_logging messages"""
    with open(log_file, "a") as f:
        f.write(f"del: {url} bc: {reason}\n")
        

def tokenize(html_body):
    """
    Tokenizes the HTML content into words, cleans the text, and returns a list of tokens.
    """
    soup = BeautifulSoup(html_body, 'html.parser')
    text = soup.get_text().strip()  # Extract text from HTML
    for tag in soup(["header", "footer", "nav", "aside", "script", "style"]):
        tag.extract() 
    main_content = soup.find("main") or soup.find("article") or soup.find("div", class_="content")
    text = main_content.get_text(separator=" ") if main_content else soup.get_text(separator=" ")
    tokens = re.findall(r"\b\w+\b", text.lower())
    return tokens

def compute_token_weights(tokens):
    """
    Computes the frequency of each token and returns a dictionary of token: weight.
    """
    stopwords = [
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few", "for",
    "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's",
    "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm",
    "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't",
    "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
    "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there", "there's",
    "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when",
    "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
]
    token_map = {}
    for token in tokens:
        if token in token_map:
            token_map[token] += 1
            if len(token) > 3 and token not in stopwords and token.isnumeric() == False:
                most_words[token] += 1
        else:
            token_map[token] = 1
            most_words[token] = 1

    sorted_words = sorted(most_words.items(), key=lambda x: x[1], reverse=True)
    top_words = sorted_words[:250]
    
    
    with open("/home/thomaht3/cs121_A2Crawler/Logs/TOKEN.LOG", "w", encoding="utf-8") as f:
        for word, count in top_words:
            f.write(f"{word} - {count}\n")
    
    return token_map


def is_similar(url, content, seen_simhashes, threshold=2,):
    """
    Checks if the content is similar to any previously seen SimHash.
    """
    tokens = tokenize(content)
    if len(tokens) > top_page[1]:
        top_page[0] = url
        top_page[1] = len(tokens)
    print(top_page)
    token_weights = compute_token_weights(tokens)
    if url in seed_sites: #we want to crawl these sites
        return False

    simhash = compute_simhash(tokens, token_weights)
    for seen_hash in seen_simhashes:
        hamming_distance = bin(simhash ^ seen_hash) #xor different bits
        hamming_distance = hamming_distance.count("1") # count the different bits
        if hamming_distance <= threshold:
            return True  # Similar content found
    seen_simhashes.add(simhash) # add to the seen hashes
    return False  # No similar content found

def compute_simhash(z, token_weights):
    # redo this fuck code
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
    print(f"innit crawling {url}") #link in
    if resp.status // 100 in {4, 5, 6}:
        print(f"Bad response ({resp.status}) for {url}")
        del_log_message(f"bad resp {resp.status}", url)
        return [] # just dont read it :D
    if (is_valid(resp.raw_response.url)or url in seed_sites):
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
    if is_similar(url, resp.raw_response.content, seen_simhashes):
        print(f"Similar content detected for {url}")
        del_log_message("similar", url)
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
    return evil_list_of_links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    # ADD FILTERS HERE FOR SPECIFIC WEBSITES
            # checks if awesome domain
    try:   
        pattern = (
            r"\.(outlook-ical=1|css|js|bmp|gif|jpe?g|ico|png|tiff?|mid|mp2|mp3|mp4|"
            r"wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|ps|eps|tex|ppt|"
            r"pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|odc|"
            r"7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1|thmx|mso|arff|apk|war|sql|rtf|jar|ppsx|img|"
            r"csv|rm|smil|wmv|swf|wma|zip|rar|gz|svg|apk|webp)$"
        )
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        # woah so epic if wrong file type do not scrape sugoi.
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        parsed_path = unquote(parsed.path.lower())
        parsed_query = unquote(parsed.query.lower())

        # checks for the valid file type
        if re.search(pattern, parsed_path) or re.search(pattern, parsed_query):
            print(f"Rejected file: {parsed.path.lower()}")
            is_valid_file = False
        else:
            is_valid_file = True
        # check domain :D
        if (re.match(
            r"^(.*\.)?(ics|cs|informatics|stat)\.uci\.edu$", parsed.netloc.lower()) == None):
            is_valid_domain = False
        else:
            is_valid_domain = True
        # Filters for ics.uci.edu
        if domain == "ics.uci.edu":
            if path.startswith("/people") or path.startswith("/happening"):
                del_log_message(f"Blocked by hardcoded filter (ics.uci.edu) path: {path}", url)
                return False
            with open("/home/thomaht3/cs121_A2Crawler/Logs/ics.log", "a", encoding="utf-8") as f:
                f.write(f"{parsed.netloc} - {path}\n") # work on this as the final one and do a test of a full crawl

        # Filters for cs.uci.edu
        elif domain == "cs.uci.edu":
            if path.startswith("/people") or path.startswith("/happening"):
                del_log_message(f"Blocked by hardcoded filter (cs.uci.edu) path: {path}", url)
                return False

        # Filters for informatics.uci.edu
        elif domain == "informatics.uci.edu":
            if path.startswith("/wp-admin/"):
                del_log_message(f"Blocked by hardcoded filter (informatics.uci.edu) path: {path}", url)
                return False

        # Filters for stat.uci.edu
        elif domain == "stat.uci.edu":
            if path.startswith("/wp-admin/"):
                if (path.startswith("/wp-admin/admin-ajax.php")):
                    return True
                del_log_message(f"Blocked by hardcoded filter (stat.uci.edu) path: {path}", url)
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
                    del_log_message(f"Blocked by hardcoded filter (stat.uci.edu) path: {path}", url)
                    return False
        return (is_valid_file and is_valid_domain)

    except TypeError:
        print ("TypeError for ", parsed)
        raise