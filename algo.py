from pyoanda import Client, PRACTICE,Order
import pandas as pd
import numpy as np
from datetime import datetime
import time


trading = {#'CN50_USD': {'buy_sl': 0.02,'buy_tp': 0.015,'dev': 1.5,'sell_sl': 0.01,'sell_tp': 0.015,'tf': 'H1','units': 1},
 'CORN_USD': {'buy_sl': 0.03,'buy_tp': 0.045,'dev': 2,'sell_sl': 0.035,'sell_tp': 0.045,'tf': 'H6','units': 40},
 'DE10YB_EUR': {'buy_sl': 0.004,'buy_tp': 0.005,'dev': 1.5,'sell_sl': 0.004,'sell_tp': 0.004,'tf': 'H1','units': 10},
# 'HK33_HKD': {'buy_sl': 0.04,'buy_tp': 0.047,'dev': 1.6,'sell_sl': 0.04,'sell_tp': 0.06,'tf': 'D','units': 1},
# 'IN50_USD': {'buy_sl': 0.03,'buy_tp': 0.06,'dev': 2,'sell_sl': 0.01,'sell_tp': 0.02,'tf': 'D','units': 1, 'cond':'buy'},
# 'NATGAS_USD': {'buy_sl': 0.062,'buy_tp': 0.19,'dev': 2,'sell_sl': 0.1,'sell_tp': 0.1,'tf': 'D','units': 20},
 'NL25_EUR': {'buy_sl': 0.011,'buy_tp': 0.014,'dev': 1.8,'sell_sl': 0.015,'sell_tp': 0.015,'tf': 'H1','units': 1},
 'SG30_SGD': {'buy_sl': 0.02,'buy_tp': 0.018,'dev': 1.9,'sell_sl': 0.014,'sell_tp': 0.018,'tf': 'H4','units': 1},
# 'SOYBN_USD': {'buy_sl': 0.03,'buy_tp': 0.035,'dev': 1.9,'sell_sl': 0.023,'sell_tp': 0.03,'tf': 'H6','units': 16},
 'SUGAR_USD': {'buy_sl': 0.06,'buy_tp': 0.08,'dev': 1.8,'sell_sl': 0.05,'sell_tp': 0.05,'tf': 'H8','units': 400},
 'TWIX_USD': {'buy_sl': 0.015,'buy_tp': 0.025,'dev': 2,'sell_sl': 0.02,'sell_tp': 0.025,'tf': 'H6','units': 1},
 'UK10YB_GBP': {'buy_sl': 0.015,'buy_tp': 0.025,'dev': 1.9,'sell_sl': 0.014,'sell_tp': 0.02,'tf': 'D','units': 2},
# 'US2000_USD': {'buy_sl': 0.04,'buy_tp': 0.06,'dev': 1.8,'sell_sl': 0.045,'sell_tp': 0.055,'tf': 'D','units': 1},
# 'WHEAT_USD': {'buy_sl': 0.03,'buy_tp': 0.04,'dev': 2,'sell_sl': 0.03,'sell_tp': 0.035,'tf': 'H6','units': 40},
 'WTICO_USD': {'buy_sl': 0.075,'buy_tp': 0.11,'dev': 1.9,'sell_sl': 0.063,'sell_tp': 0.08,'tf': 'D','units': 1}}

#####################################################
client = Client(
    environment=PRACTICE,
    account_id="",
    access_token=""
)
#####################################################
def plot_me(df,plr,symbol):
    import matplotlib.pyplot as plt
    df['close'].plot()
    plt.plot(plr,'c-')
    plt.plot(df['stdev_up'],'r')
    plt.plot(df['stdev_down'],'r')
    x = list(range(len(df['close'])))
    for i in range(len(df['close'])):
        plt.plot((x[i],x[i]), (df['low'][i],df['high'][i]), '0.4',linewidth=1)
    ax=plt.gca()
    ax.set_facecolor('black')
    t=str(datetime.now())[0:16]
    t=t[:13]+"-"+t[14:]
    plt.title("%s @%s for %s" %(symbol,trading[symbol]['tf'], trading[symbol]['dev']))
    mng = plt.get_current_fig_manager()
    mng.full_screen_toggle()
    #if save: plt.savefig("reg-%s-%s-%s.png" % (symbol,trading[symbol]['tf'],t))
    plt.show()
    plt.close()

