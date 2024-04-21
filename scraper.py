import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup as BS

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

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
    found_links = []
    # Make a list for storing found links
    if is_valid(resp.url):
        # Check to make sure that the current url is valid to crawl
        # Check to make sure the status of the response is good
        if resp.status != 200:
            return found_links
        else:
            # Get the html content of the page
            # Using BeautifulSoup to parse the html, and then find all the links within it
            page_content = resp.raw_response.content
            soup = BS(page_content, 'html_parser')
            for soup_url in soup.find_all('a'):
                link = soup_url.get('href')
                if link not in found_links:
                    found_links.append(link)

    return found_links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
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
        print ("TypeError for ", parsed)
        raise



# Helper methods for is_valid()
'''
Defining Uniqueness:
- avoid fragment
http://www.ics.uci.edu#aaa and http://www.ics.uci.edu#bbb are the same URL
- ALL pages found, not just ones scraped
'''
def check_valid_domain(parsed_url) -> bool:
  """If not a UCI domain, return True."""
  valid_domains = {"ics.uci.edu",
                   "cs.uci.edu",
                   "informatics.uci.edu",
                   "stats.uci.edu"}
  if parsed_url.hostname not in valid_domains:
      return False
  return True

def count_subdomains(parsed_url, subdomain_count):
  """Check for the amount of subdomains within a domain."""
  for key, value in subdomain_count.items():
    if key == parsed_url.hostname:
      subdomain_count[key] += 1
      break



def check_uniqueness(parsed_url, unique_pages):
  """Disregard url fragment and return True if unique."""
  for page in unique_pages:
    if (parsed_url.schema == page.schema      and
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
  #Define user_agent
  #Disallows
  #Sitemaps
  
  #if its under disallowed, store it in disallowed_paths

  return disallowed_paths
#returns list of disallowed paths  


def check_robot_allows(url, robot_exclusion):
  """checks if the url is not allowed based on robot.txt"""
  if url in robot_exclusion:
    return False
  return True
