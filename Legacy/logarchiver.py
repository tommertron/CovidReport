import os
from datetime import datetime
import shutil

now = datetime.now()
archiveDate = now.strftime("%m-%d-%y")
newname = "/logarchive-" + archiveDate + ".txt"
thepath = os.getcwd()

os.rename(thepath + "/log.txt", thepath + newname)
shutil.move(thepath + newname, thepath + "/LogArchive" + newname)
f = open("log.txt", "x")
