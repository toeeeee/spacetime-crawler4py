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


def scraper(url, resp) -> list:
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]


def extract_next_links(url, resp):
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
        
        # pre-process page_content for same-page and similar-page detection
        plain_text = str(soup.get_text())  # plain text of the page contents (gets rid of HTML elements)
        plain_text = plain_text.strip().lower()  # remove leading & trailing whitespace, & lowercase all chars
        normalized_text = re.sub(r'\s+', ' ', plain_text)  # sequences of whitespace replaced with one space
        """CREDIT: had trouble with getting hash, until I found this page that used .encode() method: https://stackoverflow.com/questions/42200117/unable-to-get-a-sha256-hash-of-a-string"""
        hs = hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()  # get the sha-256 hash of the page's contents

        # SAME-PAGE DETECTION
        """TODO: similar-page detection and confirming if same-page detection code below works"""
        # store the hash into an SQL database, checking to make sure the same hash doesn't already exist
        #   If it does exist, then this is an exact duplicate page
        db = sqlite3.connect('hashes.db')  # implicitly create 'hashes.db' database if it doesn't exist, and create a connection to the db in the current working directory
        cur = db.cursor()  # make a cursor to execute SQL statements and fetch results from SQL queries
        cur.execute("CREATE TABLE pages(hash)")  # create the 'pages' table of hash values
        cur.execute("SELECT hash FROM pages WHERE hash=?", (hs))  # check if hash already exists in table
        if cur.fetchone():  # hash already in db, meaning this is a duplicate page; skip it
            return found_links
        else:
            cur.execute("INSERT INTO pages VALUES ?", (hs))  # insert the page's hs (hash value) into the 'pages' table SQL database
            cur.commit()  # commit the change into the database

            tokens = tokenizer(normalized_text)  # tokenize the current page

            if len(tokens) < 25:  # if the page is empty/low content
                return found_links

            update_freq(tokens)  # update the token frequency dictionary
            update_longest_page(normalized_text, resp.raw_response.url)  # update the longest page found
            for soup_url in soup.find_all('a'):
                link = soup_url.get('href')
                if link not in found_links:
                    found_links.append(link)

    return found_links


#SCRAPER FUNCTIONS----------------------------------------------------------------

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


#IS_VALID GLOBAL VARIABLES AND HELPERS BELOW ----------------------------------------------------------------------------------------------------------
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


