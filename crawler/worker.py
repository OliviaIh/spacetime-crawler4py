from threading import Thread

from inspect import getsource
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
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)

        with open('results.txt', 'a') as f:
            sorted_visited_and_words = sorted(scraper.visited_and_words.items(), key=lambda item: item[1], reverse=True)
            print(sorted_visited_and_words)
            for item in sorted_visited_and_words:
                f.write(f"{item[0]}: {item[1]}\n")
            
            f.write('\nWORD FREQUENCIES\n')

            sorted_word_frequencies = sorted(scraper.word_frequencies.items(), key=lambda item: item[1], reverse=True)
            print(sorted_word_frequencies)
            for item in sorted_word_frequencies:
                f.write(f"{item[0]}: {item[1]}\n")