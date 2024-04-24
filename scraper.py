import re
from urllib.parse import urlparse, parse_qs
import urllib.robotparser
from bs4 import BeautifulSoup as BS



# SCRAPER GLOBAL VARIABLES
CURR_PAGE = None  # global variable to hold raw contents of the last site crawled over
LONGEST_PAGE = None  # the page with the most number of words (not counting HTML markup)
LONGEST_PAGE_LENGTH = None
FREQ_DICT = {}  # dict of word-freq pairs (freq: word's frequency of appearance across all sites visited)
RAW_RESPONSES = []  # list of raw_responses of sites crawled over
PAGES = []
STOP_WORDS = ["a", "about", "above", "after", "again", "against", "all", "am", "an", "and",  "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing","don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours"] # list of words that will not be considered for the top 50 most common words
sd_count = {} # looks like "subdomain": count
u_pages = set()  # Parsed urls


def scraper(url, resp) -> list:
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]


def extract_next_links(url, resp):
    global CURR_PAGE
    global PAGES
  # url: the URL that was used to get the page
  # resp.url: the actual url of the page
  # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
  # resp.error: when status is not 200, you can check the error here, if needed.
  # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
  #         resp.raw_response.url: the url, again
  #         resp.raw_response.content: the content of the page!
  # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    found_links = [] # a list for storing found links
  #if is_valid(resp.url):
    # Check to make sure that the current url is valid and the response status is good
    if resp.status != 200:
        return found_links
    else:
      # Get the html content of the page
      # Using BeautifulSoup to parse the html, and then find all the links within it
        RAW_RESPONSES.append(resp.raw_response)
        page_content = resp.raw_response.content
        tokens = tokenizer(page_content) #tokenize the current page
        #if there's no data on the page
        if tokens == len(tokens):
            return
        update_freq(tokens) #update the token frequency dictionary
        #CURR_PAGE = resp.raw_response.url
        update_longest_page(page_content, resp.raw_response.url) #update the longest page found

        soup = BS(page_content, 'html.parser')
        for soup_url in soup.find_all('a'):
            link = soup_url.get('href')
            if link not in found_links:
                found_links.append(link)
                PAGES.append(link)

    return found_links


#SCRAPER FUNCTIONS----------------------------------------------------------------

def tokenizer(content, allow_stop_words=False) -> list:
    #tokenizer for page content
    tokens = []
    new_token = ""
    for char in content:
        text = str(char)
        if not text:
            if not allow_stop_words:
                if new_token and new_token not in STOP_WORDS:
                    tokens.append(new_token)
                    break
            else:
                if new_token:
                    tokens.append(new_token)
                    break
        if text.lower().isalnum():
            new_token += text.lower()
        else:
            if not allow_stop_words:
                if new_token and new_token not in STOP_WORDS:
                    tokens.append(new_token)
            else:
                if new_token:
                    tokens.append(new_token)
        new_token = ""
    return tokens

def update_freq(tokens) -> None:
    #updates the global FREQ_DICT dictionary
    global FREQ_DICT
    for token in tokens:
        try:
            FREQ_DICT[token] += 1
        except KeyError:
            FREQ_DICT[token] = 1

def update_longest_page(content, page) -> None:
    #Update the longest page found using global variables
    global LONGEST_PAGE
    global LONGEST_PAGE_LENGTH

    curr_len = len(tokenizer(content, allow_stop_words=True))

    if LONGEST_PAGE is None:
        LONGEST_PAGE = page
        LONGEST_PAGE_LENGTH = curr_len
    else:
        if curr_len > LONGEST_PAGE_LENGTH:
            LONGEST_PAGE = page
            LONGEST_PAGE_LENGTH = curr_len

def create_report() -> None:
    """Creates a report on pages scraped"""
    global sd_count
    global LONGEST_PAGE

    with open('report.txt', 'w') as f:
        f.write("REPORT OF FINAL SCRAPER FINDINGS:\n\n")

        # Unique pages (from most common to least)
        f.write("Top 50 Words:\n")
        items = sorted(FREQ_DICT.items(), key=lambda token: token[1], reverse=True)
        for item in items:
            f.write(f"{item[0]}: {item[1]}\n")

        # What is the longest page in terms of words?
        f.write("Longest Page:\n")
        f.write(f"{LONGEST_PAGE}\n")
        f.write(f"Length: {LONGEST_PAGE_LENGTH}\n\n")


        # How many subdomains did you find in ics.uci.edu and their count
        sd_count = sorted(sd_count.items(), key=lambda x: x[0])
        count = 0
        f.write("Subdomain list:\n")
        for subdomain, subdomain_count in sd_count:
            f.write(f"{subdomain}: {subdomain_count}\n")
            count += 1

        f.write(f"\nAMOUNT OF SUBDOMAINS: {count}")



#IS_VALID GLOBAL VARIABLES AND HELPERS BELOW ----------------------------------------------------------------------------------------------------------
def is_valid(url, subdomain_count = sd_count, unique_pages = u_pages) -> bool:
    """Determines if URL is valid for scraping and returns boolean.
    Has side effect of answering questions about the URL for report deliverable. Answers
    will be added to global variables."""

    try:
        parsed = urlparse(url)  # Breaks the url into parts.

        if (parsed.scheme not in {"http", "https"}          or
            check_valid_domain(parsed) == False             or
            check_uniqueness(parsed, unique_pages) == False ):
            return False

        add_to_subdomain_count(parsed, subdomain_count)

        if re.match(r".*/(pdf|css|js|png|jpe&g|uploads|upload|calendar|login)/*", parsed.path.lower()):
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|/pdf/"
            + r"|ps|eps|tex|ppt|pptx|ppsx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print("TypeError for ", parsed)
        raise


# Helper methods for is_valid()
def check_valid_domain(parsed_url) -> bool:
  """If not a UCI domain, return False."""
  valid_domains = {".ics.uci.edu", ".cs.uci.edu",
                   ".informatics.uci.edu", ".stats.uci.edu"}

  for domain in valid_domains:
      if not parsed_url.hostname:
        return False
      if parsed_url.hostname.find(domain) > -1:
        #print("found: " + domain + "in " + parsed_url.hostname)
        return True
  return False



def add_to_subdomain_count(parsed_url, subdomain_count) -> bool:
    """Increment subdomain count for parsed url and return if subdomain"""
    valid_subdomains = {".ics.uci.edu"}
    for subdomain in valid_subdomains:
        if not parsed_url.hostname:
            return False
        if subdomain in parsed_url.hostname:
            hostname = hostname_normalization(parsed_url)
            if hostname in subdomain_count:
                subdomain_count[hostname] += 1
            else:
                subdomain_count[hostname] = 1
            return True
    return False


def hostname_normalization(url):
    """Normalize url hostnamess for comparison purposes and return normalized"""
    return url.hostname.strip('www.')


def path_normalization(url):
    """Normalize path by removing duplicate slashes"""
    return re.sub('/{2,}', '/', url.path)


def query_normalization(url):
    """Normalize url by sorting queries"""
    return sorted(parse_qs(url.query))


def check_uniqueness(parsed_url, unique_pages):
    """Disregard url fragment and return True if unique."""
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

    return unique