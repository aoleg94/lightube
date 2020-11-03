all: youtube-dl youtube-dl.exe

youtube-dl: youtube-dl.c
	$(CC) -o $@ $< -O2 -s

youtube-dl.exe: youtube-dl.c
	i686-w64-mingw32-gcc -o $@ $< -O2 -s -lws2_32

