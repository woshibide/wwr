# hello
this is a web-app radio, a wrapper for (radio-browser)[https://www.radio-browser.info/]
that is meant to work with Raspberry Pi Zero 2w, but can also work on anything that
is capable of running flask and streaming audio

## diary
when accessing the radio browser it will be asking for ssl certificate,
so the user should have one before trying to access the api
>>> kind of sorted, the deal was that python3.9 is old and no certificates are passed to it
>>> adding certifi and `import ssl` resolved the issue

program flow should be controlled by the script in a way so that 
if one part of the program fails it doesnt affect execution of the rest

volume control updates so fast it deletes user's favorite stations settings, lol 

`wget-log` makes me paranoid, i have no clue how come that file appears 





17 pin takes power 3.3 voltage (yellow wire)
next are the next
18 - 1 
19 - 2
20 - 3
...
27 - 10

button
pin 15-16
we ask the opposite pin to where the voltage is going to get state change 
both are io



pin 1 - lamp





