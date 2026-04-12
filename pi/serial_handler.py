"""
Reads raw bytes from both USB ports, 
splits on \n, 
parses the TYPE:ID:VALUE format, 
and hands off each message to the game logic. 

Also sends commands back out. 
Nothing in about cooking times or win conditions.
"""