from flask import Flask, request, render_template_string
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Payroll Dashboard</title>
</head>
<body>
    <h1>📊 Payroll Dashboard</h1>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="payroll_file" accept=".xlsx">
        <input type="submit" value="Upload & Analyze">
    </form>

    {% if summary_table %}
        <h2>Summary</h2>
        {{ summary_table|safe }}

        <h2>Charts</h2>
        <img src="data:image/png;base64,{{ chart_img }}" alt="Payroll Chart">
    {% endif %}
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def dashboard():
    summary_table = None
    chart_img = None

    if request.method == 'POST':
        file = request.files['payroll_file']
        if file:
            df = pd.read_excel(file)

            # Create summary
            summary = df.groupby('Department')['Net Pay'].sum().reset_index()
            summary_table = summary.to_html(index=False)

            # Create chart
            fig, ax = plt.subplots()
            ax.bar(summary['Department'], summary['Net Pay'])
            ax.set_title('Net Pay by Department')
            ax.set_ylabel('Total Net Pay')
            plt.xticks(rotation=45)

            # Save chart as base64
            img = io.BytesIO()
            plt.tight_layout()
            plt.savefig(img, format='png')
            img.seek(0)
            chart_img = base64.b64encode(img.read()).decode('utf-8')
            plt.close()

    return render_template_string(TEMPLATE, summary_table=summary_table, chart_img=chart_img)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
