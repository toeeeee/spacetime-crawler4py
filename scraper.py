import re
import hashlib
import sqlite3
import urllib.robotparser
from bs4 import BeautifulSoup as BS
from urllib.parse import urlparse, parse_qs


# SCRAPER GLOBAL VARIABLES
LONGEST_PAGE = ()  # ( format: page, number of words ) the page with the greatest number of words
FREQ_DICT = {}  # dict of word-frequency pairs
STOP_WORDS = ["a", "about", "above", "after", "again", "against", "all", "am", "an", "and",  "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing","don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", "them","themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've","this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd","we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", "where", "which", "while","who", "whom", "why", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"] # list of words that will not be considered for the top 50 most common words
SD_COUNT = {}  # format: {"subdomain": count, ...}
U_PAGES = set()  # Parsed urls
PREVIOUS_HASH = [] # Hash where each int is an element of a binary number


def scraper(url, resp) -> list:
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]


def extract_next_links(url, resp):
    global PREVIOUS_HASH
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    found_links = [] # a list for storing found links
    # Check to make sure that the current url is valid and the response status is good
    if resp.status != 200:
        return found_links
    else:
        # Get the html content of the page
        # Using BeautifulSoup to parse the html, and then find all the links within it
        page_content = resp.raw_response.content
        soup = BS(page_content, 'html.parser')
        
        plain_text = str(soup.get_text())  # plain text of the page contents (gets rid of HTML elements)
        plain_text = plain_text.strip().lower()  # remove leading & trailing whitespace, & lowercase all chars
        normalized_text = re.sub(r'\s+', ' ', plain_text)  # sequences of whitespace replaced with one space
        
        is_duplicate = check_db(normalized_text, resp.raw_response.url)  # do same-page check
        if is_duplicate: # if True, then this page is a duplicate of one already crawled over
            return []
        # else, not a duplicate: continue processing the page
        tokens = tokenizer(normalized_text)  # tokenize the current page
        if len(tokens) < 25:  # if the page is empty/low content
            return found_links
        
        file = open("SimHashLog.txt", "a")
        if sim_hash(PREVIOUS_HASH, tokens):
            file.write(f"{resp.raw_response.url} : Page Similar\n")
            file.close()
            return found_links
        file.write(f"{resp.raw_response.url} : Page Not Similar\n")
        file.close()
            

        update_freq(tokens)  # update the token frequency dictionary
        update_longest_page(normalized_text, resp.raw_response.url)  # update the longest page found
        for soup_url in soup.find_all('a'):
            link = soup_url.get('href')
            if link not in found_links:
                found_links.append(link)
                    
    return found_links


# SCRAPER FUNCTIONS ----------------------------------------------------------------------------------------------------------

def tokenizer(content, allow_stop_words=False) -> list:
    #tokenizer for page content
    tokens = []
    new_token = ""
    for char in content:
        text = str(char)
        if not text:  # if 'text' is empty, every char in 'content' has been iterated over: check if 'new_token' is a valid word and add into 'tokens' if so
            if not allow_stop_words:  # any words in the STOP_WORDS list won't be considered
                if new_token and new_token not in STOP_WORDS and len(new_token) > 1 and not(new_token.isdigit()):  # if new_token is a valid word, then add it to the list of tokens found on this page
                    tokens.append(new_token)
                    break
            else:
                if new_token:
                    tokens.append(new_token)
                    break
        if text.isalnum():  # if char is alphanumeric, add it to 'new_token' and continue checking for valid chars
            new_token += text.lower()
        else:  # else, for-loop has iterated over a full word: check if it's valid, and add to 'tokens' if so
            if not allow_stop_words:  # any words in the STOP_WORDS list won't be considered
                if new_token and new_token not in STOP_WORDS and len(new_token) > 1 and not(new_token.isdigit()):
                    tokens.append(new_token)
            else:
                if new_token:
                    tokens.append(new_token)
            new_token = ""
    return tokens

def update_freq(tokens) -> None:
    #updates the global FREQ_DICT dictionary
    global FREQ_DICT
    for token in tokens:  # increase token's frequency of being found while crawling by 1; if it doesn't exist, then add the word to the dictionary
        try:
            FREQ_DICT[token] += 1
        except KeyError:
            FREQ_DICT[token] = 1

    with open('top50.txt', 'w') as f:  # as words are added to the dictionary, re-evaluate the 50 words encountered most frequently while crawling; save this info to a separate txt file in case of server crashes/bugs crashing the program
        f.write("Top 50 Words:\n")
        items = sorted(FREQ_DICT.items(), key = lambda token: token[1], reverse = True)[0:50]
        for word in items:
            try:
                f.write(f"{word[0]}: {word[1]}\n")
            except IndexError:
                break

