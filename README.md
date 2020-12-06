```
usage: messenger.py [-h] [-a A] [-p P]

# ----------------------------------------------- #
#   UDP Messenger, PKS assigment 2. v.1           #
#       Author:     Michal Paulovic               #
#       STU-FIIT:   xpaulovicm1                   #
#       Github:     paulotheblack                 #
#   https://github.com/paulotheblack/udp_msngr    #
# ----------------------------------------------- #

optional arguments:
  -h, --help  show this help message and exit
  -a A        Local IP address to bind
  -p P        Local Port to bind
  -f F        Path to save files
```

Assigment tasks:
- [x] Set IP and port
- [x] Implement ARQ (After each batch)
- [x] Send 2MB File
- [x] Implement Keep Alive

UI:

```
":c"    to establish connection
":m"    to send message
":em"   error message simulation
":f"    to send file
":ef"   error file simulation
":s"    to change settings
":kk"   stop sending keepalive
":q"    to exit program
```