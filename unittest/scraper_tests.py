import unittest
from urllib.parse import urlparse
from scraper import check_valid_domain
from scraper import is_subdomain
from scraper import count_subdomains

class ScraperHelperTestCase(unittest.TestCase):
    def test_domain_validity(self):
        archive = urlparse('https://archive.ics.uci.edu/')
        goog = urlparse('https://www.google.com')
        duck = urlparse('https://duckduckgo.com/')
        sixd = urlparse('https://ics.uci.edu/~dillenco/ics6d')
        self.assertTrue(check_valid_domain(archive))
        self.assertTrue(check_valid_domain(sixd))
        self.assertFalse(check_valid_domain(goog))
        self.assertFalse(check_valid_domain(duck))

    def test_uniqueness_validity(self):
        base = urlparse('https://ics.uci.edu/~dillenco/ics6d/')
        parsed_with_fragment = urlparse('https://ics.uci.edu/~dillenco/ics6d/#coursedescription')
        nonnormal = urlparse('https://www.ics.uci.edu/////////////////~dillenco/ics6d//////////////////////////#coursestaff')
        newsite = urlparse('https://ics.uci.edu/~dillenco/ics6d/testing/')
        unique_pgs = set()
        unique_pgs.add(base)
        self.assertFalse(check_uniqueness(parsed_with_fragment, unique_pgs))
        self.assertFalse(check_uniqueness(nonnormal, unique_pgs))
        self.assertEqual(unique_pgs, {base})
        self.assertTrue(check_uniqueness(newsite, unique_pgs))
        self.assertEqual(unique_pgs, {base, newsite})

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
