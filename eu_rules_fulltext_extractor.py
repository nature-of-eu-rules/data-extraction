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

# path_to_celex_file = '[path to CSV file containing celex identifiers]'
# path_to_extracted_texts_htmls = '[path where to extract HTML documents to]'
# path_to_extracted_texts_pdfs = '[path where to extract PDF documents to]'
# path_to_extracted_texts_problems = '[path where to store files with celex identifiers as the filename where we could not find either an HTML or PDF document]'

path_to_celex_file = 'celex_nums_2.csv'
path_to_extracted_texts_htmls = 'htmls'
path_to_extracted_texts_pdfs = 'pdfs'
path_to_extracted_texts_problems = 'problems'

# open the CSV file with celex identifiers for legislation to extract
file = open(path_to_celex_file, "r")
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
    
    if len(dir_list_pr) > 0:
        df_pr = pd.read_csv(os.path.join(path_to_extracted_texts_problems, 'problematic-celexes.csv'))
        result.extend(df_pr['celex'].tolist())
    
    for item in dir_list_h:
        result.append(item.replace('.html', ''))

    for item in dir_list_p:
        result.append(item.replace('.pdf', ''))

    # for item in dir_list_pr:
    #     result.append(item.replace('.txt', ''))

    return result
    
# update list of celex identifiers to extract (by checking what is already extracted)
# this is needed when the script has to be run multiple times in order to complete
# the extraction process
s = set(get_list_done_celex())
celex_nums = [x for x in celex_nums if x not in s]

problematic_celexes = []
for celex in celex_nums:
    r = requests.get(reg_fulltext_base_url.format(celex))                                                                                                                                               # try to get HTML webpage for legislation
    soup = BeautifulSoup(r.content, 'lxml')                                                                                                                                                         # parse the webpage with BeautifulSoup's HTML5lib parser
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
        with open(path_to_extracted_texts_htmls + suffix, 'w') as f:                                                                                                                                    # write the file to disk       
            f.write(str(soup.prettify()))

# write list of problematic celexes to file
problematic_df = pd.DataFrame(problematic_celexes, columns=['celex'])
suffix = path_to_extracted_texts_problems+'problematic-celexes.csv' if path_to_extracted_texts_problems[-1] == os.path.sep else os.path.join(path_to_extracted_texts_problems, 'problematic-celexes.csv') # suffix if path to file has slash or not
problematic_df.to_csv(suffix)
