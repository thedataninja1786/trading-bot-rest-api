from flask import Flask, request, jsonify, abort
from bot import TradingBot
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import pandas as pd
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import secrets

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'your-secure-secret-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 15 * 60  # 15 minutes
jwt = JWTManager(app)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": f"""  Welcome to Alpha TrAIdon's API! 
                            To get started, you can login and start trading using the following endpoints: 
                            POST /api/v1/login 
                            POST /api/v1/register-trade 
                            PUT /api/v1/update-trade 
                            DELETE /api/v1/delete-trade 
                            GET /api/v1/trade 
                            POST /api/v1/user-action \n

    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢷⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡎⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⣧⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡌
    ⢹⣿⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣿⡇
    ⢸⣿⣿⣧⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⣠⣿⣿⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿⠁
    ⠘⣿⣿⣿⣿⣶⣤⣄⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣆⠀⠀⠀⠀⠀⠀⣰⣿⣿⣿⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣤⣴⣿⣿⣿⣿⠀
    ⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣦⣤⣀⣀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⢀⣀⣤⣤⣶⣾⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀
    ⠀⢻⣿⣿⣿⣿⣿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⡆⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡏⠀⠀⢠⣶⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠇⠀
    ⠀⢸⣿⣿⣿⣿⣿⡀⠀⠈⠉⠛⠛⠿⢿⣿⣿⣿⣿⡇⠀⠀⢿⣿⣿⣿⡄⠀⠀⠀⠀⢸⣿⣿⣿⠇⠀⠀⣼⣿⣿⣿⣿⣿⡿⠿⠟⠛⠋⠉⢁⣿⣿⣿⣿⣿⠀⠀
    ⠀⠸⣿⣿⣿⣿⣿⣿⣷⣶⣤⣄⣀⡀⠀⠀⠉⠉⠛⠳⠀⠀⢸⣿⣿⣿⣷⠀⠀⠀⢀⣿⣿⣿⣿⠀⠀⠀⠿⠛⠛⠉⠁⠀⠀⠀⢀⣀⣠⣤⣾⣿⣿⣿⣿⡟⠀⠀
    ⠀⠀⣿⣿⣿⣿⣿⣿⠿⣿⣿⣿⣿⣿⣿⣶⣦⣤⣀⡀⠀⠀⠘⣿⣿⣿⣿⣇⠀⠀⣼⣿⣿⣿⡏⠀⠀⠀⠀⣀⣀⣤⣤⣶⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀
    ⠀⠀⢿⣿⣿⣿⣿⣿⡆⠀⠀⠉⠙⠛⠿⠿⣿⣿⣿⣿⡄⠀⠀⣿⣿⣿⣿⣿⡄⢰⣿⣿⣿⣿⠇⠀⠀⢸⣿⣿⣿⣿⣿⠿⠿⠛⠋⠉⠁⠀⣿⣿⣿⣿⣿⠃⠀⠀
    ⠀⠀⢸⣿⣿⣿⣿⣿⣿⣶⣶⣤⣄⣀⠀⠀⠀⠈⠉⠙⠃⠀⠀⢹⣿⣿⣿⣿⣷⣿⣿⣿⣿⣿⠀⠀⠀⠚⠛⠉⠉⠀⠀⠀⠀⣀⣀⣤⣤⣶⣿⣿⣿⣿⣿⠀⠀⠀
    ⠀⠀⠈⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⣦⣤⣀⡀⠀⠀⠈⠻⣿⣿⣿⣿⣿⣿⣿⡿⠋⠀⠀⠀⢀⣀⣠⣤⣴⣶⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡏⠀⠀⠀
    ⠀⠀⠀⠀⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣤⡀⠀⠈⠻⣿⣿⣿⡿⠋⠀⠀⢀⣴⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠋⠀⠀⠀⠀
    ⠀⠀⢀⠀⠀⠙⢿⣿⣿⣟⠻⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⡀⠀⠈⠻⠋⠀⠀⢀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠿⣿⣿⣿⡟⠁⠀⠀⠀⠀⠀
    ⠀⠀⠈⣧⡀⠀⠈⢻⣿⣿⣷⠀⠀⠉⠙⠛⠿⢿⣿⣿⣿⣿⣿⣿⣿⣦⡀⠀⠀⣠⣶⣿⣿⣿⣿⣿⣿⣿⣿⠿⠟⠛⠉⠉⠀   ⣠⣾⣿⣿⠋⠀⠀⣰⡇⠀⠀⠀
    ⠀⠀⠀⣿⣿⣄⠀⠀⠹⣿⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠉⠙⠛⠻⠿⣿⣿⣿⣦⣾⣿⣿⣿⡿⠿⠛⠋⠉⠁⠀⠀⠀⠀⠀   ⣠⣾⣿⣿⡿⠁⠀⢀⣼⣿⠇⠀⠀⠀
    ⠀⠀⠀⣿⣿⣿⣦⡀⠀⠈⢿⣿⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⣿⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀    ⣠⣾⣿⣿⣿⠏⠀⠀⣠⣾⣿⣿⠀⠀⠀⠀
    ⠀⠀⠀⢹⣿⣿⣿⣷⡄⠀⠀⠻⣿⣿⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⡀⠀⠀⠀⠀⠀⠀   ⣠⣾⣿⣿⣿⡿⠃⠀⠀⣴⣿⣿⣿⣿⠀⠀⠀⠀
    ⠀⠀⠀⢸⣿⣿⣿⣿⣿⣆⠀⠀⠙⢿⣿⣿⣿⣿⣦⠀⠀⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⠀⠀⠀  ⣠⣾⣿⣿⣿⣿⠟⠀⠀⢠⣾⣿⣿⣿⣿⡏⠀⠀⠀⠀
    ⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣧⡀⠀⠈⢻⣿⣿⣿⣿⣷⣄⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⢀⣴⣿⣿⣿⣿⡿⠃⠀⠀⣰⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀
    ⠀⠀⠀⠘⣿⣿⣿⣿⣿⣿⣿⣷⣄⠀⠀⠹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠁⠀⢀⣾⣿⣿⣿⣿⣿⣿⣿⠇⠀⠀⠀⠀
   ⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⠀⠀⠈⢿⣿⣿⣿⣿⣿⣿⣿⣿         ⣿⣿⣿⣿⣿⣿⣿⠋⠀⠀⣠⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡄⠀⠀⠻⣿⣿⣿⣿⣿⣿⣿⣿    ⣿⣿⣿⣿⣿⣿⣿⡟⠁⠀⢀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣆⠀⠀⠙⣿⣿⣿⣿⣿⣿⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⠋⠀⠀⣠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡏⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⡀⠀⠈⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠁⠀⢀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠈⠙⠻⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣄⠀⠀⠹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠏⠀⠀⢠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠟⠃⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⠿⢿⣿⣿⣿⣿⣿⣿⣿⣦⡀⠀⠘⢿⣿⣿⣿⣿⣿⣿⣿⡿⠃⠀⠀⣴⣿⣿⣿⣿⣿⣿⣿⣿⡿⠟⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠻⠿⣿⣿⣿⣿⣷⡄⠀⠀⠻⣿⣿⣿⣿⣿⠟⠀⠀⢀⣾⣿⣿⣿⣿⡿⠿⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⠻⢿⣿⣆⠀⠀⠙⣿⣿⡿⠃⠀⠀⣰⣿⡿⠿⠛⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠃⠀⠀⠈⠟⠁⠀⠀⠘⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
