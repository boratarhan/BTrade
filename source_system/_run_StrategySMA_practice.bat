cd "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system"
call activate py375
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\forwarder.py" 5555
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\forwarder.py" 5557
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\forwarder.py" 5551
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\forwarder.py" 5553
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\portfolio.py" practice 5551
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\strategySMA.py" EUR_USD S5 practice 5556 5552 10
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\feeder.py" EUR_USD S5 practice 5555
sleep 30
call conda deactivate
