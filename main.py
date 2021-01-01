#!/usr/bin/env python3
import os, os.path, sys
import threading
from flask import Flask, render_template, url_for, request, redirect, send_file
from urllib.request import urlopen

scriptpath = os.path.dirname(os.path.abspath(__file__))

try:
	import mpv
except ImportError:
	import mpvnew.mpv as mpv

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

MOVIES = []
def scan_movies():
	import glob
	fn = scriptpath + os.sep + 'movies.txt'
	if not os.access(fn, os.R_OK): return
	L = []
	with open(fn) as f:
		for line in f:
			line = line.strip()
			if line.startswith('#') or not line: continue
			L.append(line)
	global MOVIES
	MOVIES = []
	for pat in L:
		MOVIES += glob.iglob(os.path.expandvars(os.path.expanduser(pat)), recursive=True)

MAXRES = int(os.environ.get("MAXRES", 1080))
def ytdlfmt(height):
	global MAXRES
	MAXRES = int(height)
	return ('bestvideo[height<=%(max_height)d][vcodec^=avc]' +
		'+bestaudio/best[height<=%(max_height)d][vcodec^=avc]' +
		'/bestvideo[height<=%(max_height)d]+bestaudio' +
		'/best[height<=%(max_height)d]/best') % {"max_height": MAXRES}

PLAYLIST = []
PLAYLIST_FILE = None
def sync_playlist():
	global PLAYLIST
	global PLAYLIST_FILE
	if PLAYLIST_FILE is None:
		for pf in (
				'mpvplaylist.txt',
				scriptpath + os.sep + 'mpvplaylist.txt',
				os.path.expanduser('~') + os.sep + '.mpvplaylist.txt',
			):
			PLAYLIST_FILE = pf
			if os.access(pf, os.R_OK):
				with open(pf, 'rt') as f:
					PLAYLIST = [x.strip() for x in f.readlines()]
				break
		print('playlist from ' + PLAYLIST_FILE)
	else:
		with open(PLAYLIST_FILE, 'wt') as f:
			for x in PLAYLIST:
				print(x, file=f)
sync_playlist()

def ytdl_query(url):
	pass

def ytdl_prefetch(url):
	pass

_mp = None
def mp():
	global _mp
	global PLAYLIST
	global MAXRES
	if _mp is None:
		d = dict(log_handler=print, config_dir=os.path.dirname(__file__),
			input_default_bindings=True, input_vo_keyboard=True, osc=True, config=True, load_scripts=False,
			keep_open=True, fullscreen=True, idle=True, hwdec="auto", #msg_level="all=v",
			script_opts="ytdl_hook-try_ytdl_first=yes", #loglevel='debug',
			)
		for cookiefile in (
				'ytcookie.txt',
				os.path.expanduser('~') + os.sep + '.ytcookie.txt',
				scriptpath + os.sep + 'ytcookie.txt',):
			if os.access(cookiefile, os.R_OK):
				d['ytdl_raw_options'] = "mark-watched=,cookies=" + cookiefile
				print('cookies from ' + cookiefile)
		_mp = mpv.MPV(**d)
		_mp.event_callback('shutdown')(reinit)
		_mp.volume = 50
		_mp['ytdl-format'] = ytdlfmt(MAXRES)
		_mp['pause'] = True
		_mp.command('load_script', 'sponsorblock_minimal.lua')
		for x in PLAYLIST:
			_mp.playlist_append(x)
			ytdl_prefetch(x)
	return _mp

def kill_mp():
	global _mp
	if _mp is not None:
		try:
			_mp.quit()
			_mp.wait_for_shutdown()
		except mpv.ShutdownError:
			pass
		threading.Thread(target=_mp.terminate).start()
		_mp = None

@app.route('/api/reinit', methods=['POST'])
def reinit(*args):
	kill_mp()
	return ''

def mpwrap(f):
	def x(*args, **kwargs):
		try:
			return f(mp(), *args, **kwargs)
		except (BrokenPipeError, SystemError):
			kill_mp()
		return f(mp(), *args, **kwargs)
	x.__name__ = f.__name__
	return x

