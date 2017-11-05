import json
import numpy as np
import talib as tl
import datetime

chart = {
'__isStock': True,
'title': {
    'text': '账户净值变化表'
},
'xAxis': [{
    'type': 'datetime'
}],
'yAxis' : [{
    'title': {'text': '价'},
    'opposite': False,
  }],
'series': [
{
    'name': '基准净值',
    'id': 'standard',
    'data': []
},
{
     'name': '账户净值',
     'id': 'balance',
     'color': 'red',
     'data': []
}
]
}

def main():
    #初始数据设置
    Tradetime = [0, 4, 8, 12, 16, 20]    #设置交易时间段，单位为小时
    stop_loss_line = 10    #设置回撤止损线，默认10%
    max_balance = None    #用于记录账户净值最大值
    now_balance = None    #用于计算账户实时净值
    initial_balance = None #用于计算账户初始净值
    open_balance = None    #用于计算账户开仓时的净值
    mini_buy_money = 5    #最小买入量（钱）
    mini_sell_stocks = 0.002    #最小卖出量（币）
    ht_up = 0.015    #趋势线上轨变量，上轨算法：ht*(1+ht_up)
    ht_down = 0.015    #趋势线下轨变量，下轨算法：ht*(1-ht_down)
    pending_main = False    #全局挂起参数，为True时只接收K线数据，不进行任何交易
    pending_T = True    #交易时段变为False，其余时间均为True
    pending_AT = False    #一次交易完成后变为True，防止重复交易
    HT_Line_Mid = None    #HT中线
    #初始数据设置结束

    Log('策略已启动！')


    if initial_balance is None:    #计算账户初始净值
        i_b = _C(exchange.GetAccount)
        i_t = _C(exchange.GetTicker)
        i_price = i_t['Last']
        initial_balance = i_b['Balance'] + i_b['FrozenBalance'] + i_b['Stocks']*i_price + i_b['FrozenStocks']*i_price
        initial_standard_stocks = initial_balance/i_price    #账户初始净值所能购买的stocks数量，用于计算基准净值
        Log('初始账户净值:', initial_balance)
    while True:
        account_info = _C(exchange.GetAccount)    #获取账户信息
        now_ticker = _C(exchange.GetTicker)    #获取市场深度
        now_price = now_ticker['Last']    #当前价格
        now_balance = account_info['Balance'] + account_info['FrozenBalance'] + account_info['Stocks']*now_price + account_info['FrozenStocks']*now_price    #计算当前净值
        now_balance = _N(now_balance, 2)    #保留两位小数
        now_standard = initial_standard_stocks*now_price    #当前基准净值
        now_standard = _N(now_standard, 2)    #保留两位小数
        #记录账户最大净值
        if max_balance is None:
            max_balance = now_balance
        else:
            if max_balance < now_balance:
                max_balance = now_balance
        #计算当前回撤
        current_dd = (1 - now_balance/max_balance) * 100
        current_dd = _N(current_dd, 3)
#        Log('当前回撤为:', current_dd, '%，', '回撤止损线为:', stop_loss_line, '%')
        #计算当前一次操作盈利
        if open_balance is not None:
            current_win = (now_balance-open_balance)/open_balance *100
            current_win = _N(current_win, 2)
            if current_win > 7:
                ht_down = 0.005
        #初始化交易信号
        stop_loss_sign = False    #止损信号
        long_trade_sign = False     #开仓信号
        short_trade_sign = False    #止损信号
        #若回撤大于设置值，开启止损信号
        if current_dd > stop_loss_line:
            Log('回撤大于设置的回撤止损线，触发止损信号！')
            stop_loss_sign = True

        #计算指标
        R_Hist = _G("Hist")    #读取先前保存的K线数据
        Hist = _C(exchange.GetRecords,PERIOD_H1)    #获得历史K线数据
        L_Hist = Hist[:-1]
        N_Hist = []
        if R_Hist is None:
            N_Hist = L_Hist
        else:
            N_Hist = R_Hist[:]
            for i in L_Hist:
                if i in N_Hist:
                    continue
                else:
                    N_Hist.append(i)
        #N_Hist为除当前bar以外的历史bar数据
        _G("Hist", N_Hist)    #保存获取的历史K线数据

        HistLen = len(N_Hist)    #获得的历史bar数量
#        Log('BarLength:', HistLen)
        if HistLen > 99:
            HT_Hist = N_Hist[-101:]
            HT_Hist_Close = []
            for i in HT_Hist:
                i_Close = i['Close']
                HT_Hist_Close.append(i_Close)
            Array_HT_Hist_Close = np.array(HT_Hist_Close)
            HT_Line = tl.HT_TRENDLINE(Array_HT_Hist_Close)
            HT_Line_Up = _N(HT_Line[-1] * (1+ht_up), 3)
            HT_Line_Down = _N(HT_Line[-1] * (1-ht_down), 3)
            HT_Line_Mid = _N(HT_Line[-1], 3)

            #计算能否产生买入卖出信号
            if now_price > HT_Line_Up:
                long_trade_sign = True
            elif now_price < HT_Line_Down:
                short_trade_sign = True

        #计算时间
        now_time = datetime.datetime.now()
        now_hour = now_time.hour

        #交易模块
        if pending_main is True:
            Log('交易被挂起，不进行任何交易操作！')
        else:
            if stop_loss_sign:
                ext.Sell(account_info['Stocks'])
                max_balance = None
                Log('产生止损信号，进行了全仓卖出，当前价格为：', now_price)
                open_balance = None
                ht_down = 0.015
            if now_hour in Tradetime:
                pending_T = False
            else:
                pending_T = True
                pending_AT = False
            #双开关设计保证只在交易时段进行交易，且不重复进行交易
            if pending_T is False and pending_AT is False:
                if long_trade_sign:
                    if account_info['Balance'] > mini_buy_money:
                        ext.Buy(account_info['Balance']/now_price)
                        Log('产生开仓信号，进行了一笔买入交易，当前价格为：', now_price)
                        #再次计算当前净值
                        open_balance = account_info['Balance'] + account_info['FrozenBalance'] + account_info['Stocks']*now_price + account_info['FrozenStocks']*now_price
                        pending_AT = True
                    else:
                        Log('没有交易信号，等待下个交易时段，当前价格为:', now_price)
                        pending_AT = True
                elif short_trade_sign:
                    if account_info['Stocks'] > mini_sell_stocks:
                        ext.Sell(account_info['Stocks'])
                        max_balance = None
                        Log('产生平仓信号，进行了一笔卖出交易，当前价格为：', now_price)
                        open_balance = None
                        ht_down = 0.015
                        pending_AT = True
                    else:
                        Log('没有交易信号，等待下个交易时段，当前价格为:', now_price)
                        pending_AT = True
                else:
                    Log('没有交易信号，等待下个交易时段。')
                    pending_AT = True

                #输出盈利情况
                now_profit = now_balance - initial_balance
                now_profit = _N(now_profit, 2)
                LogProfit(now_profit)

                #绘图
                global chart
                obj_chart = Chart(chart)
                obj_chart.add(0, [Hist[-1]['Time'], now_standard])
                obj_chart.add(1, [Hist[-1]['Time'], now_balance])

        #更新状态栏信息
        if HT_Line_Mid is not None:
            LogStatus('价格上轨为:', HT_Line_Up, '中轨为:', HT_Line_Mid, '下轨为:', HT_Line_Down, '当前价格为:', now_price, '\n账户信息：', account_info, '\nBarLength:', HistLen)
        else:
            LogStatus('账户信息：', account_info, '\nBarLength:', HistLen)


        Sleep(30*1000)
