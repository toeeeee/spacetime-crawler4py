import unittest
from urllib.parse import urlparse
from scraper import check_valid_domain


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


if __name__ == '__main__':
    unittest.main()