@app.route('/api/load/<path:url>', methods=['POST'])
@mpwrap
def load(mp, url):
	mp.loadfile(url, 'append-play')
	sync_playlist()
	ytdl_prefetch(url)
	return ''

@app.route('/api/add/<path:url>', methods=['POST'])
@mpwrap
def add(mp, url):
	mp.playlist_append(url)
	if mp.playlist:
		mp.playlist_move(len(mp.playlist)-1, 0)
	sync_playlist()
	ytdl_prefetch(url)
	return ''

@app.route('/api/maxres/<v>', methods=['POST'])
@mpwrap
def maxres(mp, v):
	mp['ytdl-format'] = ytdlfmt(int(v))
	return ''

@app.route('/api/play', methods=['POST'])
@mpwrap
def play(mp):
	mp.pause = False
	return ''

@app.route('/api/pause', methods=['POST'])
@mpwrap
def pause(mp):
	mp.pause = True
	return ''

@app.route('/api/vol/abs/<v>', methods=['POST'])
@mpwrap
def vol(mp, v):
	mp.volume = int(v)
	mp.show_text('Volume: %d%%' % mp.volume, 1000)
	return ''

@app.route('/api/vol/rel/<v>', methods=['POST'])
@mpwrap
def volr(mp, v):
	mp.volume += int(v)
	mp.show_text('Volume: %d%%' % mp.volume, 1000)
	return ''

@app.route('/api/speed/abs/<v>', methods=['POST'])
@mpwrap
def speed(mp, v):
	mp.speed = float(v)
	mp.show_text('Speed: %.2f' % mp.speed, 1000)
	return ''

@app.route('/api/speed/rel/<v>', methods=['POST'])
@mpwrap
def speedr(mp, v):
	mp.speed += float(v)
	mp.show_text('Speed: %.2f' % mp.speed, 1000)
	return ''

@app.route('/api/speed/up', methods=['POST'])
@mpwrap
def speedu(mp):
	mp.speed *= 1.1
	mp.show_text('Speed: %.2f' % mp.speed, 1000)
	return ''

@app.route('/api/speed/down', methods=['POST'])
@mpwrap
def speedd(mp):
	mp.speed /= 1.1
	mp.show_text('Speed: %.2f' % mp.speed, 1000)
	return ''

@app.route('/api/seek/rel/<v>', methods=['POST'])
@mpwrap
def sere(mp, v):
	mp.seek(float(v), 'relative')
	return ''

@app.route('/api/seek/abs/<v>', methods=['POST'])
@mpwrap
def seab(mp, v):
	mp.seek(float(v), 'absolute')
	return ''

@app.route('/api/mute', methods=['POST'])
@mpwrap
def mute(mp):
	mp.cycle('mute')
	mp.show_text('Mute: %s' % 'yes' if mp.mute else 'no', 1000)
	return ''

@app.route('/api/fullscreen/<v>', methods=['POST'])
@mpwrap
def setfs(mp, v):
	mp.fullscreen = bool(int(v))
	return ''

@app.route('/api/cycle/<v>', methods=['POST'])
@mpwrap
def cycle(mp, v):
	mp.cycle(v)
	return ''

@app.route('/api/cyclev/<v>/<o>', methods=['POST'])
@mpwrap
def cyclev(mp, v, o):
	mp.command('cycle-values', v, *o.split(' '))
	return ''

@app.route('/api/setprop/<p>/<v>', methods=['POST'])
@mpwrap
def setprop(mp, p, v):
	import json
	setattr(mp, p, json.loads(v))
	return ''

@app.route('/api/getprop/<p>', methods=['GET', 'POST'])
@mpwrap
def getprop(mp, p):
	import json
	return json.dumps(getattr(mp, p, None))

@app.route('/api/next', methods=['POST'])
@mpwrap
def pnext(mp):
	mp.playlist_next()
	return ''

@app.route('/api/prev', methods=['POST'])
@mpwrap
def pprev(mp):
	mp.playlist_prev()
	return ''

@app.route('/api/clear', methods=['POST'])
@mpwrap
def pclear(mp):
	mp.playlist_clear()
	global PLAYLIST
	PLAYLIST[:] = []
	sync_playlist()
	return ''

