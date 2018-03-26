
import zmq
 
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.setsockopt_string(zmq.SUBSCRIBE, '')
socket.connect("tcp://127.0.0.1:5555")
 
while True:
    msg = socket.recv_string()
    print(msg)



#import zmq
# 
#if __name__ == "__main__":
#    context = zmq.Context()
#    socket = context.socket(zmq.SUB)
#    socket.setsockopt_string(zmq.SUBSCRIBE, '')
#    socket.connect("tcp://127.0.0.1:5555")
# 
#    while True:
#        msg = socket.recv_string()
#        print(msg)
        
    