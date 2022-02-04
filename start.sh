#!/bin/sh

echo "Starting lavalink server..."

cd lavalink
nohup java -jar LavalinkPatch.jar > logs/lavalog.txt &
javaPID=$!

echo "Lavalink PID: $javaPID"

cd ../

sleep 5

echo "Starting Athena..."

nohup python3 bot.py > lavalink/logs/botlog.txt & 
pyPID=$!

echo "bot.py PID: $pyPID"

echo "Success! Appending output to lavalink/logs."

echo "kill -9 $javaPID\nkill -9 $pyPID" > stop.sh
chmod u+x stop.sh

echo "Use ./stop.sh to kill all background processes."