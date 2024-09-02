from flask import Flask, request, send_file, jsonify, render_template
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
import os
import tempfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import io
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

def generate_charts(cdf, forecast_values):
    # Generate historical data chart
    plt.figure(figsize=(10, 6))
    plt.plot(cdf.index, cdf['Delinquency(%)'], marker='o')
    plt.title('Delinquency Rate Over 3 Years')
    plt.xlabel('Date')
    plt.ylabel('Delinquency Rate (%)')
    plt.grid(True)
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    historical_chart = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()

    # Generate forecast chart
    plt.figure(figsize=(12, 6))
    plt.plot(cdf['Delinquency(%)'], label='Historical Data', color='blue', marker='o')
    forecast_index = pd.date_range(start=cdf.index[-1] + pd.DateOffset(months=1), periods=6, freq='MS')
    plt.plot(forecast_index, forecast_values, label='Forecasted Data', color='red', marker='o')
    plt.title('Historical and Forecasted Data')
    plt.xlabel('Date')
    plt.ylabel('Delinquency Rate (%)')
    plt.legend()
    plt.grid(True)

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    forecast_chart = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()

    return historical_chart, forecast_chart

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        fd, temp_path = tempfile.mkstemp(suffix='.xlsx')
        logging.debug(f"Created temporary file: {temp_path}")

        try:
            with os.fdopen(fd, 'wb') as temp_file:
                file.save(temp_file)
            
            logging.debug("File saved successfully")

            df = pd.read_excel(temp_path)
            logging.debug("Excel file read successfully")

            df2022 = df.iloc[:, 0:100]
            df2023 = df.iloc[:, 100:200]
            df2024 = df.iloc[:, 200:300]
            df2023.columns = df2022.columns
            df2024.columns = df2022.columns

            for year_df in [df2022, df2023, df2024]:
                year_df['Delinquency(%)'] = (year_df.apply(lambda row: (row != 0).sum(), axis=1)) / year_df.shape[1] * 100
                year_df = year_df.round().astype(int)

            cdf = pd.concat([df2022, df2023, df2024], ignore_index=True) 
            date_range = pd.date_range(start='2022-01-01', periods=36, freq='MS')
            cdf.index = date_range

            model = SARIMAX(cdf['Delinquency(%)'], order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
            model_fit = model.fit(disp=False)
            forecast = model_fit.get_forecast(steps=6)
            forecast_values = forecast.predicted_mean


            historical_chart, forecast_chart = generate_charts(cdf, forecast_values)

            forecast_data = [{'date': date.strftime('%Y-%m-%d'), 'value': value} 
                            for date, value in zip(pd.date_range(start=cdf.index[-1] + pd.DateOffset(months=1), periods=6, freq='MS'),
                                                    forecast_values)]

            _, output_path = tempfile.mkstemp(suffix='.xlsx')
            pd.DataFrame(forecast_values).to_excel(output_path, index=False)
            logging.debug(f"Forecast saved to: {output_path}")

            return jsonify({
                'message': 'File processed successfully',
                'output_file': output_path,
                'historical_chart': historical_chart,
                'forecast_chart': forecast_chart,
                'forecast_data': forecast_data
            })

        finally:
            os.unlink(temp_path)
            logging.debug(f"Deleted temporary input file: {temp_path}")

    except Exception as e:
        logging.exception("An error occurred during file processing")
        return jsonify({'error': str(e)}), 500
    

if __name__ == '__main__':
    app.run(debug=True)

