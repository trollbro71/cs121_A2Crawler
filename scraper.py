import re
from bs4 import BeautifulSoup
from time import sleep
from urllib.parse import urlparse, urlunparse, unquote
import hashlib

# global
seen_simhashes = set()
most_words = {}
top_page  = ["", 0,"",0,"",0]
DEL_LOG_LOCATION = "/home/thomaht3/cs121_A2Crawler/Logs/REMOVED.LOG"
seed_sites = ["https://www.ics.uci.edu", "https://www.cs.uci.edu", "https://www.stat.uci.edu"]
ics_links = set()
ics_count = {} # domain, # of differnt paths crawled :D


def del_log_message(reason, url, log_file = DEL_LOG_LOCATION) -> None:
    """Helper function for del_logging messages"""
    with open(log_file, "a") as f:
        f.write(f"del: {url} bc: {reason}\n")
        

def tokenize(html_body):
    """
    Tokenizes the HTML content into words, cleans the text, and returns a list of tokens.
    
    Returns:
    List of tokens
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
    
    
    returns:
    dictonary of tokens and token weight
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
            if len(token) > 3 and token not in stopwords and token.isalpha() == True:
                most_words[token] += 1
        else:
            token_map[token] = 1
            most_words[token] = 1

    sorted_words = sorted(most_words.items(), key=lambda x: x[1], reverse=True)
    top_words = sorted_words[:300] #top 300 words manual filter to get the top 100
    
    # write to disk
    with open("/home/thomaht3/cs121_A2Crawler/Logs/TOKEN.LOG", "w", encoding="utf-8") as f:
        for word, count in top_words:
            f.write(f"{word} - {count}\n")
    return token_map


def is_similar(url, content, seen_simhashes, threshold=5,):
    """
    Checks if the content is similar to any previously seen SimHash.
    
    Returns:
        True if similar conent
        False if not similar
    """
    tokens = tokenize(content)
    # which is the top page
    if len(tokens) > top_page[1]:
        top_page[4] = top_page[2]
        top_page[5] = top_page[3]
        top_page[2] = top_page[0]
        top_page[3] = top_page[1]
        top_page[0] = url
        top_page[1] = len(tokens)
    print(top_page)
    token_weights = compute_token_weights(tokens)
    if url in seed_sites: #we want to crawl the seeded sites
        return False
    simhash = compute_simhash(tokens, token_weights)
    for seen_hash in seen_simhashes:
        hamming_distance = bin(simhash ^ seen_hash) #xor different bits
        hamming_distance = hamming_distance.count("1") # count the different bits
        if hamming_distance <= threshold:
            return True  # Similar content found
    seen_simhashes.add(simhash) # add to the seen hashes
    return False  # No similar content found

def compute_simhash(token_weights):
    """
    Computes the SimHash fingerprint for a list of tokens and their weights.

    Args:
        token_weights (dict): A dictionary where keys are tokens (strings)
                              and values are their respective weights (integers).

    Returns:
        int: The SimHash fingerprint as a 64-bit integer.
    """
    # Initialize a vector to hold the weighted sums of each bit position
    vector = [0] * 64 
    for token, weight in token_weights.items():
        # Hash each token
        token_hash = int(hashlib.sha1(token.encode('utf-8')).hexdigest(), 16) & 0xFFFFFFFFFFFFFFFF 
        # Update the bit vector based on the token hash
        for i in range(64):
            bit = (token_hash >> i) & 1
            if bit == 1:
                vector[i] += weight
            else:
                vector[i] -= weight
    # Compute the final SimHash based on the bit vector
    simhash = 0
    for i in range(64):
        if vector[i] > 0:
            simhash |= 1 << i
    return simhash

def scraper(url, resp):
    '''
    The starting point
    '''
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
    """
    Extract hyperlinks from the response content.

    Args:
        url (str): The URL that was used to get the page.
        response: The response object containing the page data.
    
    Returns:
        list: A list of hyperlinks (as strings) scraped from the response content.
    """
    # Check for similar content before proceeding
    if is_similar(url, resp.raw_response.content, seen_simhashes):
        print(f"Similar content detected for {url}")
        del_log_message("similar", url)
        return []
    # Use Soup to look for links
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    scrapped_links = []
    
    for link in soup.find_all('a'):
        href = link.get('href')
        if not href:
            continue
        # remove fragment
        parsed = urlparse(href)._replace(fragment="")
        clean_link = urlunparse(parsed)
        scrapped_links.append(clean_link)  
    return scrapped_links

def is_valid(url):
    """
    Determine whether a url should be crawled or not
    
    Returns:
        True if url should be crawled
        False if not
        
    """
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    # ADD FILTERS HERE FOR SPECIFIC WEBSITES
            # checks if awesome domain
    try:   
        pattern = (
            r"\.(outlook-ical=1|css|js|bmp|gif|jpe?g|ico|png|tiff?|mid|mp2|mp3|mp4|files/pdf|"
            r"wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|ps|eps|tex|ppt|"
            r"pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|odc|" 
            r"7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1|thmx|mso|arff|apk|war|sql|rtf|jar|ppsx|img|"
            r"csv|rm|smil|wmv|swf|wma|zip|rar|gz|svg|apk|webp)$"
        )
        parsed = urlparse(url)
        
        # Reject URLs with unsupported schemes (only allow HTTP/HTTPS)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        parsed_path = unquote(parsed.path.lower())
        parsed_query = unquote(parsed.query.lower())
        
        # Reject URLs with blocked file extensions
        if re.search(pattern, parsed_path) or re.search(pattern, parsed_query):
            print(f"Rejected file: {parsed.path.lower()}")
            return False
        
        # Allow only specific UCI domains
        if not re.match(
        r"^(.*\.)?(ics|cs|informatics|stat)\.uci\.edu$", parsed.netloc.lower()):
            return False
        
        
        # Filters for cs.uci.edu
        if re.search(r"informatics.uci.edu", domain):
        # Filters for informatics.uci.edu
            if path.startswith("/wp-admin/"):
                del_log_message(f"Blocked by hardcoded filter (informatics.uci.edu) path: {path}", url)
                return False
            
        # Filters for stat.uci.edu
        elif re.search(r"stat.uci.edu", domain):
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
                
        # Filters for ics.uci.edu
        elif re.search(r"ics.uci.edu", domain):
            if path.startswith("/people") or path.startswith("/happening"):
                del_log_message(f"Blocked by hardcoded filter (ics.uci.edu) path: {path}", url)
                return False
            # track unique links
            if url not in ics_links:
                ics_links.add(url)
                if domain in ics_count:
                    ics_count[domain] += 1
                else:
                    ics_count[domain] = 1
            with open("/home/thomaht3/cs121_A2Crawler/Logs/ics.log", "w", encoding="utf-8") as f:
                for total_domain, count in ics_count.items():
                    f.write(f"{total_domain} - {count}\n")
        # Filters for cs.uci.edu         
        elif re.search(r"cs.uci.edu", domain):
            if path.startswith("/people") or path.startswith("/happening"):
                del_log_message(f"Blocked by hardcoded filter (cs.uci.edu) path: {path}", url)
                return False
        return (True)
    except TypeError:
        print ("TypeError for ", parsed)
        raise