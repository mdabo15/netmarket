@echo off
set NITRO_HOST=0.0.0.0
set NITRO_PORT=3000
cd /d D:\netmarket\frontend
node .output/server/index.mjs >> D:\netmarket\frontend\prod-server.log 2>&1
