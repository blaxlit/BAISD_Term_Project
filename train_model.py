import pandas as pd
from autogluon.tabular import TabularPredictor
import numpy as np # Added for safety if needed later

def prepare_and_train():
    df = pd.read_csv('import_export.csv', encoding='utf-8')
    df = df.dropna(subset=['countryNameTH'])
    
    df['tradeflow'] = df['tradeflow'].map({1: 'นำเข้า', 2: 'ส่งออก'})
    df = df.rename(columns={
        'year': 'Year',
        'month': 'Month',
        'countryNameTH': 'Country',
        'productDetailTH': 'Product',
        'tradeflow': 'TradeType',
        'price': 'Target_Value_THB'
    })
    
    # --- FIX APPLIED HERE ---
    # 1. Drop rows where Target_Value_THB or quantity are missing
    df = df.dropna(subset=['Target_Value_THB', 'quantity'])
    # 2. Keep only rows where quantity is greater than 0 to prevent Infinity
    df = df[df['quantity'] > 0]
    
    df['Unit_Price'] = df['Target_Value_THB'] / df['quantity']
    
    df = df.drop(columns=['heading11', 'countryID', 'productDetailEN', 'ETL_DATE', 'Target_Value_THB', 'weight', 'quantity'])
    
    top_products = df['Product'].value_counts().head(10).index
    top_countries = df['Country'].value_counts().head(10).index
    df = df[df['Product'].isin(top_products) & df['Country'].isin(top_countries)]

    predictor = TabularPredictor(label='Unit_Price', path='ag_fishery_model').fit(df, time_limit=120)

if __name__ == '__main__':
    prepare_and_train()