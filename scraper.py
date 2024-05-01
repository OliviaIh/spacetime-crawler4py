import re
from urllib.parse import urlparse
import urllib.robotparser
from simhash import Simhash
from time import sleep
from bs4 import BeautifulSoup
from tokenizer import tokenize, computeWordFrequencies
from collections import defaultdict

visited_and_words = {}  # key = url, val = # of words on page
simhash_values = []
word_frequencies = defaultdict(int) # key = word, val = frequency
num_visited = int()

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
    return extract_next_links(url, resp)

def extract_next_links(url, resp):
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    # ParseResult(scheme='http', netloc='www.openlab.ics.uci.edu', path='', params='', query='', fragment='')
    parsed_url = urlparse(url)
    
    hyperlinks_list = []
    politeness_delay = None
    
    # parse robots.txt to check for politness delay
    try:
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        robots = urllib.robotparser.RobotFileParser()
        robots.set_url(robots_url)
        robots.read()
        
        # if url can be fetched, request politness delay in seconds
        if robots.can_fetch("*", url):
            robots_delay = robots.request_rate("*")
            # if the delay does not eexist, default to 0.5 from config.ini
            politeness_delay = robots_delay.seconds if robots_delay else 0.5
            print('POLITENESS DELAY: ' + str(politeness_delay))
        
        # url cannot be scraped, return
        else:
            return hyperlinks_list, politeness_delay
        
    except Exception as e:
        print(e)
    
    # checks if page is responsive 
    if (resp.status < 400 and resp.status >= 200):
        crawlURL = url

        # check if page already visited
        if crawlURL in visited_and_words:
            return hyperlinks_list, politeness_delay

        # scrape text from soup
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        
        # retrieve tokens from text
        tokens = soup.get_text().split('\n') 
        tokens = tokenize([t for t in tokens if len(t.strip()) > 0])

        # check if the url is dead (no tokens), returns the hyperlink list and politness delay
        if len(tokens) == 0:
            return hyperlinks_list, politeness_delay
            
        # count word frequencies from tokens
        freqs = computeWordFrequencies(tokens)
        print(f"UNIQUE TOKENS = {len(freqs.items())}")

        # check if page is too small (<100 unique tokens) or too large (>15,000 unique tokens)
        unique_tokens = len(freqs.keys())
        if unique_tokens < 100 or unique_tokens > 15000:
            print('TOO SMALL/LARGE')
            return hyperlinks_list, politeness_delay

        # if the url is a redirect code, do not add it to the visited_and_words, but will continue to parse the content
        if resp.status < 300:
            visited_and_words[url] = len(tokens)
            global num_visited
            num_visited += 1

        # add to word_frequencies
        for word in freqs:
            if word not in stopwords:
                word_frequencies[word] += freqs[word]
        
        # check if similar to previous pages using Simhash
        current = Simhash(tokens).value
        if current not in simhash_values:
            simhash_values.append(current)
        else:
            return hyperlinks_list, politeness_delay     # url is similar to previous
                
        # scrape links from soup
        for link in soup.find_all('a'):
            try:
                href = link.get('href')
                new_link = ""

                if not href or not is_valid(href):
                    continue
                
                if href[:2] == "//":
                    # if link href starts with //, add parsed_url.scheme + ':' to the front
                        # ex: <a href="//www.ics.uci.edu/ugrad/livechat.php">
                    new_link = parsed_url.scheme + ':' + href
                elif href[0] == "/":
                    # if link href starts with /, it's a relative link --> add base URL to front
                        # ex: <scheme>://<netloc><link href>
                    new_link = parsed_url.scheme + '://' + parsed_url.netloc + href
                elif href[0] == "#":
                    # if link href starts with #, it's a fragment of url --> do nothing
                        # ex: #carouselExampleIndicators
                        #     <a href="#" id="back2Top" title="Back to top"> 
                    continue
                elif href.find('://') == -1:
                    if href.find(':') == -1:
                        # ex: employment/employ_faculty.php
                        new_link = parsed_url.scheme + '://' + parsed_url.netloc + '/' + href
                    else:
                        # ex: mailto:ichair@ics.uci.edu
                        #     tel: ...
                        #     data ...
                        #     urn:isbn:0451450523
                        continue
                else:
                    # ex: https://campusgroups.uci.edu/rsvp?id=1841688
                    new_link = href
                
                # check if there is a fragment (aka check if contains #); if so, strip from the url
                fragment_index = new_link.find("#") 
                if fragment_index != -1:
                    new_link = new_link[:fragment_index]

                # add new_link to frontier
                hyperlinks_list.append(new_link)
            
            except TypeError as e:
                print(e)
    
    # else check error if status is not 200
    return hyperlinks_list, politeness_delay

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)

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



if __name__ == "__main__":
    print(is_valid("http://www.openlab.ics.uci.edu"))