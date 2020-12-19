cd "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system"
call activate py375
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\feeder.py" AUD_USD S5 live 5555
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\feeder.py" EUR_USD S5 live 5555
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\feeder.py" GBP_USD S5 live 5555
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\feeder.py" NZD_USD S5 live 5555
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\feeder.py" USD_CAD S5 live 5555
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\feeder.py" USD_CHF S5 live 5555
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\feeder.py" USD_JPY S5 live 5555
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\feeder.py" USD_TRY S5 live 5555
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\feeder.py" AUD_NZD S5 live 5555
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\feeder.py" EUR_CHF S5 live 5555
sleep 30
start python "C:\\Users\\boratarhan\\Google Drive\\_Github\\BTrader\\source_system\\feeder.py" AUD_JPY S5 live 5555
sleep 30
call conda deactivate