@app.route('/api/move/<a>/<b>', methods=['POST'])
@mpwrap
def pmove(mp, a, b):
	if int(b) < 0: return ''
	mp.playlist_move(int(a), int(b))
	return ''

@app.route('/api/remove/<a>', methods=['POST'])
@mpwrap
def premove(mp, a):
	mp.playlist_remove(int(a))
	sync_playlist()
	return ''

@app.route('/api/scan', methods=['POST'])
@mpwrap
def scan(mp):
	scan_movies()
	return ''

@app.route('/api/status')
@mpwrap
def mpstatus(mp):
	global MAXRES
	return {
		'position': mp.time_pos,
		'duration': mp.duration,
		'volume': mp.volume,
		'mute': mp.mute,
		'playing': not mp.pause,
		'playlist_pos': mp.playlist_pos,
		'speed': mp.speed,
		'downloads': dl_status(),
		'quality': MAXRES
	}

def dl_status():
	return {'progress': None, 'items': []}

import threading
import queue
if False:
	_DL_QUEUE = queue.Queue()
	_DL_STATUS = None
	def dl_status():
		global _DL_STATUS
		return {'progress': _DL_STATUS, 'items': list(_DL_QUEUE.queue)}
	def dl_thread():
		global _DL_QUEUE
		while True:
			url, fmt = _DL_QUEUE.get()
			with os.popen('youtube-dl -o "%s/Downloads/%%(title)s.%%(ext)s" --restrict-filenames "%s"' % (scriptpath, url, fmt)) as f:
				pass
			_DL_QUEUE.task_done()
	#tt = threading.Thread(target=title_thread)
	#tt.setDaemon(1)
	#tt.start()

	@app.route('/api/download/<fmt>/<path:url>', methods=['POST'])
	def download(fmt, url):
		global _DL_QUEUE
		_DL_QUEUE.put(url, fmt)
		return ''

title = None
if True:
	_TITLE_CACHE = {}
	_TITLE_QUEUE = queue.Queue()
	def title(x):
		if x.get('title'): return
		f = x.get('filename')
		if not f: return
		if not f.startswith('http'): return
		if f not in _TITLE_CACHE:
			_TITLE_CACHE[f] = True
			_TITLE_QUEUE.put(f)
		else:
			t = _TITLE_CACHE[f]
			if t in (True, False): return
			x['title'] = t
	def title_thread():
		while True:
			k = _TITLE_QUEUE.get()
			try:
				with os.popen('youtube-dl --no-warnings --flat-playlist --no-playlist -J "%s"' % k) as f:
					o = json.load(f)
					_TITLE_CACHE[k] = o.get('title')
			except Exception:
				_TITLE_CACHE[k] = False
			_TITLE_QUEUE.task_done()
	tt = threading.Thread(target=title_thread)
	tt.setDaemon(1)
	tt.start()

@app.route('/api/status2')
@mpwrap
def mpstatus2(mp):
	pl = mp.playlist
	global MAXRES
	global PLAYLIST
	PLAYLIST = [x.get('filename') for x in pl]
	sync_playlist()
	for x in pl:
		title(x)
	p = mp.time_pos
	d = mp.duration
	if mp.playlist_pos is not None and mp.playlist_pos+1 < len(PLAYLIST) and p is not None and d is not None and d-p < 120:
		ytdl_prefetch(PLAYLIST[mp.playlist_pos+1]) # fetch in background
	return {
		'position': mp.time_pos,
		'duration': mp.duration,
		'volume': mp.volume,
		'title': mp.media_title,
		'mute': mp.mute,
		'playing': not mp.pause,
		'playlist_pos': mp.playlist_pos,
		'video': mp.path,
		'playlist': pl,
		'audio_tracks': [x for x in mp.track_list if x.get('type') == 'audio'],
		'sub_tracks': [x for x in mp.track_list if x.get('type') == 'sub'],
		'movies': [{'name': os.path.basename(x), 'full': os.path.abspath(x)} for x in MOVIES],
		'speed': mp.speed,
		'downloads': dl_status(),
		'quality': MAXRES
	}

