import pandas as pd
from autogluon.tabular import TabularPredictor

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
    
    df['Unit_Price'] = df['Target_Value_THB'] / df['quantity']
    df = df.drop(columns=['heading11', 'countryID', 'productDetailEN', 'ETL_DATE', 'Target_Value_THB', 'weight', 'quantity'])
    
    top_products = df['Product'].value_counts().head(10).index
    top_countries = df['Country'].value_counts().head(10).index
    df = df[df['Product'].isin(top_products) & df['Country'].isin(top_countries)]

    predictor = TabularPredictor(label='Unit_Price', path='ag_fishery_model').fit(df, time_limit=120)

if __name__ == '__main__':
    prepare_and_train()
