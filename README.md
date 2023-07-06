# data-extraction
Data extraction scripts for the [Nature of EU Rules project](https://research-software-directory.org/projects/the-nature-of-eu-rules-strict-and-detailed-or-lacking-bite). Given a list of [CELEX](https://eur-lex.europa.eu/content/help/eurlex-content/celex-number.html) identifiers for EU legislation, the ```eu_rules_fulltext_extractor.py``` script downloads the corresponding documents for the legislation from the [EURLEX](https://eur-lex.europa.eu) website. It stores the files in two folders: one for [HTML](https://www.w3schools.com/html/) documents and one for [PDF](https://docs.fileformat.com/pdf/) documents. Some older documents are only available in PDF format on the website. As a first priority, the script tries to download the HTML version of a document if available (because this format is easier to parse later on). If there is no HTML version available, it extracts the PDF version. If neither the HTML nor PDF versions could be extracted for whatever reason, the script keeps a list of CELEX identifiers which encountered errors when downloading.

##### Requirements
+ [Python](https://www.python.org/downloads/) 3.9.12+
+ A tool for checking out a [Git](http://git-scm.com/) repository.
+ Input CSV file with single column (no header) of [CELEX](https://eur-lex.europa.eu/content/help/eurlex-content/celex-number.html) identifiers for EU legislation

##### Usage steps

1. Get a copy of the code:

        git clone git@github.com:nature-of-eu-rules/data-extraction.git
    
2. Change into the `data-extraction/` directory:

        cd data-extraction/
    
3. Create new [virtual environment](https://docs.python.org/3/library/venv.html) e.g:

        python -m venv path/to/virtual/environment/folder/
       
4. Activate new virtual environment e.g. for MacOSX users type: 

        source path/to/virtual/environment/folder/bin/activate
        
5. Install required libraries for the script in this virtual environment:

        pip install -r requirements.txt

6. Check the command line arguments required to run the script by typing:

        python eu_rules_fulltext_extractor.py -h
        
        OUTPUT >
        
        usage: eu_rules_fulltext_extractor.py [-h] -in INPUT -htp HTMLPATH -pdp PDFPATH -prp    PROBPATH

        EURLEX PDF and HTML legislative documents downloader

        optional arguments:
        -h, --help            show this help message and exit

        required arguments:
        -in INPUT, --input INPUT
                        Path to input CSV file (single column, no header, list of celex identifiers). Find more info about CELEX identifiers here: http://eur-lex.europa.eu/content/help/eurlex-content/celex-
                        number.html
                        
        -htp HTMLPATH, --htmlpath HTMLPATH
                        Path to directory where to store the extracted EU legislative documents from EURLEX (http://eur-lex.europa.eu/) in HTML format. Each downloaded document will be named only with the CELEX identifier e.g.
                        32012R0145.html
                        
        -pdp PDFPATH, --pdfpath PDFPATH
                        Path to directory where to store the extracted EU legislative documents from EURLEX (http://eur-lex.europa.eu/) in PDF format. Each downloaded document will be named only with the CELEX identifier e.g.
                        32013R0148.pdf
                        
        -prp PROBPATH, --probpath PROBPATH
                        Path to a directory. After execution, this script will write a CSV file called 'problematic-celexes.csv' to this directory containing a list of CELEX identifiers for legislation that could
                        not be downloaded for whatever reason

7. Example usage: 

        python eu_rules_fulltext_extractor.py --input path/to/celex_nums.csv --htmlpath path/to/htmls/ --pdfpath path/to/pdfs/ --probpath path/to/problems/
        
##### License

Copyright (2023) [Kody Moodley, The Netherlands eScience Center](https://www.esciencecenter.nl/team/dr-kody-moodley/)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.