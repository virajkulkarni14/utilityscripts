#!/bin/bash

#	curl "http://freegeoip.net/json/$1" | jsonpretty
# curl ifconfig.me
curl "http://api.hostip.info/get_json.php?ip=$1&position=true"
