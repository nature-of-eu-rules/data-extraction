"""
Script to extract full-text of EU legislative documents from the EURLEX website. 
Website: http://eur-lex.europa.eu/
Each legislative document is either available in PDF or HTML (or both)
"""

import requests
from bs4 import BeautifulSoup
import os
import csv
import pandas as pd
import argparse
import sys
from os.path import exists

def check_out_dir(data_dir):
    """Check if directory for saving extracted text exists, make directory if not 

        Parameters
        ----------
        data_dir: str
            Output directory path.

    """

    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)
        print(f"Created saving directory at {data_dir}")

argParser = argparse.ArgumentParser(description='EURLEX PDF and HTML legislative documents downloader')
required = argParser.add_argument_group('required arguments')
required.add_argument("-in", "--input", required=True, help="Path to input CSV file (single column, no header, list of celex identifiers). Find more info about CELEX identifiers here: http://eur-lex.europa.eu/content/help/eurlex-content/celex-number.html")
required.add_argument("-htp", "--htmlpath", required=True, help="Path to directory where to store the extracted EU legislative documents from EURLEX (http://eur-lex.europa.eu/) in HTML format. Each downloaded document will be named only with the CELEX identifier e.g. 32013R0145.html")
required.add_argument("-pdp", "--pdfpath", required=True, help="Path to directory where to store the extracted EU legislative documents from EURLEX (http://eur-lex.europa.eu/) in PDF format. Each downloaded document will be named only with the CELEX identifier e.g. 32013R0148.pdf")
required.add_argument("-prp", "--probpath", required=True, help="Path to a directory. After execution, this script will write a CSV file called 'problematic-celexes.csv' to this directory containing a list of CELEX identifiers for legislation that could not be downloaded for whatever reason")

args = argParser.parse_args()

path_to_celex_file = str(args.input)

if args.input is None:
     sys.exit('No input file specified. Type "python eu_rules_fulltext_extractor.py -h" for usage help.')

check_out_dir(str(args.htmlpath))
check_out_dir(str(args.pdfpath))
check_out_dir(str(args.probpath))

path_to_extracted_texts_htmls = str(args.htmlpath)
path_to_extracted_texts_pdfs = str(args.pdfpath)
path_to_extracted_texts_problems = str(args.probpath)

# open the CSV file with celex identifiers for legislation to extract
file = open(path_to_celex_file, "r", encoding='utf-8')
data = list(csv.reader(file, delimiter=","))
file.close()
celex_nums = []
for item in data:
    celex_nums.append(item[0])

# base URL for HTML documents
reg_fulltext_base_url = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{}"
# base URL for PDF documents
pdf_base_url = "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:{}&from=EN"

def get_list_done_celex():
    """
    Function to get a list of celex identifiers for legislation which has already been extracted

    Returns:
    - List of celex numbers which are already completed being processed
    """
    result = []
    h_path = path_to_extracted_texts_htmls
    pdf_path = path_to_extracted_texts_pdfs
    prob_path = path_to_extracted_texts_problems
    dir_list_h = os.listdir(h_path)
    dir_list_p = os.listdir(pdf_path)
    dir_list_pr = os.listdir(prob_path)
    
    if os.path.exists(os.path.join(path_to_extracted_texts_problems, 'problematic-celexes.csv')):
        df_pr = pd.read_csv(os.path.join(path_to_extracted_texts_problems, 'problematic-celexes.csv'))
        result.extend(df_pr['celex'].tolist())
    
    for item in dir_list_h:
        result.append(item.replace('.html', ''))

    for item in dir_list_p:
        result.append(item.replace('.pdf', ''))

    return result
    
# update list of celex identifiers to extract (by checking what is already extracted)
# this is needed when the script has to be run multiple times in order to complete
# the extraction process
s = set(get_list_done_celex())
celex_nums = [x for x in celex_nums if x not in s]

problematic_celexes = []
for celex in celex_nums:
    r = requests.get(reg_fulltext_base_url.format(celex))                                                                                                                                               # try to get HTML webpage for legislation
    soup = BeautifulSoup(r.content, 'lxml-xml')                                                                                                                                                         # parse the webpage with BeautifulSoup's HTML5lib parser
    if "The requested document does not exist." in soup.prettify():                                                                                                                                     # if the page has this message then there is no HTML webpage for this celex number on EURLEX
        r = requests.get(pdf_base_url.format(celex))                                                                                                                                                    # now try to get the PDF version of the legislation
        content_type = r.headers.get('content-type')                                                                                                                                                    # get the mime type of file (hopefully 'application/pdf')
        if 'application/pdf' in content_type:                                                                                                                                                           # if it is indeed a valid PDF file
            suffix = celex+'.pdf' if path_to_extracted_texts_pdfs[-1] == os.path.sep else os.path.join(os.path.join(path_to_extracted_texts_pdfs, os.path.sep), celex+'.pdf')                           # suffix if path to file has slash or not
            pdf = open(path_to_extracted_texts_pdfs + suffix, 'wb')                                                                                                                                     # open the contents of the PDF file to get ready to save it
            pdf.write(r.content)                                                                                                                                                                        # save the PDF file to disk
            pdf.close()                                                                                                         
        else:
            problematic_celexes.append(celex)                                                                                                                                                           # append to list of problematic celexes (no HTML or PDF present)
    else:
        suffix = celex+'.html' if path_to_extracted_texts_htmls[-1] == os.path.sep else os.path.join(os.path.join(path_to_extracted_texts_htmls, os.path.sep), celex+'.html')                           # suffix if path to file has slash or not
        with open(path_to_extracted_texts_htmls + suffix, 'w', encoding="utf-8") as f:                                                                                                                                    # write the file to disk       
            f.write(str(soup.prettify()))

# write list of problematic celexes to file
problematic_df = pd.DataFrame(problematic_celexes, columns=['celex'])
suffix = path_to_extracted_texts_problems+'problematic-celexes.csv' if path_to_extracted_texts_problems[-1] == os.path.sep else os.path.join(path_to_extracted_texts_problems, 'problematic-celexes.csv') # suffix if path to file has slash or not
problematic_df.to_csv(suffix)
