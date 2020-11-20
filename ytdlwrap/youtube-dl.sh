#!/bin/bash

uriencode() {
  s="${1//'%'/%25}"
  s="${s//' '/%20}"
  s="${s//'"'/%22}"
  s="${s//'#'/%23}"
  s="${s//'$'/%24}"
  s="${s//'&'/%26}"
  s="${s//'+'/%2B}"
  s="${s//','/%2C}"
  s="${s//'/'/%2F}"
  s="${s//':'/%3A}"
  s="${s//';'/%3B}"
  s="${s//'='/%3D}"
  s="${s//'?'/%3F}"
  s="${s//'@'/%40}"
  s="${s//'['/%5B}"
  s="${s//']'/%5D}"
  printf %s "$s"
}

while [ "$#" -gt 0 -a "$1" != "--" ]
do
	shift
done

if [ "$1" = "--version" ]
then
	date +%Y.%m.%d # spoof
	exit 0
fi

shift

URL="$(uriencode "$1")"

while R=$(curl -fs -X POST "http://127.0.0.1:5000/api/ytdl/$URL")
do
	if grep -Fq '{' <<<"$R"
	then
		echo "$R"
		exit 0
	fi
	sleep 0.25
done
rc=$?
[ "$rc" -ne 22 ] || curl -s -X POST "http://127.0.0.1:5000/api/ytdl/$URL" >&2
exit $rc
