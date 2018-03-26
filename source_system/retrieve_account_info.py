import v20
import configparser

try:
    config = configparser.ConfigParser()
    config.read('..\..\configinfo.cfg')
    
except:
    print( 'Error in reading configuration file' )
    
ctx = v20.Context( 'api-fxtrade.oanda.com',
                  443,
                  True,
                  application='sample_code',
                  token=config['oanda']['access_token_live'],
                  datetime_format='RFC3339')

response = ctx.account.instruments(config['oanda_v20']['account_number_live']) 

instruments = response.get('instruments')

for instrument in instruments:
    ins = instrument.dict()
    print('%20s | %10s' % (ins['displayName'],ins['name']))  
            
            

#acc_summary = response.get('account')
#
#print( acc_summary.dict() )
#
## Information about the last few trades
#
## This is not working, do not know if it is vecause of lack otf transactions.
#response = ctx.transaction.since(ctx.account.summary(config['oanda_v20']['account_number_live'], id=1)  
#transactions = response.get('transactions')  
#
#for trans in transactions:
#    trans = trans.dict()
#    templ = '%s | %14s | %12s'
#    print(templ % (trans['time'], trans['instrument'], trans['units']))