"""})

@app.route('/api/v1/user-action', methods=['POST'])
@jwt_required()
def acknowledge_action():

    if not request.is_json:
        abort(400, description="Request must be JSON")
    
    data = request.json
    
    required_fields = ["email", "asset", "decision", "price", "key"]
    if not all(field in request.json for field in required_fields):
        abort(400, description="Missing Required Fields")

    email = data.get('email')
    asset = data.get('asset')
    decision = data.get('decision')
    key = data.get('key')
    actual_price = data.get('price')

    if not isinstance(email, str) or not isinstance(asset, str) or not isinstance(decision, bool) or not isinstance(key, str) or not isinstance(actual_price, (int, float)):
        abort(400, description="Invalid data type for one or more fields")

    try:
        conn = mysql.connector.connect( host='127.0.0.1',port=1234,user='root',password="1234",database='crypto-prices')
        cursor = conn.cursor()
        q = "SELECT * FROM PendingActions WHERE email = %s AND asset = %s AND key = %s"
        df = pd.read_sql_query(q, conn, params=(email, asset, key))
    
        if df.empty:
            abort(404, description=f"No pending action found for the provided {key}")

        budget = df['budget'].iloc[0]
        holding = df['holding'].iloc[0]
        vol_held = df['vol_held'].iloc[0]
        to_trade = df['to_trade'].iloc[0]
        action = df['action'].iloc[0]
        accumulator = df['accumulator'].iloc[0]

        q = "INSERT INTO PendingActions (email, asset, budget, holding, vol_held, to_trade, action, decision, price, accumulator, key, action_timestamp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(q, (email, asset, budget, holding, vol_held, to_trade, action, decision, actual_price, accumulator, key, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return jsonify({"message": "Trade Confirmation Acknowledged"}), 200
    except Exception as e:
        abort(500, description="Internal Server Error")
    finally:
        cursor.close()
        conn.close()

@app.route('/api/v1/trade', methods=['GET'])
@jwt_required()
def trade():

    if not request.is_json:
        abort(400, description="Request must be JSON")
    
    email = request.args.get('email')
    asset = request.args.get('asset')
    
    if not asset or not email:
        abort(400, description="Missing Required Fields")
    
    # Check if the user has registered a trade for the asset
    try:
        conn = mysql.connector.connect( host='127.0.0.1',port=1234,user='root',password="1234",database='crypto-prices')
        # Check if the user has registered a trade for the asset
        q = """select * from AssetFirstRegistration where email = %s and asset =  %s """
        df = pd.read_sql_query(q,conn,params=(email,asset))
        if df.empty:
            abort(400, description="You need to register a trade first")
        
        # Check if there is a pending action for the user and asset
        q = "SELECT * FROM PendingActions WHERE email = %s AND asset = %s order by action_timestamp desc"
        df = pd.read_sql_query(q, conn, params=(email, asset))
    except Exception as e:
        abort(500, description="Internal Server Error")
    finally:
        conn.close()
                
    
    def has_duplicates(df, column_name):
        # the key needs to appear twice to avoid concurrency issues
        return df[column_name].duplicated().any()

    # pending action exists
    if not df.empty:
        # user has yet to respond to the pending action
        if df.shape[0] == 1 or not has_duplicates(df, 'key'):
                abort(403, description=f"Pending action for {asset} awaits")
        else:
            try:
                             
                duplicate_key = df[df['key'].duplicated()]['key'].iloc[0]
                df['action_timestamp'] = pd.to_datetime(df['action_timestamp'])
                df = df[df['key'] == duplicate_key]
                df = df.sort_values(by='action_timestamp', ascending=False)
                
                # choose the first pending action since the user response will always be the latest  
                decision = df['decision'].iloc[0]
                action = df['action'].iloc[0]
                actual_price = df['price'].iloc[0]
                asset = df['asset'].iloc[0]
                budget = df['budget'].iloc[0]
                holding = df['holding'].iloc[0]
                vol_held = df['vol_held'].iloc[0]
                to_trade = df['to_trade'].iloc[0]
                accumulator = df['accumulator'].iloc[0]
                key = df['key'].iloc[0]

                
                conn = mysql.connector.connect( host='127.0.0.1',port=1234,user='root',password="1234",database='crypto-prices')
                cursor = conn.cursor()
                q = "SELECT * FROM PendingActions WHERE email = %s AND asset = %s order by action_timestamp desc limit 1"
                df = pd.read_sql_query(q, conn, params=(email, asset))
                
                if decision and not df.empty:
                    # Delete the pending actions
                    q = "DELETE FROM PendingActions WHERE email = %s AND asset = %s"
                    cursor.execute(q, (email, asset))
    
                    # Decision to trade -> Insert into trades table
                    q = "INSERT INTO trades (email, asset, budget, holding, vol_held, to_trade, action, price, accumulator, action_timestamp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                    cursor.execute(q, (email, asset, budget, holding, vol_held, to_trade, action, actual_price, accumulator, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit() # commit insertion and deletion
                    return jsonify({"message": "Trade Action Registered Successfuly"}), 200
                else:
                    # Decision not to trade
                    q = "DELETE FROM PendingActions WHERE email = %s AND asset = %s"
                    cursor.execute(q, (email, asset))
                    conn.commit() # only commit deletion
                    return jsonify({"message": "Trade Action not Registered"}), 200
            except Exception as e:
                conn.rollback()  # roll back the entire transaction if anything fails
                abort(500, description="Internal Server Error 5")
            finally:
                cursor.close()
                conn.close()
            
    else:
        # no pending action
        try:
            # connect to the database to get the latest price
            conn = sqlite3.connect('C:\\Users\\cs2291\\tradiing_bot\\crypto_trades.db')
            cursor = conn.cursor()

            q = f"""select price from trades order by processing_timestamp desc limit 1"""
            df = pd.read_sql_query(q,conn)

            if df.empty:
                abort(400, description = "No price data available")
            price = df['price'].iloc[0]

        except Exception as e:
            abort(500, "Internal Server Error 6")
        finally:
            cursor.close()
            conn.close()
        
        # Create a new instance of the TradingBot class and start trading
        try:
            # data are read from the databases
            bot = TradingBot(asset=asset,email=email)
            bot.find_asset_prices()
            conn = mysql.connector.connect( host='127.0.0.1',port=1234,user='root',password="1234",database='crypto-prices')
            cursor = conn.cursor()
            bot.find_commission_and_starting_budget(conn=conn)
            bot.find_previous_state(conn=conn)
            conn.close()
        except Exception as e:
            print(e)
            abort(500, description="Internal Server Error 7")
        
        try:
            # trading bot calculations 
            budget, action, holding, vol_held, to_trade, accumulator,vol_to_trade = bot.trade(price)
            decision = True
            key = ""
        except Exception as e:
            # If an error occurs during trading, return a 503 Service Unavailable error
            abort(503, description="Service Unavailable")
        
        if action != "NO_ACTION":
            key = secrets.token_hex(64)
            try:
                conn = mysql.connector.connect( host='127.0.0.1',port=1234,user='root',password="1234",database='crypto-prices')
                cursor = conn.cursor()
                q = "INSERT INTO PendingActions (email, asset, budget, holding, vol_held, to_trade, action, decision, price, accumulator, key, action_timestamp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                cursor.execute(q, (email, asset, budget, action, str(holding), vol_held, to_trade, action, decision, price, accumulator, key, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
            except Exception as e:
                abort(500, description="Internal Server Error")
            finally:
                cursor.close()
                conn.close()    
        
        return jsonify({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "asset": asset,
            "price": price,
            "action": action,
            "volume": vol_to_trade,
            "key": key
        })



@app.route('/api/v1/login', methods=['POST'])
def login():

    if not request.is_json:
        abort(400, description="Request must be JSON")
    
    data = request.json
    required_fields = ["email", "password"]
    if not all(field in data for field in required_fields):
        abort(400, description="Missing Required Fields")
    
    email = data["email"]
    password =  data["password"]

    try:
        conn = mysql.connector.connect( host='127.0.0.1',port=1234,user='root',password="1234",database='crypto-prices')
        cursor = conn.cursor()
        
        q = "SELECT * FROM user WHERE email = %s"
        df = pd.read_sql_query(q, conn, params=(email,))

    except Exception as e:
        abort(500, description="Internal Server Error")
    finally:
        cursor.close()
        conn.close()
    
    if df.empty:
        abort(401, description="Invalid Credentials")
    else:
        db_email = df["email"].iloc[0]
        db_password = df["password_hash"].iloc[0]
        if email == db_email and check_password_hash(db_password,password):
            try:
                access_token = create_access_token(identity=email)
                return jsonify({"message": "Login Successful",
                                "access_token": access_token}), 200    
            except Exception as e:
                abort(500, description="Error generating access token")
        else:
            abort(401, description="Invalid Credentials")


@app.route('/api/v1/register-trade-config', methods=['POST'])
@jwt_required()
def register_trade_config():

    supported_assets = set(['BTC','ETH'])

    if not request.is_json:
        abort(400, description="Request must be JSON")
    
    data = request.json
    required_fields = ["asset", "starting_budget", "vendor_commission", "min_transaction"]
    if not all(field in data for field in required_fields):
        abort(400, description="Missing Required Fields")
  
    email = data["email"]
    asset = data["asset"]
    vendor_commission = data["vendor_commission"]
    starting_budget = data["starting_budget"]
    min_transaction = data["min_transaction"]

    if asset not in supported_assets:
        abort(400, description=f"Asset {asset} not currently supported")

    if not isinstance(email, str) or not isinstance(asset, str) or not isinstance(vendor_commission, (int, float)) or\
        not isinstance(starting_budget, (int, float)) or not isinstance(min_transaction, (int, float)):
        abort(400, description="Invalid data type for one or more fields")

    try:
        conn = mysql.connector.connect( host='127.0.0.1',port=1234,user='root',password="1234",database='crypto-prices')
        cursor = conn.cursor()
        q = "SELECT * FROM AssetFirstRegistration WHERE email = %s AND asset = %s"
        df = pd.read_sql_query(q, conn, params=(email, asset))
    except Exception as e:
        abort(500, description="Internal Server Error")
    
    if not df.empty:
        cursor.close()
        conn.close()
        abort(403, description="Trade already exists, delete to start a new one, or update as necessary")

    try:
        q = "INSERT INTO AssetFirstRegistration (email, asset, vendors_commission, min_transaction, starting_budget, first_registration_timestamp) VALUES (%s,%s,%s,%s,%s,%s)"
        cursor.execute(q, (email, asset, vendor_commission, min_transaction, starting_budget, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return jsonify({"message": "Trade Configuration Registered Successfully"}), 201
    except Exception as e:
        abort(500, description="Internal Server Error")
    finally:
        cursor.close()
        conn.close()


@app.route('/api/v1/update-trade-config', methods=['PUT'])
@jwt_required()
def update_trade_config():

    if not request.is_json:
        abort(400, description="Request must be JSON")
    
    data = request.json
    required_fields = ["asset", "starting_budget", "vendor_commission", "min_transaction"]
    if not all(field in data for field in required_fields):
        abort(400, description="Missing Required Fields")
    
    email = data["email"]
    asset = data["asset"]
    vendor_commission = data["vendor_commission"]
    starting_budget = data["starting_budget"]
    min_transaction = data["min_transaction"]
               
    
    if not isinstance(email, str) or not isinstance(asset, str) or not isinstance(vendor_commission, (int, float)) or\
        not isinstance(starting_budget, (int, float)) or not isinstance(min_transaction, (int, float)):
        abort(400, description="Invalid data type for one or more fields")
    
    try:
        conn = mysql.connector.connect( host='127.0.0.1',port=1234,user='root',password="1234",database='crypto-prices')
        cursor = conn.cursor()
        q = "SELECT * FROM AssetFirstRegistration WHERE email = %s AND asset = %s"
        df = pd.read_sql_query(q, conn, params=(email, asset))
    except Exception as e:
        abort(500, description="Internal Server Error")
        
    if df.empty:
        cursor.close()
        conn.close()
        abort(403, description="You need to register a trade first")

    try:
        q = "UPDATE AssetFirstRegistration SET vendors_commission = %s, min_transaction = %s, starting_budget = %s WHERE email = %s AND asset = %s"
        cursor.execute(q, (vendor_commission, min_transaction, starting_budget, email, asset))
        conn.commit()       
        return jsonify({"message": "Trade Updated Successfully"}), 200
    except Exception as e:
        abort(500, description="Internal Server Error")
    finally:
        cursor.close()
        conn.close()


@app.route('/api/v1/delete-trade-config', methods=['DELETE'])
@jwt_required()
def delete_trade_config():

    if not request.is_json:
        abort(400, description="Request must be JSON")
    
    data = request.json
    if "asset" not in data:
        abort(400, description="Missing Required Fields")
    email = data["email"]
    asset = data["asset"]

    try:
        conn = conn = mysql.connector.connect( host='127.0.0.1',port=1234,user='root',password="1234",database='crypto-prices')
        cursor = conn.cursor()
        q = "SELECT * FROM AssetFirstRegistration WHERE email = %s AND asset = %s"
        df = pd.read_sql_query(q, conn, params=(email, asset))
    except Exception as e:
        abort(500, description="Internal Server Error")
        
    if df.empty:
        cursor.close()
        conn.close()
        abort(403, description="Trade does not exist, register a trade first")

    try:
        q = "DELETE FROM AssetFirstRegistration WHERE email = %s AND asset = %s"
        cursor.execute(q, (email, asset))
        q = "DELETE FROM trades WHERE email = %s AND asset = %s"
        cursor.execute(q, (email, asset))
        conn.commit()
        
        return jsonify({"message": "Trade and Configs Deleted Successfully"}), 200

    except Exception as e:
        conn.rollback() # Roll back any changes if an error occurs
        abort(500, description="Internal Server Error")
    finally:
        cursor.close()
        conn.close()



if __name__ == '__main__':
    app.run(debug=True, port=5000)