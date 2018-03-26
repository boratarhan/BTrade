import threading
import time
c = threading.Condition()
flag = 0      #shared between Thread_A and Thread_B
val = 20
        
class Thread_A(object):
    
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

        t1 = threading.Thread( target=self.run1 )
        t2 = threading.Thread( target=self.run2 )
        t1.start()
        t2.start()
        t1.join()
        t2.join()

    def run1(self):
        global flag
        global val     #made global here
        while True:
            c.acquire()
            if flag == 0:
                print("A: val=" + str(val))
                time.sleep(0.1)
                flag = 1
                val = val+10
                c.notify_all()
            else:
                c.wait()
            c.release()

    def run2(self):
        global flag
        global val    #made global here
        while True:
            c.acquire()
            if flag == 1:
                print("B: val=" + str(val))
                time.sleep(0.5)
                flag = 0
                val = val+10
                c.notify_all()
            else:
                c.wait()
            c.release()


a = Thread_A("myThread_name_A")
