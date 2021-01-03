#!/usr/bin/env python3
import os, os.path, sys
from urllib.request import urlopen
import json

scriptpath = os.path.dirname(os.path.abspath(__file__))

REPO = "aoleg94/lightube"
BRANCH = "master"
ZIP_PREFIX = REPO.split('/')[-1] + f"-{BRANCH}/"
COMMIT_URL = f"https://api.github.com/repos/{REPO}/commits/{BRANCH}"
REPO_URL = f"https://github.com/{REPO}/archive/{BRANCH}.zip"
MPVPY_INFO_URL = "https://api.github.com/repos/aoleg94/lightube/contents/mpvnew"
MPVPY_URL = "https://api.github.com/repos/jaseg/python-mpv/contents/mpv.py?ref="

BLACKLIST = ".* *.orig mpvnew/ web-mpv/* requirements.txt".split(" ")

OLD_COMMIT = None
NEW_COMMIT = None

with open(os.path.join(scriptpath, "gitversion.txt"), "w+t") as f:
	OLD_COMMIT = f.readline().strip()

def is_outdated():
	global OLD_COMMIT
	global NEW_COMMIT
	try:
		with urlopen(COMMIT_URL) as f:
			o = json.load(f)
			NEW_COMMIT = o["sha"]
	except Exception:
		import traceback
		traceback.print_exc()
	return NEW_COMMIT and OLD_COMMIT != NEW_COMMIT

def update():
	if is_outdated():
		print("downloading update")
		import zipfile, io, fnmatch
		with urlopen(REPO_URL) as f:
			b = f.read()
		with urlopen(MPVPY_INFO_URL) as f1:
			o = json.load(f1)
			with urlopen(MPVPY_URL + o["sha"]) as f2:
				o = json.load(f2)
				with open("mpv.py", "wb") as f3:
					import base64
					f3.write(base64.b64decode(o["content"]))
		print("unpacking update")
		with zipfile.ZipFile(io.BytesIO(b)) as z:
			L = [zi.filename[len(ZIP_PREFIX):] for zi in z.filelist if zi.filename != ZIP_PREFIX]
			L = [x for x in L if not any(fnmatch.fnmatch(x.lower(), y) for y in BLACKLIST)]
			for fn in L:
				if fn.endswith('/'):
					os.makedirs(fn, exist_ok=True)
				else:
					with open(fn, "wb") as f:
						f.write(z.read(ZIP_PREFIX + fn))
		for f in ['main.py', 'updater.py']:
			os.chmod(os.path.join(scriptpath, f), 0o755)
		print("saving version to file")
		with open(os.path.join(scriptpath, "gitversion.txt"), "wt") as f:
			f.write(NEW_COMMIT)

if __name__ == "__main__":
	import subprocess
	rc = 0
	while rc == 0:
		update()
		rc = subprocess.call([sys.executable, "main.py"])
