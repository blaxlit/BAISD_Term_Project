import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
from autogluon.tabular import TabularPredictor

# โหลดโมเดล
try:
    predictor = TabularPredictor.load('ag_fishery_model')
except:
    predictor = None
    print("ไม่พบโมเดล! กรุณารัน train_model.py ก่อน")

app = dash.Dash(__name__)

# รายชื่อข้อมูลสำหรับ Dropdown
TOP_COUNTRIES = ['ญี่ปุ่น', 'จีน', 'สหรัฐอเมริกา', 'ฮ่องกง', 'มาเลเซีย', 'เกาหลีใต้', 'เวียดนาม', 'อินโดนีเซีย', 'ไต้หวัน', 'เมียนมา']
TOP_PRODUCTS = [
    'ปลาทูน่า สคิปแจกและแอตแลนติกโบนิโตอื่นๆ ที่บรรจุภาชนะที่อากาศผ่านเข้าออกไม่ได้',
    'ของผสมที่ใช้ปรุงรส และของผสมที่ใช้ชูรสอื่น ๆ',
    'อาหารสุนัขหรือแมวที่มีปลาบรรจุภาชนะที่อากาศเข้าออกไม่ได้',
    'ลูกปลาอื่น ๆ มีชีวิต',
    'น้ำปลา'
]

# --- UI Layout ---
app.layout = html.Div(style={'fontFamily': 'Tahoma, sans-serif', 'padding': '30px', 'backgroundColor': '#f4f6f9'}, children=[
    
    html.H1("🐟 แดชบอร์ดพยากรณ์มูลค่าการนำเข้า-ส่งออกสินค้าประมงไทย", style={'textAlign': 'center', 'color': '#2c3e50'}),
    
    # --- พารามิเตอร์รับค่า (3 คะแนน) ---
    html.Div(style={'backgroundColor': 'white', 'padding': '25px', 'borderRadius': '10px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)', 'marginBottom': '20px'}, children=[
        html.H3("⚙️ ปรับตัวแปรสถานการณ์การค้า:"),
        
        html.Div(style={'display': 'flex', 'gap': '20px'}, children=[
            html.Div(style={'flex': 1}, children=[
                html.Label("ประเภทการค้า:"),
                dcc.Dropdown(id='input-trade', options=[{'label': 'นำเข้า', 'value': 'นำเข้า'}, {'label': 'ส่งออก', 'value': 'ส่งออก'}], value='ส่งออก', clearable=False),
            ]),
            html.Div(style={'flex': 1}, children=[
                html.Label("ประเทศคู่ค้า:"),
                dcc.Dropdown(id='input-country', options=[{'label': c, 'value': c} for c in TOP_COUNTRIES], value='ญี่ปุ่น', clearable=False),
            ]),
            html.Div(style={'flex': 1}, children=[
                html.Label("เดือนที่ต้องการพยากรณ์:"),
                dcc.Slider(id='input-month', min=1, max=12, step=1, value=12, marks={i: str(i) for i in range(1,13)}),
            ]),
        ]),
        html.Br(),
        html.Label("ประเภทสินค้าประมง:"),
        dcc.Dropdown(id='input-product', options=[{'label': p, 'value': p} for p in TOP_PRODUCTS], value=TOP_PRODUCTS[0], clearable=False),
        
        html.Hr(),
        # --- โมดูลเพิ่มเติมออกแบบเอง: Trade Balance Simulator (5 คะแนน) ---
        html.H4("💡 โมดูลเสริม: เครื่องมือวิเคราะห์ผลกำไร/ขาดทุน (Profit Simulator)", style={'color': '#8e44ad'}),
        html.Label("กรอกต้นทุนเฉลี่ยของสินค้าล็อตนี้ (บาท): "),
        dcc.Input(id='input-cost', type='number', value=1000000, step=100000)
    ]),

    # ส่วนแสดงผลพยากรณ์เป็นตัวเลข
    html.Div(style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}, children=[
        html.Div(id='output-value', style={'flex': 1, 'fontSize': '20px', 'fontWeight': 'bold', 'color': '#2980b9', 'padding': '20px', 'backgroundColor': '#ebf5fb', 'borderRadius': '10px', 'textAlign': 'center'}),
        html.Div(id='output-profit', style={'flex': 1, 'fontSize': '20px', 'fontWeight': 'bold', 'padding': '20px', 'borderRadius': '10px', 'textAlign': 'center'})
    ]),
    
    # --- กราฟแสดงผล (5 คะแนน) ---
    html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'}, children=[
        dcc.Graph(id='prediction-graph')
    ])
])

# Callback ควบคุมการอัปเดต
@app.callback(
    [Output('output-value', 'children'),
     Output('output-profit', 'children'),
     Output('output-profit', 'style'),
     Output('prediction-graph', 'figure')],
    [Input('input-trade', 'value'),
     Input('input-country', 'value'),
     Input('input-month', 'value'),
     Input('input-product', 'value'),
     Input('input-cost', 'value')]
)
def update_dash(trade_type, country, month, product, cost):
    if predictor is None: return "Error", "Error", {}, px.bar()

    # 1. ป้อนข้อมูลให้ AutoGluon
    input_data = pd.DataFrame({'Year': [2568], 'Month': [month], 'Country': [country], 'Product': [product], 'TradeType': [trade_type]})
    
    try:
        predicted_value = predictor.predict(input_data).iloc[0]
        if predicted_value < 0: predicted_value = 0
    except:
        predicted_value = 0
        
    # 2. คำนวณกำไร/ขาดทุนจากโมดูลเสริม (รายได้ - ต้นทุน)
    est_cost = cost if cost else 0
    profit = predicted_value - est_cost
    
    # 3. จัดการสีป้ายกำไร/ขาดทุน
    if profit >= 0:
        profit_text = f"📈 คาดการณ์กำไรสุทธิ: +{profit:,.2f} บาท"
        profit_style = {'flex': 1, 'fontSize': '20px', 'fontWeight': 'bold', 'color': '#27ae60', 'padding': '20px', 'backgroundColor': '#e8f8f5', 'borderRadius': '10px', 'textAlign': 'center'}
    else:
        profit_text = f"📉 คาดการณ์ขาดทุน: {profit:,.2f} บาท"
        profit_style = {'flex': 1, 'fontSize': '20px', 'fontWeight': 'bold', 'color': '#c0392b', 'padding': '20px', 'backgroundColor': '#fdedec', 'borderRadius': '10px', 'textAlign': 'center'}

    value_text = f"💰 พยากรณ์มูลค่าการ{trade_type}: {predicted_value:,.2f} บาท"
    
    # 4. สร้างกราฟแท่ง
    fig = px.bar(
        x=[f"เดือนที่ {month} ({country})"], y=[predicted_value], 
        labels={'x': 'ช่วงเวลาพยากรณ์', 'y': 'มูลค่า (บาท)'},
        title=f"แนวโน้มมูลค่าการ{trade_type} สินค้า {product.split()[0][:20]}...",
        color_discrete_sequence=['#3498db']
    )
    
    return value_text, profit_text, profit_style, fig

if __name__ == '__main__':
    app.run(debug=True)