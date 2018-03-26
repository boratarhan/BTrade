import zmq
import time
import sys

class forwarder(object):
    ''' Forwarder object acts as a stable point between objects
    '''

    def __init__(self,socket_number):

        self.context = zmq.Context(1)
        self.frontend_socket_number = socket_number
        self.backend_socket_number = socket_number+1
        
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