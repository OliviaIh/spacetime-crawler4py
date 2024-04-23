import re
from urllib.parse import urlparse
import urllib.request
import time
from bs4 import BeautifulSoup
from tokenizer import tokenize, computeWordFrequencies
from simhash import simhash, is_near_duplicate
from collections import defaultdict

visited_and_words = {}  # key = url, val = # of words on page
word_frequencies = defaultdict(int)

stopwords = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers",
    "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've",
    "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more",
    "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only",
    "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't",
    "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than",
    "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there", "there's",
    "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to",
    "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've",
    "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who",
    "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll",
    "you're", "you've", "your", "yours", "yourself", "yourselves"
    }


# don't add visited links to frontier
def scraper(url, resp):
    # DONE:
    #   - determine low information value (min: 300 words or so or call is_valid in extract_next_links)
    #   - check this requirement: detect and avoid crawling very large files, especially if they have low information value
    # TO DOS:
    #   - check redirect works properly
    #   - simhash/compare similarities with no information (Detect and avoid sets of similar pages with no information)

    links = extract_next_links(url, resp)
    # return [link for link in links if is_valid(link)]
    return links

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

    # ParseResult(scheme='http', netloc='www.openlab.ics.uci.edu', path='', params='', query='', fragment='')
    delay = _check_politness(url)
    if delay < 0:
        return
    sleep(delay) # maintains politness before parsing url
    parsed_url = urlparse(url)

    hyperlinks_list = []
    if (resp.status < 400 and resp.status >= 200):
        crawlURL = url

        # check if page already visited
        if crawlURL in visited_and_words:
            return hyperlinks_list
        
        # if the url is a redirect code, do not add it to the visited_and_words, but will continue to parse the content
        if resp.status < 300:
            visited_and_words[url] = 0

        # scrape text from soup
        tokens = _get_content(resp.raw_response.content)

        # check if the url is dead (no tokens), returns the hyperlink list
        if len(tokens) == 0:
            return hyperlinks_list
            
        # count word frequencies from tokens
        freqs = computeWordFrequencies(tokens)
        print(f"UNIQUE TOKENS = {len(freqs.items())}")
        # print(freqs)

        # check if page is too small (<300 unique tokens) or too large (>15,000 unique tokens)
        unique_tokens = len(freqs.keys())
        if unique_tokens < 300 or unique_tokens > 15000:
            print('TOO SMALL/LARGE')
            return hyperlinks_list

        # print(tokens)
        visited_and_words[url] = len(tokens)

        # add to word_frequencies
        for word in freqs:
            if word not in stopwords:
                word_frequencies[word] += freqs[word]
                
        # scrape links from soup
        for link in soup.find_all('a'):
            try:
                # print("LINK: " + link)
                href = link.get('href')
                # print(href)
                new_link = ""

                if not href or not is_valid(href):
                    continue
                
                if href[:2] == "//":
                    # if link href starts with //, add parsed_url.scheme + ':' to the front
                    # <a href="//www.ics.uci.edu/ugrad/livechat.php">
                    new_link = parsed_url.scheme + ':' + href
                elif href[0] == "/":
                    # if link href starts with /, it's a relative link --> add base URL to front
                    # <scheme>://<netloc><link href>
                    new_link = parsed_url.scheme + '://' + parsed_url.netloc + href
                elif href[0] == "#":
                    # if link href starts with #, it's a fragment of url --> do nothing
                    # #carouselExampleIndicators
                    # <a href="#" id="back2Top" title="Back to top"> 
                    continue
                elif href.find('://') == -1:
                    if href.find(':') == -1:
                        # employment/employ_faculty.php
                        new_link = parsed_url.scheme + '://' + parsed_url.netloc + '/' + href
                    else:
                        # mailto:ichair@ics.uci.edu
                        # tel: ...
                        # data ...
                        # urn:isbn:0451450523
                        continue
                else:
                    # https://campusgroups.uci.edu/rsvp?id=1841688
                    new_link = href
                
                # check if there is a fragment (aka check if contains #); if so, strip from the url
                fragment_index = new_link.find("#") 
                if fragment_index != -1:
                    new_link = new_link[:fragment_index]

                # add new_link to frontier
                new_resp = download(new_link, self.config, self.logger)
                new_link_tokens = _get_content(new_resp.raw_response.content)

                simhash1 = simhash(tokens)
                simhash2 = simhash(new_link_tokens)
                
                if is_near_duplicate(simhash1, simhash2, 5):
                    hyperlinks_list.append(new_link)

            except TypeError:
                print("HREF is null")
    
    # else check error if status is not 200

    return hyperlinks_list

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        # print(parsed)

        if parsed.scheme not in set(["http", "https"]):
            return False
        
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False
        
        # parsed.netloc must be either *.ics.uci.edu/*, *.cs.uci.edu/*, *.informatics.uci.edu/*, *.stat.uci.edu/*
        
        valid_urls = [".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu"]
        for url in valid_urls:
            if (re.search(url, parsed.netloc)):
                return True
        return False
                
    except TypeError:
        print ("TypeError for ", parsed)
        raise

def _get_content(web_content):
    soup = BeautifulSoup(web_content, 'html.parser')
    tokens = soup.get_text().split('\n') 
    tokens = tokenize([t for t in tokens if len(t.strip()) > 0])
    return tokens

def _check_politness(url):
    # checks if the url has a robots.txt file and returns a time-delay to maintain politness
    url += "/robots.txt" if url[-1] != "/" else "robots.txt"

    # make http get request
    try:
        # from https://docs.python.org/3/howto/urllib2.html
        with urllib.request.urlopen('http://python.org/') as response:
            for line in response: 
                # check the allow/disallow
                if line.contains("IR US24"):
                    return -1
                if line.contains("Crawl-delay"):
                    # return the value

            return 1
    except urllib.error.URLError as e: # is this the correct error type?
        return 1






if __name__ == "__main__":
    print(is_valid("http://www.openlab.ics.uci.edu"))