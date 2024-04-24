from threading import Thread

from inspect import getsource

import requests.exceptions
import urllib3.exceptions

from utils.download import download
from utils import get_logger
import scraper
import time


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            try:
                resp = download(tbd_url, self.config, self.logger) #
            except ConnectionRefusedError:
                self.logger(f"Connection refused")
                time.sleep(120)
                continue
            except urllib3.exceptions.ConnectionError:
                self.logger(f"Connection error")
                time.sleep(120)
                continue
            except urllib3.exceptions.NewConnectionError:
                self.logger(f"Cant open new connection error")
                time.sleep(120)
                continue
            except urllib3.exceptions.MaxRetryError:
                self.logger(f"Reached max attempts")
                time.sleep(120)
                continue
            except requests.exceptions.ConnectionError:
                self.logger(f"Reached connection error for requests")
                time.sleep(120)
                continue
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
