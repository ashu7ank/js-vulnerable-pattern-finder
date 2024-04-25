##Checks inside of text file given as input containing JS endpoints, evaluates it for problematic JS code, dumps a CSV full of JS endpoints with possible issues.
##For input file, feel free to use the results from tools like getJS, gau or waybackurls.
## python3 blaze-pp-js-check.py input.txt output.csv --workers '1-10' (be thoughtful while using excessive number of workers)

import argparse
import csv
import requests
import re
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

def check_js_flaws(url):
    """Checks for JavaScript flaws in a URL and returns a list of flaws"""
    flaws = []

    # Make a GET request to the URL
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e:
        return [f"Error: {e}"]

    # Check for JavaScript flaws
    content = response.text
    if "eval(" in content and "JSON.parse(" not in content:
        flaws.append("eval() function used")
    if "document.write" in content:
        flaws.append("document.write() function used")
    if "innerHTML" in content and "<" in content:
        flaws.append("innerHTML property used to insert HTML")
    if "window.open" in content:
        flaws.append("window.open() function used")
    if "with(" in content:
        flaws.append("with statement used")
    if re.search(r'on\w+=', content):
        flaws.append("Event handlers found")
    if re.search(r'Function\(', content):
        flaws.append("Function constructor used")
    if "String.fromCharCode" in content or ("eval" in content and "(\"" in content):
        flaws.append("Dynamic code execution found")

    return flaws

def check_url(url):
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e:
        status_code = "Error"
        flaws = [f"Error: {e}"]
    else:
        status_code = response.status_code
        if status_code == 200:
            flaws = check_js_flaws(url)
        else:
            flaws = []
    return [url, status_code, ", ".join(flaws)]

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="input file containing URLs")
    parser.add_argument("output_file", help="output file in CSV format")
    parser.add_argument("--workers", type=int, default=cpu_count(),
                        help="number of worker processes to use")
    args = parser.parse_args()

    # Read input URLs from file
    with open(args.input_file) as f:
        urls = [line.strip() for line in f]

    # Check URLs for JavaScript flaws and write results to CSV file
    with Pool(args.workers) as pool, open(args.output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["URL", "Status Code", "Flaws"])
        results = list(tqdm(pool.imap(check_url, urls), desc="Checking URLs", total=len(urls)))
        for result in results:
            writer.writerow(result)

if __name__ == "__main__":
    main()
