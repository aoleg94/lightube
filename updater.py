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

try:
	with open(os.path.join(scriptpath, "gitversion.txt"), "rt") as f:
		OLD_COMMIT = f.readline().strip()
except OSError:
	pass

def update(url, fname):
	def retrcb(got_blocks, block_size, total_bytes):
		got_bytes = got_blocks * block_size
		if total_bytes > 0:
			if got_bytes > total_bytes:
				got_bytes = total_bytes
			print(" Downloading %.2f%%... (%d kb / %d kb)" % (got_bytes * 100.0 / total_bytes, got_bytes // 1024, total_bytes // 1024), end='\r')
		else:
			print(" Downloading... (%d kb)" % (got_bytes // 1024), end='\r')

	import urllib.request, urllib.error, time
	req = urllib.request.Request(url)
	if os.access(fname, os.R_OK):
		timestamp = os.path.getmtime(fname)
		timestr = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(timestamp))
		req.add_header("If-Modified-Since", timestr)
	try:
		with urllib.request.urlopen(req) as fp:
			headers = fp.info()
			print("Downloading '%s' -> '%s'" % (url, fname))
			with open(fname, 'wb') as tfp:
				bs = 1024*8
				size = -1
				read = 0
				blocknum = 0
				if "content-length" in headers:
					size = int(headers["Content-Length"])
				retrcb(blocknum, bs, size)
				while True:
					block = fp.read(bs)
					if not block:
						break
					read += len(block)
					tfp.write(block)
					blocknum += 1
					retrcb(blocknum, bs, size)
	except urllib.error.HTTPError as e:
		if e.code == 304:
			print("File '%s' is up to date" % fname)
			return
		raise
	print()

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

def update_lightube():
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
		old_updater = open(__file__, 'rb').read()
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
		new_updater = open(__file__, 'rb').read()
		if old_updater != new_updater:
			os.execvp(sys.executable, [sys.executable, __file__])
			os.exit(0)

def update_ytdl_zip():
	update('http://yt-dl.org/downloads/latest/youtube-dl', 'youtube_dl.zip')

def update_mpv_dll(ver=None):
	if os.name != 'nt': return
	current = None
	try:
		with open(os.path.join(scriptpath, "mpvversion.txt"), "rt") as f:
			current = f.readline().strip()
	except OSError:
		pass
	if not os.access("mpv-1.dll", os.F_OK):
		if ver is None: ver="20201220-git-dde0189"
		ver = ("x86_64-" if sys.maxsize > 2**32 else "i686-") + ver
		url = "https://downloads.sourceforge.net/project/mpv-player-windows/libmpv/mpv-dev-" + ver + ".7z"
		update(url, scriptpath + os.sep + "libmpv.7z")
		os.system("ytdlwrap\\7za x libmpv.7z mpv-1.dll")
		#os.remove(scriptpath + os.sep + "libmpv.7z")

def update_all():
	update_ytdl_zip()
	update_mpv_dll()
	update_lightube()

if __name__ == "__main__":
	import subprocess
	rc = 0
	while rc == 0:
		update_all()
		rc = subprocess.call([sys.executable, "main.py"])
