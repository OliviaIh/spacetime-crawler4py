from collections import defaultdict
from urllib.parse import urlparse

def generate_report():
    unique_pages = 0
    longest_page = ""
    word_frequencies_mode = False
    subdomain_list = defaultdict(int)
    
    with open('report.txt', 'w') as report:
        with open('results.txt', 'r') as results:
            for line in results:
                # break line up into url/word and count
                if line != "WORD COUNTS\n" and line != "WORD FREQUENCIES\n" and line != '\n':
                    item, count = line.split(': ')

                # get page with highest number of words
                if unique_pages == 1:
                    longest_page = (item, count)
                
                # begin retrieving the 50 most common words
                if line == "WORD FREQUENCIES\n":
                    word_frequencies_mode = True
                    log_msg = "TOP 50 COMMON WORDS:\n"
                    print(log_msg)
                    report.write(log_msg)

                # if still going through url/wordcount pairs, increment unique page count and check for ics.uci.edu subdomain
                if not word_frequencies_mode and line != '\n':
                    unique_pages += 1
                    if line != "WORD COUNTS\n" and "ics.uci.edu" in item:
                        # ParseResult(scheme='http', netloc='www.openlab.ics.uci.edu', path='', params='', query='', fragment='')
                        parsed_url = urlparse(item)
                        subdomain = f"http://{parsed_url.netloc.removeprefix('www.')}"
                        subdomain_list[subdomain] += 1
            # in word/frequency count pairs --> print it out
                else:
                    if line != "WORD FREQUENCIES\n":
                        log_msg = f"\t{line}"
                        print(log_msg)
                        report.write(log_msg)

    
        # How many unique pages did you find?
        unique_pages -= 1   # account for counting the WORD COUNTS header
        log_msg = f"Number of unique pages: {unique_pages}"
        print(log_msg)
        report.write(f'\n{log_msg}\n')

        # What is the longest page in terms of the number of words?
        log_msg = f"The longest page in terms of number of words is {longest_page[0]} with {longest_page[1]} words."
        print(log_msg)
        report.write(f'\n{log_msg}\n')

        # What are the 50 most common words in the entire set of pages crawled under these domains ?
        # printed above in the for loop
        
        # How many subdomains did you find in the ics.uci.edu domain? Submit the list of subdomains 
        # ordered alphabetically and the number of unique pages detected in each subdomain.
        subdomains_sorted = sorted(subdomain_list.items(), key=lambda x: x[0])
        
        log_msg = f"The number of ics.uci.edu subdomains is {len(subdomains_sorted)}."
        print(log_msg)
        report.write(f'\n{log_msg}\n')

        log_msg = "ics.uci.edu subdomains:\n"
        print(log_msg)
        report.write(f'\n{log_msg}')

        for subdomain, count in subdomains_sorted:
            log_msg = f'\t{subdomain}, {count}'
            print(log_msg)
            report.write(f'{log_msg}\n')


if __name__ == '__main__':
    generate_report()