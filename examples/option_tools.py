import refinitiv.dataplatform as rdp
import pandas as pd
from datetime import timedelta
from datetime import datetime

rdp.open_desktop_session('DEFAULT_CODE_BOOK_APP_KEY')


def get_exchange_code(asset):
    
    # build search query to find exchange codes where the option on the given underlying is traded  
    response = rdp.Search.search(
        query = asset,
        filter = "SearchAllCategory eq 'Options' and Periodicity eq 'Monthly' ",
        select = ' RIC, DocumentTitle, UnderlyingQuoteRIC,Periodicity, ExchangeCode',
        navigators = "ExchangeCode",
        top = 10000
    )
    result = response.data.raw["Navigators"]["ExchangeCode"]
    
    # store a=exchange codes in a list
    exchange_codes = []
    for i in range(len(result['Buckets'])):
        code = result['Buckets'][i]['Label']
        exchange_codes.append(code)
    return exchange_codes


def check_ric(ric, maturity, ident):
    exp_date = pd.Timestamp(maturity)
    
    # get start and end date for get_historical_price_summaries query (take current date minis 90 days period)
    sdate = (datetime.now() - timedelta(90)).strftime('%Y-%m-%d')
    edate = datetime.now().strftime('%Y-%m-%d')
    
    # check if option is matured. If yes, add expiration syntax 
    # and recalculate start and end date of the query (take expiration day minus 90 days period)
    if pd.Timestamp(maturity) < datetime.now():
        ric = ric + '^' + ident[str(exp_date.month)]['exp'] + str(exp_date.year)[-2:]
        sdate = (exp_date - timedelta(90)).strftime('%Y-%m-%d')
        edate = exp_date.strftime('%Y-%m-%d')
    
    # request option prices. Please note, there is no settle price for OPRA traded options
    if ric.split('.')[1][0] == 'U':
        prices = rdp.get_historical_price_summaries(ric,  start = sdate, end = edate, interval = rdp.Intervals.DAILY,
                                                fields = ['BID','ASK','TRDPRC_1'])
    else:
        prices = rdp.get_historical_price_summaries(ric,  start = sdate, end = edate, interval = rdp.Intervals.DAILY,
                                                fields = ['BID','ASK','TRDPRC_1', 'SETTLE'])
    return ric, prices


def get_exp_month(exp_date, opt_type):
    
    # define option expiration identifiers
    ident = {'1': {'exp': 'A','C': 'A', 'P': 'M'}, 
           '2': {'exp': 'B', 'C': 'B', 'P': 'N'}, 
           '3': {'exp': 'C', 'C': 'C', 'P': 'O'}, 
           '4': {'exp': 'D', 'C': 'D', 'P': 'P'},
           '5': {'exp': 'E', 'C': 'E', 'P': 'Q'},
           '6': {'exp': 'F', 'C': 'F', 'P': 'R'},
           '7': {'exp': 'G', 'C': 'G', 'P': 'S'}, 
           '8': {'exp': 'H', 'C': 'H', 'P': 'T'}, 
           '9': {'exp': 'I', 'C': 'I', 'P': 'U'}, 
           '10': {'exp': 'J', 'C': 'J', 'P': 'V'}, 
           '11': {'exp': 'K', 'C': 'K', 'P': 'W'}, 
           '12': {'exp': 'L', 'C': 'L', 'P': 'X'}}
    
    # get expiration month code for a month
    if opt_type.upper() == 'C':
        exp_month = ident[str(exp_date.month)]['C']
    elif opt_type.upper() == 'P':
        exp_month = ident[str(exp_date.month)]['P']
        
    return ident, exp_month