@app.route('/')
def index():
	return redirect('/static/indexmpv.html')

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

try:
	update('http://yt-dl.org/downloads/latest/youtube-dl', 'youtube_dl.zip')
	sys.path.append('youtube_dl.zip')
	import youtube_dl, time, json
	print('Youtube-DL library on')
	_YTDL_OBJ = youtube_dl.YoutubeDL(dict(simulate=True, no_warnings=True, extract_flat='in_playlist',
		sub_format='ass/srt/best', subtitleslangs='en,ru,eng,rus'.split(','), writesubtitles=True, writeautomaticsub=True,
		noplaylist=True, quiet=True, format=ytdlfmt(MAXRES)))
	_YTDL_CACHE = {}
	_YTDL_QUEUE = queue.Queue()
	_YTDL_CACHE_OK_TIMEOUT = 60 * 60
	_YTDL_CACHE_ERR_TIMEOUT = 10
	_YTDL_SPONSORBLOCK_API = 'https://sponsor.ajay.app/api/skipSegments?categories=["sponsor","intro","outro","interaction","selfpromo"]&videoID='
	def ytdl_thread():
		while True:
			k = _YTDL_QUEUE.get()
			try:
				if k.startswith('https://sponsor.ajay.app/api/'):
					with urlopen(k) as f:
						res = f.read()
						_YTDL_CACHE[k] = (True, res, time.time())
				else:
					_YTDL_OBJ.params['format'] = ytdlfmt(MAXRES)
					res = _YTDL_OBJ.extract_info(k)
					_YTDL_CACHE[k] = (type(res) != str, res, time.time())
			except Exception:
				import traceback
				_YTDL_CACHE[k] = (False, traceback.format_exc(), time.time())
			_YTDL_QUEUE.task_done()
	ytt = threading.Thread(target=ytdl_thread)
	ytt.setDaemon(1)
	ytt.start()
	@app.route('/api/ytdl/<path:url>', methods=['POST'])
	def ytdl_query(url):
		if not url.startswith('http'): return '', 400
		if url not in _YTDL_CACHE:
			print('query ' + url)
			_YTDL_CACHE[url] = (None, None, None)
			_YTDL_QUEUE.put(url)
			return '', 201
		else:
			ok, data, when = _YTDL_CACHE[url]
			if ok is None: return '', 202
			ago = time.time() - when
			if ago > (_YTDL_CACHE_OK_TIMEOUT if ok else _YTDL_CACHE_ERR_TIMEOUT):
				_YTDL_CACHE[url] = (None, None, None)
				_YTDL_QUEUE.put(url)
				return '', 201
			return data, 200 if ok else 500
	import re
	_YTDL_ID_RE = re.compile(
	r'https?://youtu\.be/([-_\w]+).*|' +
	r'https?://w?w?w?\.?youtube%.[a-zA-Z]{2,3}/v/([-_\w]+).*|' +
	r'https?://w?w?w?\.?youtube%.[a-zA-Z]{2,3}/watch.*[?&]v=([-_\w]+).*|' +
	r'https?://w?w?w?\.?youtube%.[a-zA-Z]{2,3}/embed/([-_\w]+).*')
	def ytdl_prefetch(url):
		ytdl_query(url)
		m = _YTDL_ID_RE.match(url)
		if m:
			url = _YTDL_SPONSORBLOCK_API + m.group(1)
			ytdl_query(url)
except ImportError:
	print('Youtube-DL library failed to load, using fallback method')
	os.environ["PATH"] = scriptpath + os.pathsep + os.environ["PATH"]
	if os.system('youtube-dl --version') != 0:
		ytdlexe = 'youtube-dl.exe' if os.name == 'nt' else 'youtube-dl'
		update('http://yt-dl.org/downloads/latest/' + ytdlexe, ytdlexe)
else:
	os.environ["PATH"] = scriptpath + os.sep + 'ytdlwrap' + os.pathsep + os.environ["PATH"]
	if os.name == 'posix':
		os.chmod(os.path.join(scriptpath, 'ytdlwrap', 'youtube-dl'), 0o755)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
