
import time
from random import choice
from random import randrange
 
import zmq
 
stock_symbols = ['RAX', 'EMC', 'GOOG', 'AAPL', 'RHAT', 'AMZN']
 
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://127.0.0.1:5555")
 
while True:
    time.sleep(.01)
    # pick a random stock symbol
    stock_symbol = choice(stock_symbols)
    # set a random stock price
    stock_price = randrange(1, 100)
 
    # compose the message
    msg = "{0} ${1}".format(stock_symbol, stock_price)
 
    print("Sending Message: {0}".format(msg))
 
    # send the message
    socket.send_string(msg)
        
