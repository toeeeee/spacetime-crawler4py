import unittest
from urllib.parse import urlparse
from scraper import check_valid_domain, check_uniqueness


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

if __name__ == '__main__':
    unittest.main()
