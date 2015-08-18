from django.core.management.base import BaseCommand, CommandError
import json, os
import elasticsearch, uuid

es = elasticsearch.Elasticsearch()

class Command(BaseCommand):
    help = 'Indexes a set of text file. Obsolute. Now part of update root.'

    def add_arguments(self, parser):
        parser.add_argument('dir', nargs='+', type=str, help="Directory or root directory containing index format.")

        parser.add_argument('--root',
            action='store_true',
            default=False,
            help='Specifies if the directory is a root dir with a collection of indexable dirs.')

    def handle(self, *args, **options):
        if options['root']:
            self.stdout.write('This dir (%s) is a root dir.' % options['dir'][0])
        else:
            self.stdout.write('Reading from directory: %s' % options['dir'][0])
            
            try:
                with open(os.path.join(options['dir'][0], "./meta.json")) as metaDataFile:
                    dirMetaData = json.load(metaDataFile)
            except IOError:
                self.stderr.write("No such directory, or error reading from directory, or malformed meta.json.")
            
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
                
                for page in os.listdir(os.path.join(options['dir'][0], "./pages/txt/")):
                    
                    try:
                        with open(os.path.join(options['dir'][0], "./pages/txt/", page)) as pageFile:
                            pageContent = pageFile.read()
                    except IOError:
                        self.stderr.write("Could not open file %s" % os.path.join(options['dir'][0], "./pages/txt/", page))
                    
                    self.stdout.write('Indexing page %s' % page.split(".txt")[0].split("-")[-1:])
                    es.index(index='library', doc_type='book', body={
                        'author': dirMetaData["author"],
                        'title': dirMetaData["title"],
                        'parentDocUUID': parentDocUUID,         # Generate a unique ID for the book/article such that pagination can call to next page by referencing this UUID and the page#.
                        'location':options['dir'][0],
                        'pageNumber':int(page.split(".txt")[0].split("-")[-1:][0]),
                        'pageContent':pageContent
                    })
                    
            except OSError:
                self.stderr.write("Invalid directory structure; was expecting pages/txt under directory root.")
                