def update_longest_page(content, page) -> None:
    #Update the longest page found using global variables
    global LONGEST_PAGE

    curr_len = len(tokenizer(content, allow_stop_words=True))

    if not LONGEST_PAGE:
        LONGEST_PAGE = (page, curr_len)
    elif curr_len > LONGEST_PAGE[1]:
        LONGEST_PAGE = (page, curr_len)

    with open('longest.txt', 'w') as f:  # re-evaluate the longest page encountered by the crawler as new pages are iterated over; save this info to a separate txt file in case of server crashes/bugs crashing the program
        f.write(f"Longest page: {LONGEST_PAGE[0]}\nLength: {LONGEST_PAGE[1]}")

# SAME PAGE CHECK ----------------------------------------------------------------------------------------------------------

def check_db(text: str, url) -> bool:
    """
    check if current page is an exact duplicate of other pages already crawled over
    """
    
    hash = hashlib.sha256(text.encode()).hexdigest()  # generate the sha256 hash of the given text
    file = open('hashes.txt', 'a')  # open the txt file that the hashes will be written into
    # create a connection to the database 'hashes.db' (creates the db if it doesn't already exist)
    con = sqlite3.connect("hashes.db")
    # Create a db cursor to execute SQL statements and fetch results from SQL queries
    cur = con.cursor()
    # check if the 'hashes' table already exists in the 'hashes' db
    res = cur.execute("SELECT name FROM sqlite_master WHERE name='hashes'")
    res = res.fetchone()  # if res == anything other than None, then it exists in db
    if not res:  # if it doesn't exist, create the 'hashes' table
        cur.execute(" CREATE TABLE hashes (hash STR) ")  # table created with one column named 'hash'
        con.commit()  # commit the CREATE TABLE transaction to the db
    # check if hash already in db
    res = cur.execute("SELECT * FROM hashes WHERE hash = ?", (hash,))
    res = res.fetchone()  # if res == anything other than None, it was found in the table
    if res:  # since it's in db, return False: this page is a duplicate of one already crawled over
        file.write(f"Duplicate -- url: {url} | hash: {hash}")
        file.close()
        return True
    # otherwise, add its hash to the table
    cur.execute(f"""INSERT INTO hashes(hash) VALUES(?)""", (hash))
    con.commit()  # commit the INSERT transaction to db

    # now get that hash from the table and wite it into 'hashes.txt'
    file.write(f"New Page -- url: {url} | hash: {hash}")
    file.close()
    
    return False


# SIMHASHING DONE BELOW ----------------------------------------------------------------------------------------------------------

'''
Member Variables:
tokens

'''

def string_to_binary_hash(string):
    hash_value = hashlib.sha256(string.encode()).hexdigest()
    binary_hash = bin(int(hash_value, 16))[2:] # remove header of binary string
    binary_hash = binary_hash[:10].zfill(10)
    return binary_hash

def list_to_binary_hash(string_list):
    binary_hashes = []
    for string in string_list:
        binary_hash = string_to_binary_hash(string)
        binary_hashes.append(binary_hash)
    return binary_hashes

def computeWordFrequencies(tokens) -> dict :  # return frequencies of file's tokens
    instances = {} # dict of frequencies of words in the given text file
    for token in tokens:
        if token not in instances:
            instances[token] = 0
        instances[token] += 1
    return instances

def count_digit(token_freq):
    data_for_fingerprint = []
    for x in range(10):
        bit_sum = 0
        for key, value in token_freq.items():
            if get_digit(int(key), x) > 0:
                bit_sum += value
            else:
                bit_sum -= value
        data_for_fingerprint.append(bit_sum)
    return data_for_fingerprint

# The // performs integer division by a power of ten to move the digit to the ones position, 
# then the % gets the remainder after division by 10.
# Note that the numbering in this scheme uses zero-indexing and starts from the right side of the number.
def get_digit(number, n):
    return number // 10**n % 10

def generate_fingerprint(list):
    fingerprint = []
    for value in list:
        if value > 0:
            fingerprint.append(1)
        else:
            fingerprint.append(0)
    return fingerprint

#if its similar return true, else return false
def compare_fingerprint(previous_hash, new_fingerprint):
    #see how many bits are the same from the first fingerprint to the second
    similarity_score = 0
    threshold = 0.85
    for x in range(10):
        if previous_hash[x] == new_fingerprint[x]:
            similarity_score += 1
    if similarity_score/10 > threshold:
        return True
    return False


