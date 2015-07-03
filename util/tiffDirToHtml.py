# Convert all pdf's in a directory to format suitable for tesseract. 

import sys, subprocess, os

for each in os.listdir(sys.argv[1]):
	if os.path.splitext(each)[1].lower() == ".tiff":
		print "Converting: %s" % os.path.join(sys.argv[1], each)
		#subprocess.call(["convert", "-density", "600", "-depth", "8", os.path.join(sys.argv[1], each), os.path.join(sys.argv[1], os.path.splitext(each)[0]+".tiff") ])
		subprocess.call(["tesseract", os.path.join(sys.argv[1], each), os.path.join(sys.argv[1], os.path.splitext(each)[0]), "-l", "eng", "hocr"])
