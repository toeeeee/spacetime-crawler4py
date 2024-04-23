import re
from urllib.parse import urlparse, parse_qs
import urllib.robotparser
from bs4 import BeautifulSoup as BS


LONGEST_PAGE = None  # the page with the most number of words (not counting HTML markup)
FREQ_DICT = {}  # dict of word-freq pairs (freq: word's frequency of appearance across all sites visited)
STOP_WORDS = ["a", "about", "above", "after", "again", "against", "all", "am", "an", "and",  "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing","don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours"]  # list of words that will not be considered for the top 50 most common words
# is_valid global variables
SD_COUNT = {"ics.uci.edu": 0, "cs.uci.edu": 0,
                   "informatics.uci.edu": 0, "stats.uci.edu": 0}
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
  #if is_valid(resp.url):
    # Check to make sure that the current url is valid and the response status is good
    if resp.status != 200:
        return found_links
    else:
      # Get the html content of the page
      # Using BeautifulSoup to parse the html, and then find all the links within it
        page_content = resp.raw_response.content
        count_and_add_to_dict(resp.raw_response)
        soup = BS(page_content, 'html.parser')
        for soup_url in soup.find_all('a'):
            link = soup_url.get('href')
            if link not in found_links:
                found_links.append(link)

    return found_links

def count_and_add_to_dict(page) -> None:  # given a page, get the number of words and add words to FREQ_DICT
  global FREQ_DICT
  global LONGEST_PAGE
  global STOP_WORDS

  page_content = BS(page.content, 'html.parser')  # convert from HTML to plain text
  token = ""  # used to collect all the chars of each word in the page
  num_words = 0  # used to count the number of words in the page
  for char in page_content:
    if char.isalnum():  # since the current char is alphanumeric, continue adding chars to token
      token += char.lower()
    else:  # add the current token to the dictionary and increase word count
      if token != "":  # continue only if token isn't empty
        if token not in STOP_WORDS: num_words += 1
        if token not in FREQ_DICT:  # if word isn't in dict already, add it in
          FREQ_DICT[token] = 0
        FREQ_DICT[token] += 1  # increment frequency of the word by 1
        token = ""  # reset token to empty to start reading in the next word
  
  # check if this page is the longest page found so far
  if LONGEST_PAGE == None:  # this is the first site crawled, so this is the longest page so far
    LONGEST_PAGE = (page, num_words)  # format: (page, number of words)
  elif LONGEST_PAGE[1] < num_words:  # otherwise, compare number of words & redefine if needed
    LONGEST_PAGE = (page, num_words)

  return

def create_report() -> None:  # make the report txt file
  """
  Besides the code itself, must submit a report containing answers to the following questions:
  1. How many unique pages did you find?
  2. What is the longest page in terms of the number of words?
  3. What are the 50 most common words in the entire set of pages crawled under these domains?
  4. How many subdomains did you find in the ics.uci.edu domain?
  """
  global SD_COUNT
  global LONGEST_PAGE

  # CREDIT:(https://stackoverflow.com/questions/10695139/sort-a-list-of-tuples-by-2nd-item-integer-value)
  num_unique_pages = 0  # TODO
  top_fifty_words = sorted( [(word, freq) for word, freq in FREQ_DICT.items()], key=lambda x: x[1] )[:-50]
  pass
  top_fifty_string = ""
  for i in range(len(top_fifty_words)):
    top_fifty_string += f"\t{i}. {top_fifty_string[i][0]}: {top_fifty_string[i][1]}\n"
  num_subdomains = 0  # SD_COUNT {site/host name: count}
  for key in SD_COUNT:
    num_subdomains += SD_COUNT[key]
  # make txt file of all subdomains and counts

  with open("report.txt", "w") as file:
    file.write(f"REPORT\n\n\nNumber of unique pages found: {num_unique_pages}\n\nLongest page in terms of the number of words: {LONGEST_PAGE.url}\n\n50 most common words found:\n{top_fifty_string}\nNumber of 'ics.uci.edu' subdomains found: {num_subdomains}\n")

  return None

# IS_VALID HELPERS BELOW ----------------------------------------------------------------------------------------------------------
def is_valid(url, subdomain_count = SD_COUNT, unique_pages = U_PAGES) -> bool:
    """Determines if URL is valid for scraping and returns boolean.
    Has side effect of answering questions about the URL for report deliverable. Answers
    will be added to global variables."""

    try:
        parsed = urlparse(url, allow_fragments = False)  # Breaks the url into parts.

        if (parsed.scheme not in {"http", "https"} or
                check_valid_domain(parsed) == False or
                check_uniqueness(parsed, unique_pages) == False or
                check_robot_file(parsed, url) == False):
            return False

        count_subdomains(parsed, subdomain_count)

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
        print("TypeError for ", parsed)
        raise

# Helper methods for is_valid()
def check_valid_domain(parsed_url) -> bool:
  """If not a UCI domain, return True."""
  valid_domains = {"ics.uci.edu",
                   "cs.uci.edu",
                   "informatics.uci.edu",
                   "stats.uci.edu"}
  for domain in valid_domains:
      if domain in parsed_url.hostname:
        return True
  return False

def count_subdomains(parsed_url, subdomain_count):
  """Check for the amount of subdomains within a domain."""
  for key, value in subdomain_count.items():
    if is_subdomain(parsed_url.hostname, key):
      subdomain_count[key] += 1
      break


def hostname_normalization(url):
    """Normalize url hostnamess for comparison purposes and return normalized"""
    return url.hostname.strip('www.')


def path_normalization(url):
    """Normalize path by removing duplicate slashes"""
    return re.sub('/{2,}', '/', url.path)


def query_normalization(url):
    """Normalize url by sorting queries"""
    return sorted(parse_qs(url.query))


def is_subdomain(parsed_domain, domain_bank):
  if domain_bank == parsed_domain:
    return True
  return False


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
  

def check_robot_file(parsed_url, url):
  robot_url = parsed_url.scheme + "://" + parsed_url.hostname + "/robots.txt"
  r_parse = urllib.robotparser.RobotFileParser()
  r_parse.set_url(robot_url)
  r_parse.read()
  if r_parse.can_fetch("IR US24 51886940,28685686,62616299,32303304", url):
    return True
  return False
