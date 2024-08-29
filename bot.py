import numpy as np
import pandas as pd
import ast 
import sqlite3


class TradingBot:
    def __init__(self,asset,email) -> None:
        self.asset = asset
        self.email = email

        self.commission = None
        self.TO_TRADE = None 
        self.min_transaction = None

        self.STARTING_BUDGET = None 
        
        self.prices = []
        self.holding = []

        self.actions = "" 
        self.to_trade = None  
        self.vol_held = 0
        self.budget = None 
        self.accumulator = None
        self.ACCUMULATOR = 1.15
    

    # assume there is a db called transactions and that holds 2 tables: register_new_trade | trades

    def find_commission_and_starting_budget(self,conn):
        q = "select starting_budget,vendors_commission,min_transaction from AssetFirstRegistration where email = %s and asset = %s"
        df = pd.read_sql_query(q,conn,params=(self.email,self.asset))
        self.STARTING_BUDGET = df['starting_budget'].iloc[0]
        self.commission = df['vendors_commission']
        self.min_transaction = df['min_transaction']

        order = round(self.STARTING_BUDGET / 2975,5)
        self.TO_TRADE = round(0.001 * order,5)

    
    def find_asset_prices(self):
        conn = sqlite3.connect('C:\\Users\\cs2291\\tradiing_bot\\crypto_trades.db')
        q = f"""select price from trades order by processing_timestamp desc limit 4500"""
        df = pd.read_sql_query(q,conn)
        self.prices = df['price'].to_list()
        conn.close()

    
    def find_previous_state(self,conn):
        q = "select budget, holding, vol_held, to_trade, accumulator from trades where email = %s and asset = %s order by action_timestamp desc"
        df = pd.read_sql_query(q,conn,params=(self.email,self.asset))
        if df.empty:
            self.vol_held = 0
            self.holding = []
            self.budget = self.STARTING_BUDGET
            self.to_trade = self.TO_TRADE
            self.accumulator = self.ACCUMULATOR
        else: 
            self.vol_held = df['vol_held'].iloc[0]
            self.holding = ast.literal_eval(df['holding'].iloc[0]) # convert str to list of tuples
            self.budget = df['budget'].iloc[0]
            self.to_trade = df['to_trade'].iloc[0]
            self.accumulator = df['accumulator'].iloc[0]
                            
        
    def check_slope(self,w=900) -> float:
        prices = self.prices[-w:]
        x = np.arange(len(prices))
        slope, _ = np.polyfit(x, prices, 1)
        return np.tanh(slope) # convert slope between [-1, 1]
    

    def calculate_profit(self,price:float) -> float:
        if not self.holding: return 0
        volume_to_sell = [x for x in self.holding if x[1] < price] # find prices lower than the current price
        vol = sum([x[0] for x in volume_to_sell])  # volume sum of the lower prices
        weighted_bought_price = sum([(x[0] / vol) * x[1] for x in volume_to_sell]) 
        sell_price =  (1 - self.commission) * price
        if (sell_price * 0.94) > weighted_bought_price: # adjust for commission
            return vol
        return 0


    def trade(self,price:float):
        init_vol_held = sum(x[0] for x in self.holding)

        self.prices.append(price)

        if not self.holding:
            self.to_trade = self.TO_TRADE
        
        # CHECK SELL  
        slope = self.check_slope()
        V = self.calculate_profit(price) # volume to sell 
        if V and slope < -0.45: # do not sell when there is an upward trend
            self.budget += V * (1-self.commission) * price # update budget after selling
            l = len(self.holding)
            self.holding = [x for x in self.holding if x[1] >= price] # update holding after selling
            for _ in range(l-len(self.holding)):
                self.accumulator /= self.accumulator
            self.accumulator = round(self.accumulator,6)
            self.actions  = "SELL"
            self.to_trade -= V # free up the volume that was sold
            self.to_trade = max(self.to_trade, self.TO_TRADE) 
            
        # CHECK FIRST BUY -> first time buying (or after everything is sold)
        elif not self.holding and (price * 1.029 < np.median(self.prices[-800:])) and (self.check_slope(w=350) > 0.7): # don't buy when downwards trend still
            self.accumulator = self.ACCUMULATOR
            self.to_trade = self.TO_TRADE # reset next trade to the original trade amount
            self.budget -= self.to_trade * price
            self.holding.append((self.to_trade * (1 - self.commission),price))
            self.actions = "FIRST_BUY"
            
        # BUY EXISTING
        elif self.holding and (self.holding[-1][-1] > (price * 1.023)) and (self.budget > self.to_trade * price) and (self.to_trade * price > self.min_transaction):                      
            self.holding.append((self.to_trade * (1 - self.commission),price))
            self.actions = "BUY"
            self.budget -= self.to_trade * price
            self.accumulator *= self.ACCUMULATOR
            self.to_trade += round(self.TO_TRADE * self.accumulator,6) # accumulate the trading amount for next trade                

        else:
            self.actions = "NO_ACTION"

        self.vol_held = sum(x[0] for x in self.holding)
        vol_to_trade = abs(init_vol_held - self.vol_held)

            
        return self.budget, self.actions, str(self.holding), self.vol_held, self.to_trade, self.accumulator, vol_to_trade

