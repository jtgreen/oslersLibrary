from PyPDF2 import PdfFileWriter, PdfFileReader
import sys, os

inputpdf = PdfFileReader(open(sys.argv[1], "rb"))

for i in xrange(inputpdf.numPages):
    print "At page %s of %s" % (i, str(inputpdf.numPages))
    output = PdfFileWriter()
    output.addPage(inputpdf.getPage(i))
    with open(os.path.join(sys.argv[2], "document-page-%s.pdf" % i), "wb") as outputStream:
        
	try:
		output.write(outputStream)
	except:
		print "Couldn't write page %s" % i
