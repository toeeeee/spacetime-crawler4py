import unittest
from urllib.parse import urlparse
from scraper import check_valid_domain
from scraper import is_subdomain
from scraper import count_subdomains

class ScraperHelperTestCase(unittest.TestCase):
    def test_domain_validity(self):
        parsed = urlparse('https://archive.ics.uci.edu/', allow_fragments = False)
        parsed2 = urlparse('https://www.google.com', allow_fragments = False)
        parsed3 = urlparse('https://www.duckduckgo.com/', allow_fragments = False)
        parsed4 = urlparse('https://ics.uci.edu/~dillenco/ics6d', allow_fragments = False)
        self.assertEqual(True, check_valid_domain(parsed))
        self.assertEqual(True, check_valid_domain(parsed4))
        self.assertEqual(False, check_valid_domain(parsed2))
        self.assertEqual(False, check_valid_domain(parsed3))

    #robot testing

    #uniqueness testing

    #subdomain testing
    def test_subdomain(self):
        domain_bank = ("ics.uci.edu",
                   "cs.uci.edu",
                   "informatics.uci.edu",
                    "stats.uci.edu"
                    ".ics.uci.edu",
                    ".cs.uci.edu",
                     ".informatics.uci.edu",
                     ".stats.uci.edu")
        
        self.assertTrue(is_subdomain("https://archive.ics.uci.edu/",domain_bank))
        self.assertTrue(is_subdomain("https://ics.uci.edu/~dillenco/ics6d", domain_bank))
    #subdomain counting
        counter = 0
        parsed_url = "https://archive.ics.uci.edu/"
        parsed_url2 = "https://ics.uci.edu/~dillenco/ics6d"
        self.assertEqual(1, count_subdomains(parsed_url, counter))
        self.assertEqual(2, count_subdomains(parsed_url2, counter))

if __name__ == '__main__':
    unittest.main()
