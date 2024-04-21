import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup as BS


CURR_PAGE = None  # global variable to hold raw contents of the last site crawled over
LONGEST_PAGE = None  # the page with the most number of words (not counting HTML markup)
FREQ_DICT = {}  # dict of word-freq pairs (freq: word's frequency of appearance across all sites visited)
RAW_RESPONSES = []  # list of raw_responses of sites crawled over
STOP_WORDS = ["a", "about", "above", "after", "again", "against", "all", "am", "an", "and",  "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing","don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours"] # list of words that will not be considered for the top 50 most common words


def scraper(url, resp) -> list:
    links = extract_next_links(url, resp)
    links_list = []
    for i in range(len(links)):
      if is_valid(links[i]):  # if link is_valid: append to links_list; check if it's the longest page; and add all of the site's words to FREQ_DICT
        links_list.append(links[i])
        
        # add all words on the site to the dictionary and count up number of words
        page_text = BS(RAW_RESPONSES[i].content, 'html.parser')  # get plain text of html contents of the page
        token = ""
        num_words = 0
        for char in page_text:
          if not char.isalnum():
            if token != "":  # continue only if token isn't empty
              num_words += 1
              if token not in FREQ_DICT:  # add into FREQ_DICT
                FREQ_DICT[token] = 0  # if word isn't in dict already, add it in
              FREQ_DICT[token] += 1  # increment frequency by 1
              token = ""  # reset token to empty to start reading in the next word
          else:  # since the current char is alphanumeric, for-loop must be on a word; continue adding chars to token
            token += char
        
        if LONGEST_PAGE == None:  # this must be the first site crawled over, so this is the longest page found so far
          LONGEST_PAGE = (CURR_PAGE, num_words)  # (page, number of words)
        elif LONGEST_PAGE[1] < num_words:  # otherwise, compare number of words
          LONGEST_PAGE = (CURR_PAGE, num_words)
    
    # CREDIT: I looked up how to sort a list of tuples based on the second element of each tuple (https://stackoverflow.com/questions/10695139/sort-a-list-of-tuples-by-2nd-item-integer-value)
    top_fifty_words = sorted( [(word, freq) for word, freq in FREQ_DICT.items()], key=lambda x: x[1] )[:50]
    return links_list

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
  if is_valid(resp.url):
    # Check to make sure that the current url is valid and the response status is good
    if resp.status != 200:
      return found_links
    else:
      # Get the html content of the page
      # Using BeautifulSoup to parse the html, and then find all the links within it
      RAW_RESPONSES.append(resp.raw_response)
      page_content = resp.raw_response.content
      CURR_PAGE = resp.raw_response
      soup = BS(page_content, 'html_parser')
      for soup_url in soup.find_all('a'):
        link = soup_url.get('href')
        if link not in found_links:
          found_links.append(link)

  return found_links


sd_count = {"ics.uci.edu": 0, "cs.uci.edu": 0,
                   "informatics.uci.edu": 0, "stats.uci.edu": 0}
u_pages = set()  # Parsed urls
def is_valid(url, subdomain_count = sd_count, unique_pages = u_pages) -> bool:
    """Determines if URL is valid for scraping and returns boolean.
    Has side effect of answering questions about the URL for report deliverable. Answers
    will be added to global variables."""
    robot_exclusion = parse_for_robot(url)  # checks the url for robots.txt

    try:
        parsed = urlparse(url, allow_fragments = False)  # Breaks the url into parts.

        robot_exclusion = parse_for_robot(url)  # checks the url for robots.txt
        if (parsed.scheme not in {"http", "https"} or
                check_valid_domain(parsed) == False or
                check_uniqueness(parsed, unique_pages) == False or
                check_robot_allows(parsed, robot_exclusion) == False):
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
'''
Defining Uniqueness:
- avoid fragment
https://www.ics.uci.edu#aaa and https://www.ics.uci.edu#bbb are the same URL
- ALL pages found, not just ones scraped
'''
def check_valid_domain(parsed_url) -> bool:
  """If not a UCI domain, return True."""
  valid_domains = {"ics.uci.edu",
                   "cs.uci.edu",
                   "informatics.uci.edu",
                    "stats.uci.edu"
                    ".ics.uci.edu",
                    ".cs.uci.edu",
                     ".informatics.uci.edu",
                     ".stats.uci.edu"
                    }
  for domain in valid_domains:
      if domain in parsed_url.hostname:
          return True

  return False

def count_subdomains(parsed_url, subdomain_count):
  """Check for the amount of subdomains within a domain."""
  for key, value in subdomain_count.items():
    if key == parsed_url.hostname:
      subdomain_count[key] += 1
      break

def check_uniqueness(parsed_url, unique_pages):
  """Disregard url fragment and return True if unique."""
  for page in unique_pages:
    if (parsed_url.scheme == page.scheme      and
        parsed_url.hostname == page.hostname  and
        parsed_url.path == page.path          and
        parsed_url.params == page.params      and
        parsed_url.query == page.query           ):
      return False
    unique_pages.add(page)
    return True
  
def parse_for_robot(parsed_url):
  """converts url to robots.txt and stores robot_exclusion"""
  robot_url = parsed_url.scheme + "://" + parsed_url.hostname + "/robots.txt"
  disallowed_paths = ()
  '''
  use robot_url, and download that file
  gather data from robots.txt
  '''
  # Define user_agent
  # Disallows
  # Sitemaps
  
  # if its under disallowed, store it in disallowed_paths

  return disallowed_paths  # returns list of disallowed paths  

def check_robot_allows(url, robot_exclusion):
  """checks if the url is not allowed based on robot.txt"""
  if url in robot_exclusion:
    return False
  return True