def get_ric_opra(asset, maturity, strike, opt_type):
    exp_date = pd.Timestamp(maturity)
    
    # trim underlying asset's RIC to get the required part for option RIC
    if asset[0] == '.': # check if the asset is an index or an equity
        asset_name = asset[1:] # get the asset name - we remove "." symbol for index options
    else:
        asset_name = asset.split('.')[0] # we need only the first part of the RICs for equities
    
    ident = {'1': {'exp': 'A', 'C_bigStrike': 'a','C_smallStrike': 'A', 'P_bigStrike': 'm', 'P_smallStrike': 'M'}, 
           '2': {'exp': 'B', 'C_bigStrike': 'b','C_smallStrike': 'B', 'P_bigStrike': 'n', 'P_smallStrike': 'N'}, 
           '3': {'exp': 'C', 'C_bigStrike': 'c','C_smallStrike': 'C', 'P_bigStrike': 'o', 'P_smallStrike': 'O'}, 
           '4': {'exp': 'D', 'C_bigStrike': 'd','C_smallStrike': 'D', 'P_bigStrike': 'p', 'P_smallStrike': 'P'},
           '5': {'exp': 'E', 'C_bigStrike': 'e','C_smallStrike': 'E', 'P_bigStrike': 'q', 'P_smallStrike': 'Q'},
           '6': {'exp': 'F', 'C_bigStrike': 'f','C_smallStrike': 'F', 'P_bigStrike': 'r', 'P_smallStrike': 'R'},
           '7': {'exp': 'G', 'C_bigStrike': 'g','C_smallStrike': 'G', 'P_bigStrike': 's', 'P_smallStrike': 'S'}, 
           '8': {'exp': 'H', 'C_bigStrike': 'h','C_smallStrike': 'H', 'P_bigStrike': 't', 'P_smallStrike': 'T'}, 
           '9': {'exp': 'I', 'C_bigStrike': 'i','C_smallStrike': 'I', 'P_bigStrike': 'u', 'P_smallStrike': 'U'}, 
           '10': {'exp': 'J', 'C_bigStrike': 'j','C_smallStrike': 'J', 'P_bigStrike': 'v', 'P_smallStrike': 'V'}, 
           '11': {'exp': 'K', 'C_bigStrike': 'k','C_smallStrike': 'K', 'P_bigStrike': 'w', 'P_smallStrike': 'W'}, 
           '12': {'exp': 'L', 'C_bigStrike': 'l','C_smallStrike': 'L', 'P_bigStrike': 'x', 'P_smallStrike': 'X'}}
    
    # get expiration month code for a month
    if opt_type.upper() == 'C':
        if strike > 999.999:
            exp_month = ident[str(exp_date.month)]['C_bigStrike']
        else:
            exp_month = ident[str(exp_date.month)]['C_smallStrike']
            
    # calculate the strike price and get expiration month code for a month for put options
    elif opt_type.upper() == 'P':
        if strike > 999.999:
            exp_month = ident[str(exp_date.month)]['P_bigStrike'] 
        else:
            exp_month = ident[str(exp_date.month)]['P_smallStrike']
    
    # get strike prrice
    if type(strike) == float:
        int_part = int(strike)
        dec_part = str(str(strike).split('.')[1])
    else:
        int_part = int(strike)
        dec_part = '00'
    if len(dec_part) == 1:
        dec_part = dec_part + '0'
 
    if int(strike) < 10:
        strike_ric = '00' + str(int_part) + dec_part
    elif int_part >= 10 and int_part < 100:
        strike_ric = '0' + str(int_part) + dec_part
    if int_part >= 100 and int_part < 1000:
        strike_ric = str(int_part) + dec_part
    elif int_part >= 1000 and int_part < 10000:
        strike_ric = str(int_part) + '0'
    elif int_part >= 10000 and int_part < 20000:
        strike_ric = 'A' + str(int_part)[-4:]
    elif int_part >= 20000 and int_part < 30000:
        strike_ric = 'B' + str(int_part)[-4:]      
    elif int_part >= 30000 and int_part < 40000:
        strike_ric = 'C' + str(int_part)[-4:]
    elif int_part >= 40000 and int_part < 50000:
        strike_ric = 'D' + str(int_part)[-4:]
        
    # build initial ric
    ric = asset_name + exp_month + str(exp_date.day) + str(exp_date.year)[-2:] + strike_ric + '.U'
    # check ric validity
    ric, prices = check_ric(ric, maturity, ident)
    
    # return valid rics or append to the possible_ric list if no price is found
    possible_rics = [] 
    if prices is not None:
        return ric, prices
    else:
        possible_rics.append(ric)
        print(f'Here is a list of possible RICs {possible_rics}, however we could not find any prices for those!')
    return ric, prices


