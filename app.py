import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from autogluon.tabular import TabularPredictor

# 1. โหลดโมเดล AI
try:
    predictor = TabularPredictor.load('ag_fishery_model')
except:
    predictor = None
    print("ไม่พบโมเดล! กรุณารัน train_model.py ก่อน")

# 2. โหลดข้อมูลจริง (Actual Data) มาเพื่อสร้างกราฟเปรียบเทียบ
try:
    df_actual = pd.read_csv('import_export.csv', encoding='utf-8')
    df_actual['tradeflow'] = df_actual['tradeflow'].map({1: 'นำเข้า', 2: 'ส่งออก'})
    df_actual = df_actual.rename(columns={
        'year': 'Year',
        'month': 'Month',
        'countryNameTH': 'Country',
        'productDetailTH': 'Product',
        'tradeflow': 'TradeType',
        'price': 'Target_Value_THB'
    })
except Exception as e:
    df_actual = pd.DataFrame()
    print("หาไฟล์ข้อมูลจริงไม่พบ")

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
    
    # --- พารามิเตอร์รับค่า ---
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
        # --- โมดูลเพิ่มเติม: เพิ่มช่องกรอกค่าระวางเรือ ---
        html.H4("💡 โมดูลเสริม: เครื่องมือวิเคราะห์ผลกำไร (รวมค่าโลจิสติกส์)", style={'color': '#8e44ad'}),
        
        html.Div(style={'display': 'flex', 'gap': '20px'}, children=[
            html.Div(style={'flex': 1}, children=[
                html.Label("ต้นทุนสินค้าล็อตนี้ (บาท): "),
                dcc.Input(id='input-cost', type='number', value=1000000, step=50000, style={'width': '100%', 'padding': '8px'})
            ]),
            html.Div(style={'flex': 1}, children=[
                html.Label("🚢 ค่าระวางเรือ / ค่าขนส่ง (บาท): "),
                dcc.Input(id='input-freight', type='number', value=50000, step=5000, style={'width': '100%', 'padding': '8px'})
            ]),
        ])
    ]),

    # ส่วนแสดงผลพยากรณ์
    html.Div(style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}, children=[
        html.Div(id='output-value', style={'flex': 1, 'fontSize': '18px', 'fontWeight': 'bold', 'color': '#2980b9', 'padding': '20px', 'backgroundColor': '#ebf5fb', 'borderRadius': '10px', 'textAlign': 'center'}),
        html.Div(id='output-profit', style={'flex': 1, 'fontSize': '18px', 'fontWeight': 'bold', 'padding': '20px', 'borderRadius': '10px', 'textAlign': 'center'})
    ]),
    
    # --- กราฟแสดงผล ---
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
     Input('input-cost', 'value'),
     Input('input-freight', 'value')] # รับค่าระวางเรือเพิ่ม
)
def update_dash(trade_type, country, month, product, cost, freight):
    # 1. ให้โมเดล AI พยากรณ์ล่วงหน้า 12 เดือน
    months_list = list(range(1, 13))
    input_data_all = pd.DataFrame({
        'Year': [2568] * 12, 
        'Month': months_list, 
        'Country': [country] * 12, 
        'Product': [product] * 12, 
        'TradeType': [trade_type] * 12
    })
    
    if predictor is not None:
        try:
            predictions_all = predictor.predict(input_data_all).tolist()
            predictions_all = [max(0, p) for p in predictions_all]
        except:
            predictions_all = [0] * 12
    else:
        predictions_all = [0] * 12
        
    predicted_value = predictions_all[month - 1]
        
    # 2. ดึง "ข้อมูลจริง (Actual Data)" จากไฟล์ CSV มาเปรียบเทียบ
    actual_values = [None] * 12
    if not df_actual.empty:
        filtered_df = df_actual[
            (df_actual['TradeType'] == trade_type) & 
            (df_actual['Country'] == country) & 
            (df_actual['Product'] == product)
        ]
        # หาค่าในแต่ละเดือนมาใส่กราฟ
        for m in months_list:
            val = filtered_df[filtered_df['Month'] == m]['Target_Value_THB']
            if not val.empty:
                actual_values[m-1] = val.values[0]
                
    actual_value_month = actual_values[month - 1] if actual_values[month - 1] is not None else 0

    # 3. คำนวณกำไร/ขาดทุน (รายได้ - (ต้นทุนสินค้า + ค่าระวางเรือ))
    est_cost = cost if cost else 0
    est_freight = freight if freight else 0
    total_cost = est_cost + est_freight
    
    profit = predicted_value - total_cost
    
    # 4. จัดการป้ายผลลัพธ์
    if profit >= 0:
        profit_text = f"📈 คาดการณ์กำไรสุทธิ: +{profit:,.2f} บาท\n(หักต้นทุนและค่าระวางเรือแล้ว)"
        profit_style = {'flex': 1, 'fontSize': '18px', 'fontWeight': 'bold', 'color': '#27ae60', 'padding': '20px', 'backgroundColor': '#e8f8f5', 'borderRadius': '10px', 'textAlign': 'center', 'whiteSpace': 'pre-line'}
    else:
        profit_text = f"📉 คาดการณ์ขาดทุน: {profit:,.2f} บาท\n(ต้นทุนรวมโลจิสติกส์: {total_cost:,.2f} บาท)"
        profit_style = {'flex': 1, 'fontSize': '18px', 'fontWeight': 'bold', 'color': '#c0392b', 'padding': '20px', 'backgroundColor': '#fdedec', 'borderRadius': '10px', 'textAlign': 'center', 'whiteSpace': 'pre-line'}

    actual_str = f" (ค่าจริง: {actual_value_month:,.2f})" if actual_value_month else ""
    value_text = f"💰 พยากรณ์มูลค่าเดือน {month}: {predicted_value:,.2f} บาท{actual_str}"
    
    # 5. สร้างกราฟเส้นเปรียบเทียบ (Actual vs Predicted)
    fig = go.Figure()
    
    # เส้นที่ 1: ค่าที่พยากรณ์ (เส้นประสีฟ้า)
    fig.add_trace(go.Scatter(
        x=[f"เดือน {m}" for m in months_list], 
        y=predictions_all, 
        mode='lines+markers',
        name='มูลค่าที่พยากรณ์ได้ (AI Predicted)',
        line=dict(color='#2980b9', width=3, dash='dash'),
        marker=dict(size=8)
    ))
    
    # เส้นที่ 2: ค่าจริง (เส้นทึบสีเขียว)
    fig.add_trace(go.Scatter(
        x=[f"เดือน {m}" for m in months_list], 
        y=actual_values, 
        mode='lines+markers',
        name='มูลค่าที่เกิดขึ้นจริง (Actual)',
        line=dict(color='#27ae60', width=3),
        marker=dict(size=8)
    ))
    
    # ไฮไลต์จุดในเดือนที่เลือก (รูปดาวสีแดง)
    fig.add_trace(go.Scatter(
        x=[f"เดือน {month}"], 
        y=[predicted_value], 
        mode='markers',
        name='เดือนเป้าหมาย',
        marker=dict(color='#e74c3c', size=16, symbol='star')
    ))

    # ตกแต่งกราฟ
    fig.update_layout(
        title=f"📈 เปรียบเทียบเทรนด์มูลค่าจริง vs พยากรณ์: สินค้า {product[:30]}...",
        xaxis_title="เดือน",
        yaxis_title="มูลค่า (บาท)",
        hovermode="x unified",
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01) # ย้ายกล่อง legend ไปซ้ายบน
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
    
    return value_text, profit_text, profit_style, fig

if __name__ == '__main__':
    app.run(debug=True)