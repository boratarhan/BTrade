cd "C:\\Users\\bora\\Documents\\GitHub\\BTrade\\source_system"
call activate py375
start python C:\\Users\\bora\\Documents\\GitHub\\BTrade\\source_system\\forwarder.py 5555
sleep 30
start python C:\\Users\\bora\\Documents\\GitHub\\BTrade\\source_system\\forwarder.py 5557
sleep 30
start python C:\\Users\\bora\\Documents\\GitHub\\BTrade\\source_system\\portfolio.py practice 5554
sleep 30
start python C:\\Users\\bora\\Documents\\GitHub\\BTrade\\source_system\\strategySMA.py EUR_USD S5 practice 5556 10
sleep 30
start python C:\\Users\\bora\\Documents\\GitHub\\BTrade\\source_system\\feeder.py EUR_USD S5 practice 5555
sleep 30
call conda deactivate
