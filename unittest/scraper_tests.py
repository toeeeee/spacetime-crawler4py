import unittest
from urllib.parse import urlparse
from scraper import check_valid_domain, add_to_subdomain_count, check_uniqueness

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

    def test_subdomain_checker(self):
        sd_count = {}
        parsed = urlparse('https://archive.ics.uci.edu/')
        self.assertTrue(add_to_subdomain_count(parsed, sd_count))
        parsed = urlparse("https://archive.ics.uci.edu/dataset/53/iris")
        self.assertTrue(add_to_subdomain_count(parsed, sd_count))
        parsed = urlparse("https://ics.uci.edu/~dillenco/ics6d")
        self.assertFalse(add_to_subdomain_count(parsed, sd_count))

        # Subdomain counting
        self.assertEqual(2, sd_count["archive.ics.uci.edu"])

if __name__ == '__main__':
    unittest.main()