def get_ric_hk(asset, maturity, strike, opt_type):
    exp_date = pd.Timestamp(maturity)
    
    # get asset name and strike price for the asset
    if asset[0] == '.': 
        asset_name = asset[1:] 
        strike_ric = str(int(strike))
    else:
        asset_name = asset.split('.')[0]
        strike_ric = str(int(strike * 100))
     
    # get expiration month codes
    ident, exp_month = get_exp_month(exp_date, opt_type)
 
    possible_rics = []
    # get rics for options on indexes. Return if valid add to the possible_rics list if no price is found
    if asset[0] == '.':
        ric = asset_name + strike_ric + exp_month + str(exp_date.year)[-1:] + '.HF'
        ric, prices = check_ric(ric, maturity, ident)
        if prices is not None:
            return ric, prices
        else:
            possible_rics.append(ric)
    else:
        # get rics for options on equities. Return if valid add to the possible_rics list if no price is found
        # there could be several generations of options depending on the number of price adjustments due to a corporate event
        # here we use 4 adjustment opportunities.
        for i in range(4): 
            ric = asset_name + strike_ric + str(i)+ exp_month + str(exp_date.year)[-1:] + '.HK'
            ric, prices = check_ric(ric, maturity, ident)
            if prices is not None:
                 return ric, prices # we return ric and prices for the first found ric (we don't check for other adjusted rics)
            else:
                possible_rics.append(ric)
    print(f'Here is a list of possible RICs {possible_rics}, however we could not find any prices for those!')
    return  ric, prices


def get_ric_ose(asset, maturity, strike, opt_type):
    exp_date = pd.Timestamp(maturity)
 
    if asset[0] == '.':
        asset_name = asset[1:]
    else:
        asset_name = asset.split('.')[0]
    strike_ric = str(strike)[:3]
        
    ident, exp_month = get_exp_month(exp_date, opt_type)
    
    possible_rics = []
    if asset[0] == '.':
        # Option Root codes for indexes are different from the RIC, so we rename where necessery
        if asset_name == 'N225':
            asset_name = 'JNI'
        elif asset_name == 'TOPX':
            asset_name = 'JTI'
        # we consider also J-NET (Off-Auction(with "L")) and High  frequency (with 'R') option structures 
        for jnet in ['', 'L', 'R']:
            ric = asset_name + jnet + strike_ric + exp_month + str(exp_date.year)[-1:] + '.OS'
            ric, prices = check_ric(ric, maturity, ident)
            if prices is not None:
                return ric, prices
            else:
                possible_rics.append(ric)
    else:
        generations = ['Y', 'Z', 'A', 'B', 'C'] # these are generation codes similar to one from HK 
        for jnet in ['', 'L', 'R']:
            for gen in generations:
                ric = asset_name + jnet + gen + strike_ric + exp_month + str(exp_date.year)[-1:] + '.OS'
                ric, prices = check_ric(ric, maturity, ident)
                if prices is not None:
                    return ric, prices
                else:
                    possible_rics.append(ric)
    print(f'Here is a list of possible RICs {possible_rics}, however we could not find any prices for those!')
    return  ric, prices


