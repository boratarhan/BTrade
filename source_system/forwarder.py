import zmq
import time
import sys

class forwarder(object):
    ''' 
    Forwarder object acts as a stable point between critical objects
    If any of the critical objects fail, this aviods an entire system shut-down
    '''

    def __init__(self,socket_number):

        self.context = zmq.Context(1)
        self.frontend_socket_number = socket_number
        self.backend_socket_number = socket_number+1

        print('Forwarder is ready')
        
        # Socket facing clients 
        frontend = self.context.socket(zmq.SUB)
        frontend.bind("tcp://127.0.0.1:{}".format(self.frontend_socket_number))
                
        frontend.setsockopt_string(zmq.SUBSCRIBE, "")
                
        # Socket facing services
        backend = self.context.socket(zmq.PUB)
        backend.bind("tcp://127.0.0.1:{}".format(self.backend_socket_number))
        
        zmq.device(zmq.FORWARDER, frontend, backend)
        
        time.sleep(5) # Since binding takes time, sleep for a few seconds before running
        
if __name__ == "__main__":
    
    try:

        socket_number = int(sys.argv[1])
        
        f1 = forwarder(socket_number)
       
    except:
        
        print( 'Error in forwarder object' )
        
'''
About ZMQ:
https://www.randonomicon.com/zmq/2018/09/19/zmq-bind-vs-connect.html

Use BIND for stable tings & Use CONNECT for volatile things
Use BIND when listening & Use CONNECT when broadcasting
Use BIND for incoming & Use CONNECT for outgoing
Use BIND for long-lived process & Use CONNECT for short-lived process

'''