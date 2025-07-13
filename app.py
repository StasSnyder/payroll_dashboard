from flask import Flask, request, render_template_string
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import matplotlib
matplotlib.use('Agg')  # ← prevents crash by disabling GUI backend

app = Flask(__name__)

TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Payroll Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1, h2 { color: #2c3e50; }
        table.dataframe { border-collapse: collapse; width: 60%; margin-top: 20px; }
        table.dataframe th, table.dataframe td {
            border: 1px solid #ccc; padding: 8px; text-align: center;
        }
        table.dataframe th { background-color: #f2f2f2; }
        ul { list-style-type: none; padding-left: 0; }
        .error { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Upload your payroll Excel file</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="payroll">
        <input type="submit" value="Upload">
    </form>

    {% if error %}
        <p class="error">Error: {{ error }}</p>
    {% endif %}

    {% if tables %}
        <h2>{{ pay_period }}</h2>
        {{ tables|safe }}

        <h2>Key Metrics</h2>
        <ul>
            <li><strong>Average Gross Pay:</strong> ${{ avg_gross_pay }}</li>
            <li><strong>Total Taxes Paid:</strong> ${{ total_taxes }}</li>
            <li><strong>Worker Count:</strong>
                <ul>
                {% for worker, count in worker_counts.items() %}
                    <li>{{ worker }}: {{ count }}</li>
                {% endfor %}
                </ul>
            </li>
        </ul>

        <h2>Net Pay by Worker Type</h2>
        <img src="data:image/png;base64,{{ chart }}" width="600">
    {% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    chart = None
    tables = None
    error = None
    pay_period = None
    avg_gross_pay = 0
    total_taxes = 0
    worker_counts = {}

    if request.method == 'POST':
        file = request.files['payroll']
        if file and file.filename.endswith('.xlsx'):
            df = pd.read_excel(file)
            required_cols = ['Employee Name', 'Worker Type', 'Gross Pay', 'Taxes', 'Pay Date']

            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                error = f"Missing column(s): {', '.join(missing)}"
            else:
                # Calculate Net Pay
                df['Net Pay'] = df['Gross Pay'] - df['Taxes']
                df['Pay Date'] = pd.to_datetime(df['Pay Date'])

                # Create summary
                summary = df.groupby('Worker Type')[['Gross Pay', 'Taxes', 'Net Pay']].sum()
                tables = summary.to_html(classes='data', header="true")

                # Metrics
                avg_gross_pay = round(df['Gross Pay'].mean(), 2)
                total_taxes = round(df['Taxes'].sum(), 2)
                worker_counts = df['Worker Type'].value_counts().to_dict()
                pay_start = df['Pay Date'].min().strftime('%b %d, %Y')
                pay_end = df['Pay Date'].max().strftime('%b %d, %Y')
                pay_period = f"Pay Period: {pay_start} – {pay_end}"

                # Create chart
                fig, ax = plt.subplots()
                summary['Net Pay'].plot(kind='bar', ax=ax, color='#2980b9')
                ax.set_title("Net Pay by Worker Type")
                ax.set_ylabel("Net Pay ($)")
                ax.set_xlabel("Worker Type")
                plt.xticks(rotation=45)
                plt.tight_layout()

                # Encode plot
                img = io.BytesIO()
                plt.savefig(img, format='png')
                img.seek(0)
                chart = base64.b64encode(img.read()).decode('utf-8')
                plt.close()
        else:
            error = "Please upload a valid .xlsx Excel file."

    return render_template_string(
        TEMPLATE,
        tables=tables,
        chart=chart,
        error=error,
        pay_period=pay_period,
        avg_gross_pay=avg_gross_pay,
        total_taxes=total_taxes,
        worker_counts=worker_counts
    )

if __name__ == '__main__':
    app.run(debug=True)
