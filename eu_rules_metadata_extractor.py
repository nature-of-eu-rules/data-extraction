"""
Script to extract metadata of EU legislative documents from the CELLAR database
SPARQL endpoint URL to access CELLAR is here: http://publications.europa.eu/webapi/rdf/sparql
If any fields have missing values, an attempt is made to scrape these from the EURLEX website.
Website: http://eur-lex.europa.eu/
"""

import csv
from SPARQLWrapper import SPARQLWrapper, TURTLE, JSON
from rdflib import Graph, Literal
import pandas as pd
import os
import requests
import json
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import argparse
import sys
from os.path import exists

argParser = argparse.ArgumentParser(description='EURLEX PDF and HTML legislative documents metadata downloader')
required = argParser.add_argument_group('required arguments')
required.add_argument("-in", "--input", required=True, help="Path to input CSV file (single column, no header, list of celex identifiers). Find more info about CELEX identifiers here: http://eur-lex.europa.eu/content/help/eurlex-content/celex-number.html")
required.add_argument("-out", "--output", required=True, help="Path to a CSV file to store the metadata in e.g. 'path/to/metadata.csv'. ")

args = argParser.parse_args()

if args.input is None:
     sys.exit('No input file specified. Type "python eu_rules_metadata_extractor.py -h" for usage help.')

if args.output is None:
     sys.exit('No output file specified. Type "python eu_rules_metadata_extractor.py -h" for usage help.')

IN_CELEX_FILE = str(args.input)
OUT_METADATA_FILE = str(args.output)

# import list of celex numbers of legislation for which to extract metadata
file = open(IN_CELEX_FILE, "r")
data = list(csv.reader(file, delimiter=","))
file.close()
celex_nums = []
for item in data:
    celex_nums.append(item[0])

# Todo: if possible, extract the number of times that a file has been discussed in the Council or its preparatory bodies (under Procedure tab)
# Todo: if possible, extract the responsible EP committee

# the names of properties in CELLAR use the CDM ontology terminology / ontology: https://op.europa.eu/en/web/eu-vocabularies/cdm
# the names used on the EURLEX website are different than the CDM ones. We specify a mapping here:
property_mapping = {
    "celex"                 : "http://publications.europa.eu/ontology/cdm#resource_legal_id_celex",
    "author"                : "http://publications.europa.eu/ontology/cdm#work_created_by_agent",
    "responsible_body"      : "http://publications.europa.eu/ontology/cdm#regulation_service_responsible",
    "form"                  : "http://publications.europa.eu/ontology/cdm#resource_legal_type",
    "title"                 : "http://publications.europa.eu/ontology/cdm#work_title",                                     # (or scrape by p tag with id = "englishTitle")
    "addressee"             : "http://publications.europa.eu/ontology/cdm#resource_legal_addresses_country",               # only for decisions - (get string from XML result)
    "date_adoption"         : "http://publications.europa.eu/ontology/cdm#work_date_document",
    "date_in_force"         : "http://publications.europa.eu/ontology/cdm#resource_legal_date_entry-into-force",
    "date_end_validity"     : "http://publications.europa.eu/ontology/cdm#resource_legal_date_end-of-validity",            # (and cdm:resource_legal_in-force)
    "directory_code"        : "http://publications.europa.eu/ontology/cdm#resource_legal_is_about_concept_directory-code", # (get string from XML result)
    "procedure_code"        : "http://publications.europa.eu/ontology/cdm#procedure_code_interinstitutional_basis_legal",  # (or cdm:resource_legal_information_miscellaneous)
    "eurovoc"               : "http://publications.europa.eu/ontology/cdm#work_is_about_concept_eurovoc",                  # (get string from XML result)
    "subject_matters"       : "http://publications.europa.eu/ontology/cdm#resource_legal_is_about_subject-matter"          # (get string from XML result)
    
}

def get_title(celex):
    """
    Function to extract the title summary of legislation from EURLEX website if it is not available in CELLAR

    Parameters:
    - celex: str
        unique identifier for legislation e.g. '32016R0679'
    
    Return:
    - Summary title (str) of legislation

    """
    reg_base_url = "https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:{}"
    r = None
    try:
        r = requests.get(reg_base_url.format(celex))
    except:
        return ''
      
    if r is not None:  
        soup = BeautifulSoup(r.content, 'html5lib')
        res = soup.find('meta', attrs={"property" : "eli:title", "lang" : "en"})
        if res:
            return res.get('content')
        else:
            return ''
    else:
        return ''

def execute_sparql_query_and_return_results(sparql, query):
    """
    Function to get metadata for a specific piece of legislation (indicated by a unique celex number).
    This is done by executing a sparql query

    Parameters:
    - sparql: SPARQLWrapper instance
        initialised with endpoint URL
    - query: str
        SPARQL query string to execute

    Returns:
    - SPARQL query results in TURTLE format

    """
    sparql.setReturnFormat(TURTLE)
    sparql.setQuery(query)
    try:
        results = sparql.query().convert()
        return results.decode("utf-8")

    except Exception as e:
        print(e)
        return -1
    