def get_ric_eurex(asset, maturity, strike, opt_type):
    exp_date = pd.Timestamp(maturity)
 
    if asset[0] == '.': 
        asset_name = asset[1:]
        if asset_name == 'FTSE':
            asset_name = 'OTUK'
        elif asset_name == 'SSMI':
            asset_name = 'OSMI'
        elif asset_name == 'GDAXI':
            asset_name = 'GDAX'
        elif asset_name == 'ATX':
            asset_name = 'FATXA'
        elif asset_name == 'STOXX50E':
            asset_name = 'STXE'           
    else:
        asset_name = asset.split('.')[0]
        
    ident, exp_month = get_exp_month(exp_date, opt_type)
        
    if type(strike) == float:
        int_part = int(strike)
        dec_part = str(str(strike).split('.')[1])[0]
    else:
        int_part = int(strike)
        dec_part = '0'      
        
    if len(str(int(strike))) == 1:
        strike_ric = '0' + str(int_part) + dec_part
    else:
        strike_ric = str(int_part) + dec_part
    
    possible_rics = []
    generations = ['', 'a', 'b', 'c', 'd']
    for gen in generations:
        ric = asset_name + strike_ric  + gen + exp_month + str(exp_date.year)[-1:] + '.EX'
        ric, prices = check_ric(ric, maturity, ident)
        if prices is not None:
            return ric, prices
        else:
            possible_rics.append(ric)
    print(f'Here is a list of possible RICs {possible_rics}, however we could not find any prices for those!')
    return  ric, prices


def get_ric_ieu(asset, maturity, strike, opt_type):
    exp_date = pd.Timestamp(maturity)
    
    if asset[0] == '.':
        asset_name = asset[1:]
        if asset_name == 'FTSE':
            asset_name = 'LFE'       
    else:
        asset_name = asset.split('.')[0] 
        
    ident, exp_month = get_exp_month(exp_date, opt_type)
 
    if len(str(int(strike))) == 2:
        strike_ric = '0' + str(int(strike))
    else:
        strike_ric = str(int(strike))
        
    if type(strike) == float and len(str(int(strike))) == 1:
        int_part = int(strike)
        dec_part = str(str(strike).split('.')[1])[0]        
        strike_ric = '0' + str(int_part) + dec_part
    
    possible_rics = []
    generations = ['', 'a', 'b', 'c', 'd']
    for gen in generations:
        ric = asset_name + strike_ric  + gen + exp_month + str(exp_date.year)[-1:] + '.L'
        ric, prices = check_ric(ric, maturity, ident)
        if prices is not None:
            return ric, prices
        else:
            possible_rics.append(ric)
    print(f'Here is a list of possible RICs {possible_rics}, however we could not find any prices for those!')
    return  ric, prices


def get_optionRic(isin, maturity, strike, opt_type):
    
    # define covered exchanges along with functions to get RICs from
    exchanges = {'OPQ': get_ric_opra,
           'IEU': get_ric_ieu,
           'EUX': get_ric_eurex,
           'HKG': get_ric_hk,
           'HFE': get_ric_hk,
           'OSA': get_ric_ose}
    
    # convert ISIN to RIC
    df = rdp.convert_symbols( isin, from_symbol_type = "ISIN" , to_symbol_types = "RIC")
    ricUnderlying = df['RIC'][0]
    
    # get exchanges codes where the option on the given asset is traded
    exchnage_codes = get_exchange_code(ricUnderlying)
    
    # get the list of (from all available and covered exchanges) valid rics and their prices
    option_rics = [] 
    priceslist = []
    for exch in exchnage_codes:
        if exch in exchanges.keys():
            ric, prices = exchanges[exch](ricUnderlying, maturity, strike, opt_type)
            if prices is not None:
                option_rics.append(ric)
                priceslist.append(prices)
                print(f'Option RIC for {exch} exchange is successfully constructed')     
        else:
            print(f'The {exch} exchange is not supported yet')
    return option_rics, priceslist