#handles calendar webpages/ blogs/ events
#values of the binary are reversed, that means the data originally is 1-2-3-4-5, but our fingerprint is stored as 5-4-3-2-1
#if you want to access these values, start from the beginning of the fingerprint (but know that that's the last hash)
def sim_hash(previous_hash, tokens):
    global PREVIOUS_HASH

    hash_tokens = list_to_binary_hash(tokens)
    token_freq = computeWordFrequencies(hash_tokens)
    #print(token_freq)
    fingerprint = generate_fingerprint(count_digit(token_freq))
    if PREVIOUS_HASH:
        if compare_fingerprint(previous_hash, fingerprint) == True:
            return True
    PREVIOUS_HASH = fingerprint
    return False


# IS_VALID GLOBAL VARIABLES AND HELPERS BELOW ----------------------------------------------------------------------------------------------------------
def is_valid(url, subdomain_count = SD_COUNT, unique_pages = U_PAGES) -> bool:
    """
    Determines if URL is valid for scraping and returns boolean.
    Has side effect of answering questions about the URL for report deliverable. Answers
    will be added to global variables.
    """

    try:
        parsed = urlparse(url)  # Breaks the url into parts.

        if (parsed.scheme not in {"http", "https"}          or
            check_valid_domain(parsed) == False             or
            check_uniqueness(parsed, unique_pages) == False ):
            return False  # if scheme or domain of the url isn't valid, or it's not a unique page, then it's not valid

        add_to_subdomain_count(parsed, subdomain_count)

        if re.match(r".*/(pdf|css|js|png|jpe&g|uploads|upload|calendar|login)/*", parsed.path.lower()):
            return False  # if the url leads to any of these tyeps of pages, it's not valid

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|/pdf/"
            + r"|ps|eps|tex|ppt|pptx|ppsx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|odc)$", parsed.path.lower())

    except TypeError:
        print("TypeError for ", parsed)
        raise


# Helper methods for is_valid()
def check_valid_domain(parsed_url) -> bool:
    """
    If not a UCI domain, return False.
    """
    valid_domains = {".ics.uci.edu", ".cs.uci.edu",
                   ".informatics.uci.edu", ".stats.uci.edu"}

    for domain in valid_domains:
        if not parsed_url.hostname:  # domain isn't valid if hostname == None
            return False
        if parsed_url.hostname.find(domain) > -1:  # domain is valid if hostname contains any string from the valid_domains set
            return True
    return False


def add_to_subdomain_count(parsed_url, subdomain_count) -> bool:
    """
    Increment subdomain count for parsed url and return if subdomain
    """
    valid_subdomains = {".ics.uci.edu"}
    for subdomain in valid_subdomains:
        if not parsed_url.hostname:  # return False if hostname == None
            return False
        if subdomain in parsed_url.hostname:  # if hostname contains a valid subdomain, normalize the url and add it to / increment it in subdomain_count
            hostname = hostname_normalization(parsed_url)
            if hostname in subdomain_count:
                subdomain_count[hostname] += 1
            else:
                subdomain_count[hostname] = 1
            subdomain_count.pop("ics.uci.edu", None) #scuffed ass solution but its okay
            with open('subdomains.txt', 'w') as f:  # note the subdomains crawled over and how often they were encountered; save this info to a separate txt file in case of server crashes/bugs crashing the program
                f.write(f"# of subdomains: {len(subdomain_count)}\n")
                for sd, freq in subdomain_count.items():
                    f.write(f"\t{sd}: {freq}\n")
            return True
    return False


def hostname_normalization(url):
    """
    Normalize url hostnames for comparison purposes and return normalized
    """
    return url.hostname.strip('www.')


def path_normalization(url):
    """
    Normalize path by removing duplicate slashes
    """
    return re.sub('/{2,}', '/', url.path)


def query_normalization(url):
    """
    Normalize url by sorting queries
    """
    return sorted(parse_qs(url.query))


def check_uniqueness(parsed_url, unique_pages):
    """
    Disregard url fragment and return True if unique.
    """
    unique = True
    for page in unique_pages:
        if (parsed_url.scheme == page.scheme                                   and
            hostname_normalization(parsed_url) == hostname_normalization(page) and
            path_normalization(parsed_url) == path_normalization(page)         and
            parsed_url.params == page.params                                   and
            query_normalization(parsed_url) == query_normalization(page)          ):
                unique = False

    if unique:
        unique_pages.add(parsed_url)
        with open('unique.txt', 'w') as f:
            f.write(f'Amount of unique pages: {len(unique_pages)}')

    return unique