def get_string_label(sparql, uri, pred, celex_num):
    """
    Gets the string representation of a coded metadata field for legislation.
    For example, the directory code field for legislation is a numerical identifier for the policy area.
    An example directory code looks like this: '11.60.40.20' and its URL representation 
    looks like this: http://publications.europa.eu/resource/authority/dir-eu-legal-act/11604020
    The string label for this code is 'Anti-dumping measures'

    Parameters:
    - sparql : SPARQLWrapper instance
        initialised with endpoint URL
    - uri : str
        URL representation of the directory code
    - pred : str
        The metadata field (using the EURLEX name for that field and not the CDM one)
    - celex_num : str
        The CELEX identifier for the legislation 

    Returns:
    - String representation of the given metadata property value
    """
    if (pred == 'directory_code'):
        # for directory code we only need the most general policy area 
        # not the most fine-grained topic of the legislation
        dc_uri_parts = uri.split('/')
        new_dc_uri_parts = dc_uri_parts[:-1]
        dc = dc_uri_parts[-1][:2] # most general part of directory code
        new_dc_uri_parts.append(dc)
        uri = '/'.join(new_dc_uri_parts)
    
    sparql.setReturnFormat(JSON) # return JSON format response
    query = """ 

    SELECT (str(?o) as ?label) WHERE {{
        <{}> skos:prefLabel ?o .
        FILTER (lang(?o) = "en")
    }}

    """

    query = query.format(uri) # insert URI value into query
    sparql.setQuery(query)
    try: # execute query
        results = sparql.query().convert()
    except:
        return ''
    
    # return query results
    val = results["results"]["bindings"][0]["label"]["value"]
    return val
    
def get_metadata_for_legal_acts(celex_nums, endpoint_url):
    """
    Extracts all the metadata for a given legislative document

    Parameters:
    - celex_nums : List
        list of unique celex identifiers for legislation to extract
    - endpoint_url : str
        SPARQL endpoint URL (CELLAR) where to extract the metadata from

    Returns:
    - Metadata as (list of lists) where each list in the larger list
     represents all the metadata property values for a single legislative document
     (the list represents a table row of values for that legislative document)
    """
    sparql = SPARQLWrapper(endpoint_url)
    CDM_PREFIX = "http://publications.europa.eu/ontology/cdm#"
    metadata_query_base = """
    
    PREFIX cdm: <{}> 

    CONSTRUCT {{?s ?p ?o}}

    WHERE {{

      SELECT DISTINCT ?s ?p ?o WHERE {{
         ?s cdm:resource_legal_id_celex "{}"^^xsd:string .
         ?s ?p ?o .
      }}

    }}
    
    """
    
    metadata = []
    processed_celex = []
    metadata_header_row = ['celex', 'author', 'responsible_body', 'form', 'title', 'addressee', 'date_adoption', 'date_in_force', 'date_end_validity', 'directory_code', 'procedure_code', 'eurovoc', 'subject_matters']
    metadata.append(metadata_header_row)
    idx = 1
    for celex_num in celex_nums:
        if (celex_num not in processed_celex) and (celex_num not in ['celex']):
            current_row = {
                    "celex"                 : [],
                    "author"                : [],
                    "responsible_body"      : [],
                    "form"                  : [],
                    "title"                 : [],
                    "addressee"             : [],
                    "date_adoption"         : [],
                    "date_in_force"         : [],
                    "date_end_validity"     : [],
                    "directory_code"        : [],
                    "procedure_code"        : [],
                    "eurovoc"               : [],
                    "subject_matters"       : [] 
            }
            
            idx += 1
            metadata_query = metadata_query_base.format(CDM_PREFIX, celex_num)
            query_result = execute_sparql_query_and_return_results(sparql, metadata_query)
            if (query_result != -1):
                g = Graph().parse(data=str(query_result), format='turtle')
                for s, p, o in g.triples((None, None, None)):
                    if str(p) in list(property_mapping.values()):
                        keys = [k for k, v in property_mapping.items() if v == str(p)]
                        predicate = keys[0]

                        if isinstance(o, Literal):
                            current_row[predicate].append(str(o))
                        else:
                            current_row[predicate].append(get_string_label(sparql, str(o), predicate, celex_num))
                                
                for item in current_row:
                    if len(current_row[item]) == 0:
                        current_row[item] = ''
                    elif len(current_row[item]) == 1:
                        current_row[item] = current_row[item][0]
                    else:
                        current_row[item] = ' | '.join(list(set(current_row[item])))
                        
                # If the title summary is missing then try to scrape the title
                # from the EURLEX website
                if (len(current_row['title']) == 0):
                    current_row['title'] = get_title(celex_num)
                    
                new_current_row = []
                for field in current_row:
                    new_current_row.append(current_row[field])
                        
                metadata.append(new_current_row)
            
    return metadata
    
import time

# get the start time
st = time.time()
# Extract all metadata for input list of celex identifiers
SPARQL_ENDPOINT_URL = "http://publications.europa.eu/webapi/rdf/sparql"
metadata = get_metadata_for_legal_acts(celex_nums, SPARQL_ENDPOINT_URL)
# get the end time
et = time.time()
# get the execution time
elapsed_time = et - st

print('Execution time:', elapsed_time, 'seconds')

# saving the results to file: opening the csv file in 'w+' mode
file = open(OUT_METADATA_FILE, 'w', newline ='')
with file:   
    write = csv.writer(file)
    write.writerows(metadata)


