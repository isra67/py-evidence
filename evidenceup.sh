#! /bin/bash

PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/node/bin

pustaj() {
	while true
	do
		## working dir
		cd /home/pi/is-kivy-test

		## Inoteska Evidence python App
		/usr/bin/python main.py
		sleep 5
	done
}

sleep 15

## working dir
#cd /home/pi/is-kivy-test

pustaj >& /dev/null &
