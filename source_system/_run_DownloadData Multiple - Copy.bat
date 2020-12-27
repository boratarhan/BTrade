cd "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system"
call activate py375
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\feeder.py" USD_CAD S5 live 5555
sleep 30
call conda deactivate