def get_positions():
    return pd.DataFrame(client.get_positions()['positions'])

def get_prices(s_list):
    return pd.DataFrame(client.get_prices(instruments=','.join(s_list),stream=False)['prices'])

def get_bid(symbol):
    prices = get_prices([symbol])
    return prices['bid'][prices['instrument'] == symbol][0]

def market_order(symbol, units, side):
    bid = get_bid(symbol)
    if side == 'buy':
        sl = "{0:.1f}".format(bid * (1-trading[symbol][side+'_sl']))
        tp = "{0:.1f}".format(bid * (1+trading[symbol][side+'_tp']))
    else:
        sl = "{0:.1f}".format(bid * (1+trading[symbol][side+'_sl']))
        tp = "{0:.1f}".format(bid * (1-trading[symbol][side+'_tp']))
    market_order = Order(
        instrument=symbol,
        units=units,
        side=side,
        type="market",
        stopLoss = sl,
        takeProfit = tp
    )
    return market_order

def open_trade(symbol, side):
    units = trading[symbol]['units']
    pos_df = get_positions()
    if not pos_df.empty:
        if symbol in pos_df.instrument.tolist():
            if pos_df['side'][pos_df['instrument'] == symbol][0] == side:
                return 'exists'
            else:
                u_cur = pos_df['units'][pos_df['instrument'] == symbol][0]
                return client.create_order(order=market_order(symbol, units + u_cur, side))
    return client.create_order(order=market_order(symbol, units, side))
########################################################
def send_email(res):
    import requests
    return requests.post(
        "https://api.mailgun.net/v3/sandboxb8199fa5adb34ba388ea729a11ad249e.mailgun.org/messages",
        auth=("api", "key-"),
        data={"from": "Mailgun Sandbox <postmaster@sandboxb8199fa5adb34ba388ea729a11ad249e.mailgun.org>",
              "to": "",
              "subject": "Oanda Py",
              "text": res})
##########################################################
def getdata(symbol):
    candles=client.get_instrument_history(
        count=120,
        instrument=symbol,
        candle_format="midpoint",
        granularity = trading[symbol]['tf']
    )["candles"]
    op=pd.DataFrame(candles)
    del candles
    op=pd.DataFrame(op,columns=('openMid','closeMid','highMid','lowMid','time','volume'))
    op.columns=('open','close','high','low','time','volume')
    return op
##########################################################3
def poly_pos(df,pos):
    if df['low'][pos]<df['stdev_down'][pos] and df['high'][pos]>df['stdev_up'][pos]:
        return 'nn'
    elif df['low'][pos]<df['stdev_down'][pos]:
        return "buy"
    elif df['high'][pos]>df['stdev_up'][pos]:
        return "sell"
    else:
        return "nn"
###########################################
def polyreg(symbol):
    dev = trading[symbol]['dev']
    df=getdata(symbol)
    l=len(df['close'])
    y = df['close']
    x = list(range(l))

    rg=np.polyfit(x,y,3)
    pr=np.poly1d(rg)

    x_new = np.linspace(x[0], x[-1], 120)
    plr = pr(x_new)

    sigma = np.std([tup-tupp for tup,tupp in zip(y,plr) ])
    moas=dev*sigma
    df['stdev_up']=[i+moas for i in plr]
    df['stdev_down']=[i-moas for i in plr]

    plot_me(df,plr,symbol)

    return(poly_pos(df,l-1))

def body():
    for s in trading.keys():
        print(s)
        sit = polyreg (s)
        print(sit)
        try:
            cond = trading[s]['cond']
        except:
            cond = ''
        if (sit == cond) or (sit != 'nn'):
            try:
                trade = open_trade(s,sit)
                if trade != 'exists':
                    send_email(str(trade))
                    print(trade)
            except:
                print("Could not open %s trade on %s" % (sit,s))
                send_email("Could not open %s trade on %s" % (sit,s))

while True:
    ctmin=str(datetime.now())[14:16]
    if  ctmin =='01':
        body()
    mint=int(ctmin)
    for o in [1,61]:
        if o>mint:
            mint=o-mint
            break
    sec=str(datetime.now())[17:26]
    sec=float(sec)
    print("sleeping for ",mint," minus",sec," @ ",datetime.now())
    time.sleep(60*mint-sec)
