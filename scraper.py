import re
from urllib.parse import urlparse, parse_qs
import urllib.robotparser
from bs4 import BeautifulSoup as BS



# SCRAPER GLOBAL VARIABLES
LONGEST_PAGE = ()  # ( format: page, number of words ) the page with greatest number of words
FREQ_DICT = {}  # dict of word-frequency pairs
STOP_WORDS = ["a", "about", "above", "after", "again", "against", "all", "am", "an", "and",  "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing","don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours"] # list of words that will not be considered for the top 50 most common words
SD_COUNT = {} # format: {"subdomain": count, ...}
U_PAGES = set()  # Parsed urls

#
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
  #if is_valid(resp.url):
    # Check to make sure that the current url is valid and the response status is good
    if resp.status != 200:
        return found_links
    else:
      # Get the html content of the page
      # Using BeautifulSoup to parse the html, and then find all the links within it
        page_content = resp.raw_response.content
        soup = BS(page_content, 'html.parser')
        tokens = tokenizer(str(soup.get_text()))  # tokenize the current page
        if len(tokens) == 0:
            return
        update_freq(tokens)  # update the token frequency dictionary
        update_longest_page(str(soup.get_text()), resp.raw_response.url)  # update the longest page found
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

    with open('top50.txt', 'w') as f:
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

    with open('longest.txt', 'w') as f:
        f.write(f"Longest page: {LONGEST_PAGE[0]}\nLength: {LONGEST_PAGE[1]}")


#IS_VALID GLOBAL VARIABLES AND HELPERS BELOW ----------------------------------------------------------------------------------------------------------
def is_valid(url, subdomain_count = SD_COUNT, unique_pages = U_PAGES) -> bool:

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
            with open('subdomains.txt', 'w') as f:
                f.write(f"# of subdomains: {len(subdomain_count)}\n")
                for sd, freq in subdomain_count.items():
                    f.write(f"\t{sd}: {freq}\n")
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
        with open('unique.txt', 'w') as f:
            f.write(f'Amount of unique pages: {len(unique_pages)}')

    return unique

