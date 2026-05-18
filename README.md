PS S-100 explorer
-----------------
-----------------
The result files of the code can be browse here : [Feature catalogs](https://jibede.github.io/S100PSexplorer/catalog/)

Tool to generate the S100 PS explorer developed by SHOM
-------------------------------------------------------
# Install 
* ## Librairies :
  * pip install -r requirements.txt  
  librairies used : pyyaml, xmltodict

  ## Config : 
* config.yaml : for now only used by cr_indexhtml.py 
  * name : name of the website
  * basedir : directory wich contains FCxml dir
  * dev_dir : directory containing the FC.xml in dev (usually downloaded from github)
  * official_dir : directory containing the official FC.xml (downloaded from the official IHO register)
  * other : if you mant to put your own files
  * output_html : file index.html in output (normally in basedir/FCxml)
  * html_extension : to decide wether the generated html files will have htm or html extension


  * dir structure :  
    - BasediR  
      - FCxml  
        - dev
          - FC1.xml
          - FC1.htm
        - official
          - FC1.xml
          - FC1.xml
        - others
        - index.htm
           

# FC2html.py
Create an html file from the xml Feature Catalog. 

* Usage : python FC2html.py -f FC.xml
* Result : FC.htm in the same dir

Or 

* Usage : python FC2html.py -d FCxml/dev (no final \ )
* Result : scans the xml files in the FCxml/dev directory to create an htm for each

# cr_indexhtml.py 
Create an index file for the html catalogs in the specified basedir (in config.yaml file)
If no FC.htm in one of the official_dir or dev_dir, then index.html will reference nothing.
* Usage
  * Fill config.yaml file
  * Run
* Result : index.htm in the basedir/output_html dir

Remarks
-------
Code has to be improved, refactored and pût in object oriented structure
If you want to add your own files in others, you'll have to modify the html creation in main.py
Improvements needed for the interface
