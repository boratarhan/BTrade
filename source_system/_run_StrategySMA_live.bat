cd "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system"
call activate py375
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\forwarder.py" 5555
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\forwarder.py" 5557
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\portfolio.py" live 5554
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\strategySMA.py" EUR_USD S5 live 5556 10
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\feeder.py" EUR_USD S5 live 5555
sleep 30
call conda deactivate
