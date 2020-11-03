// x86_64-w64-mingw32-gcc -o youtube-dl.exe youtube-dl.c -O2 -s -lws2_32
// gcc -o youtube-dl youtube-dl.c -O2 -s

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#ifdef _WIN32
# include <winsock2.h>
# include <ws2tcpip.h>
#else /* POSIX */
# include <netinet/in.h>
# include <sys/select.h>
# include <sys/socket.h>
# include <netdb.h>
# include <unistd.h>
# include <error.h>
# define closesocket close
# define Sleep(x) usleep(x * 1000)
#endif

void urlencode(char* enc, const char* url)
{
	char* d = enc;
	for(const char* s = url; *s; s++)
	{
		switch(*s)
		{
		case 'a' ... 'z':
		case 'A' ... 'Z':
		case '0' ... '9':
		case '.':
			*d++ = *s;
			break;
		default:
			sprintf(d, "%%%02X", (unsigned int)*s);
			d += 3;
		}
	}
	*d = 0;
}

int main(int argc, char** argv)
{
	const char* url = 0;
	for(int i = 1; i < argc; i++)
	{
		if(memcmp(argv[i], "https://", 8) == 0 || memcmp(argv[i], "http://", 7) == 0)
		{
			url = argv[i];
			break;
		}
	}
	if(!url)
		return 1;

	char enc[1024];
	urlencode(enc, url);

#ifdef _WIN32
	WSADATA wsa_data;
	if(WSAStartup(MAKEWORD(2, 2), &wsa_data) != 0)
	{
		return 2;
	}
#endif

	int retries = 60 * 1000 / 250;
retry:;
	int sock = socket(AF_INET, SOCK_STREAM, 0);
	if(sock < 0)
	{
		return 3;
	}

	struct sockaddr_in sin;
	sin.sin_family = AF_INET;
	sin.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
	sin.sin_port = htons(5000);
	if(connect(sock, (struct sockaddr*)&sin, sizeof sin) < 0)
	{
		return 4;
	}

	char buf[128 * 1024];
	int sz = sprintf(buf, "POST /api/ytdl/%s HTTP/1.0\r\nConnection: close\r\n\r\n", enc);
	if(send(sock, buf, sz, 0) != sz)
	{
		return 5;
	}
	Sleep(250);

	if((sz = recv(sock, buf, sizeof buf-1, MSG_WAITALL)) <= 0)
	{
		return 6;
	}
	buf[sz] = 0;
	closesocket(sock);

	int status = 0;
	if(sscanf(buf, "HTTP/%*c.%*c %d %*[^\r\n]", &status) != 1)
	{
		return 7;
	}

	switch(status)
	{
	case 201:
	case 202:
		Sleep(250);
		if(retries--)
			goto retry;
		return 11;
	case 200:
	case 500:
		break;
	default:
		return 8;
	}

	const char* data = strstr(buf, "\r\n\r\n");
	if(data)
	{
		data += 4;
	}
	else
	{
		data = strstr(buf, "\n\n");
		if(data)
		{
			data += 2;
		}
	}

	if(!data)
	{
		fputs(buf, stderr);
		return 9;
	}

	puts(data);
	return status == 200 ? 0 : 10;
}
