from django.core.management.base import BaseCommand, CommandError
from PyPDF2 import PdfFileWriter, PdfFileReader

import json, os, string, shutil
import elasticsearch, uuid
import sys, subprocess
import bs4 as bs

import config

if config._OS == "os x":
    imageType = ".png"
elif config._OS == "ubuntu 14":
    imageType = ".tiff"
else:
    imageType = ".png"
    
es = elasticsearch.Elasticsearch()

def puncTo_(s):
    table = string.maketrans(string.punctuation+string.whitespace, "_"*len(string.punctuation+string.whitespace))
    
    return "_".join([ t for t in string.translate(s, table).split("_") if t.strip() != "" ])
    
def splitPdfToDir(d, pdfLoc):
    inputpdf = PdfFileReader(open(pdfLoc, "rb"))
    
    for i in xrange(inputpdf.numPages):
        print "At page %s of %s" % (i, str(inputpdf.numPages))
        output = PdfFileWriter()
        output.addPage(inputpdf.getPage(i))
        with open(os.path.join(d, "document-page-%s.pdf" % i), "wb") as outputStream: 
            try:
                output.write(outputStream)
            except:
                print "Couldn't write page %s" % i

class Command(BaseCommand):
    help = 'Indexes a directory or a collection of directories (root).'

    def add_arguments(self, parser):
        parser.add_argument('dir', nargs='+', type=str, help="Root directory with que of files.")

        parser.add_argument('--blank',
            action='store_true',
            default=False,
            help='Specifies ...')

    def handle(self, *args, **options):
        if options['blank']:
            self.stdout.write('Beep')
        else:
            ## Build que from .pdf's in dir
            print "Loading que:\n",
            que = sorted([  f for f in os.listdir(options['dir'][0]) if f[-3:].lower() == "pdf" ], reverse=True)
            
            for each in que:
                print each
            ## Check if a previous aborted operation exists (operation.aborted).
                # If so, clean up that dir so it can start over
                # (to implement)
            
            # While que not empty, check for quit (to implement)
            while que != []:                
                # pop next in que
                nextFile = que.pop()
                
                print "Processing %s" % nextFile
                
                try:
                    ## mkdir
                    try:
                        # make new directory friendly
                        newDir = os.path.join(options['dir'][0], puncTo_(nextFile[:-4]))
                        os.mkdir(newDir)         # Assumes ends in .pdf
                    except BaseException, e:
                        print e                         # Catch all errors. This should be specific.
                    
                    # split the pdf
                    print "Splitting file."
                    splitPdfToDir(newDir, os.path.join(options['dir'][0], nextFile))
                    
                    # convert to TIFF|JPG
                    for each in os.listdir(newDir):
                        if os.path.splitext(each)[1].lower() == ".pdf":
                            print "Converting: %s" % os.path.join(newDir, each)
                            subprocess.call(["convert", "-density", "150", "-depth", "8", os.path.join(newDir, each), os.path.join(newDir, os.path.splitext(each)[0]+imageType) ])
                    
                    # Tesseract OCR to hocr,html
                    for each in os.listdir(newDir):
                        if os.path.splitext(each)[1].lower() == imageType:
                            print "OCRing: %s to html" % os.path.join(newDir, each)
                            subprocess.call(["tesseract", os.path.join(newDir, each), os.path.join(newDir, os.path.splitext(each)[0]), "-l", "eng", "hocr"])
                    
                    # raw txt out for indexing
                    for each in os.listdir(newDir):
                        if os.path.splitext(each)[1].lower() == imageType:
                            print "Ripping raw txt: %s to txt" % os.path.join(newDir, each)
                            subprocess.call(["tesseract", os.path.join(newDir, each), os.path.join(newDir, os.path.splitext(each)[0]), "-l", "eng"])
                    
                            #
                            #with open(os.path.join(newDir, each), "r") as fileIn:
                            #    soup = bs.BeautifulSoup(fileIn.read())
                            #    
                            #    with open(os.path.join(newDir, each[:-4]+".txt"), "w") as fileOut:
                            #        fileOut.write(soup.getText("\n").encode('utf-8'))
                            
                    # update elasticsearch
                    try:
                        
                        # Set the unique UUID for the whole document, so that pages can be grouped later. Could do a parent child relationship, but it seems unnecesarrily complex for our purposes here.
                        parentDocUUID = str(uuid.uuid4())
                        
                        # Check if index library and type book exist, if not, create mapping
                        if not es.indices.exists_type(index="library", doc_type="book"):
                            mapping = {
                                            "mappings" : {
                                                "book" : {
                                                    "properties" : {
                                                        "parentDocUUID" : {
                                                            "type" : "string",
                                                            "index" : "not_analyzed" 
                                                        }
                                                    }
                                                }
                                            }
                                        
                                        }
                            es.indices.create(index="library", body=mapping)
                        
                        for page in os.listdir(newDir):
                            if page[-4:] == ".txt":
                                
                                print "Indexing page: %s" % page
                                try:
                                    with open(os.path.join(newDir, page)) as pageFile:
                                        pageContent = pageFile.read()
                                except IOError:
                                    self.stderr.write("Could not open file %s" % os.path.join(newDir, page))
                                
                                self.stdout.write('Indexing page %s' % page.split(".txt")[0].split("-")[-1:])
                                es.index(index='library', doc_type='book', body={
                                    'author': 'unknown',#dirMetaData["author"],
                                    'title': puncTo_(nextFile[:-4]),#dirMetaData["title"],
                                    'parentDocUUID': parentDocUUID,         # Generate a unique ID for the book/article such that pagination can call to next page by referencing this UUID and the page#.
                                    'location':os.path.join("data", puncTo_(nextFile[:-4]))+"/",     # VERY HARDCODED!!!!!!!!!!!
                                    'pageNumber':int(page.split(".txt")[0].split("-")[-1:][0]),
                                    'pageContent':pageContent
                                })
                                
                    except OSError:
                        self.stderr.write("Invalid directory structure; was expecting pages/txt under directory root.")
                    
                    ## cleanup    
                    # mk subdir pages and subsubdir html/txt
                    os.mkdir(os.path.join(newDir, "pages/"))
                    os.mkdir(os.path.join(newDir, "pages/html"))
                    os.mkdir(os.path.join(newDir, "pages/txt"))
                    
                    # mk extra png files?
                    # If .tiff for conversion, make png files now
                    
                    # move .png files to pages subdir
                    for pageImage in os.listdir(newDir):
                        if pageImage[-4:] == ".png":
                            shutil.move(os.path.join(newDir, pageImage), os.path.join(newDir, "pages/") )
                            
                    # rm *.pdf
                    for f in os.listdir(newDir):
                        if f[-4:] == ".pdf":
                            os.remove(os.path.join(newDir, f))
                        
                    # mv *.html to pages (for in image hit highlighting)
                    for pageImage in os.listdir(newDir):
                        if pageImage[-5:] == ".html":
                            shutil.move(os.path.join(newDir, pageImage), os.path.join(newDir, "pages/html") )
                            
                    # mv *.txt to pages/txt for later data analysis
                    for pageImage in os.listdir(newDir):
                        if pageImage[-4:] == ".txt":
                            shutil.move(os.path.join(newDir, pageImage), os.path.join(newDir, "pages/txt") )
                            
                    # mv source pdf to ./targer_dir/source.pdf (for easy deleting if space a problem and archived elsewhere)
                    # This also marks that as done, if a pdf errored out it would stay in the directory for a rerun
                    shutil.move(os.path.join(options['dir'][0], nextFile), newDir)
    
                    # Hand fix shitty doc and test
                except:
                    with open("./error.log", "a") as f:
                        f.write("Error with %s" % str(nextFile))