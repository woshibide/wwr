# diary

when accessing the radio browser it will be asking for ssl certificate,
so the user should have one before trying to access the api
>>> kind of sorted, the deal was that python3.9 is old and no certificates are passed to it
>>> adding certifi and `import ssl` resolved the issue

program flow should be controlled by the script in a way so that 
if one part of the program fails it doesnt affect execution of the rest




