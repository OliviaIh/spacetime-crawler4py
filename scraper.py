import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

def scraper(url, resp):
    print("URL: " + url)
    print("Raw_Response.content: " + str(resp.raw_response.content)) 
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

    # ParseResult(scheme='http', netloc='www.openlab.ics.uci.edu', path='', params='', query='', fragment='')
    parsed_url = urlparse(url)

    hyperlinks_list = []
    if (resp.status == 200):
        
        # scrape links from resp.raw_response.content

        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        
        for link in soup.find_all('a'):
            href = link.get('href')
            print(href)
            new_link = ""
            
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
    
            hyperlinks_list.append(new_link)
    
    # else check error if status is not 200

    return hyperlinks_list

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        print(parsed)

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