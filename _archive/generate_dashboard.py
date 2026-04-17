"""
📊 Local FWA Data Visualization Dashboard
Interactive HTML dashboard for analyzing FWA data without AWS.

Generates a standalone HTML file with interactive charts using Chart.js.
Perfect for previewing data before QuickSight upload or offline analysis.
"""

import pandas as pd
import json
from datetime import datetime

def generate_interactive_dashboard(csv_file='insurance_fwa_data.csv'):
    """Generate interactive HTML dashboard from FWA data."""
    
    print("📊 Generating Interactive Dashboard...")
    
    # Load data
    try:
        df = pd.read_csv(csv_file)
        print(f"✅ Loaded {len(df):,} records from {csv_file}")
    except FileNotFoundError:
        print(f"❌ File not found: {csv_file}")
        print("Run: python engine/fwa_data_generator.py first")
        return
    
    # Prepare data for charts
    
    # 1. FWA Type Distribution
    fwa_dist = df['fwa_type'].value_counts().head(10)
    fwa_labels = fwa_dist.index.tolist()
    fwa_values = fwa_dist.values.tolist()
    
    # 2. Risk Category Distribution
    risk_dist = df['risk_category'].value_counts()
    risk_labels = risk_dist.index.tolist()
    risk_values = risk_dist.values.tolist()
    
    # 3. State-wise FWA Rate
    state_analysis = df.groupby('state').agg({
        'claim_id': 'count',
        'is_fwa': 'sum',
        'claim_amount': 'sum'
    })
    state_analysis['fwa_rate'] = (state_analysis['is_fwa'] / state_analysis['claim_id'] * 100).round(2)
    state_analysis = state_analysis.sort_values('fwa_rate', ascending=False).head(10)
    
    state_labels = state_analysis.index.tolist()
    state_fwa_rates = state_analysis['fwa_rate'].tolist()
    
    # 4. Monthly Trend
    monthly = df.groupby('year_month').agg({
        'claim_id': 'count',
        'is_fwa': 'sum'
    }).reset_index()
    monthly_labels = monthly['year_month'].tolist()
    monthly_total = monthly['claim_id'].tolist()
    monthly_fwa = monthly['is_fwa'].tolist()
    
    # 5. Top High-Risk Providers
    provider_risk = df.groupby(['provider_id', 'specialty']).agg({
        'fwa_risk_score': 'mean',
        'claim_id': 'count',
        'claim_amount': 'sum'
    }).sort_values('fwa_risk_score', ascending=False).head(20)
    
    provider_data = []
    for idx, row in provider_risk.iterrows():
        provider_data.append({
            'provider': idx[0],
            'specialty': idx[1],
            'risk': round(row['fwa_risk_score'], 3),
            'claims': int(row['claim_id']),
            'amount': f"${row['claim_amount']:,.2f}"
        })
    
    # 6. Specialty-wise Analysis
    specialty_analysis = df.groupby('specialty').agg({
        'claim_id': 'count',
        'is_fwa': 'sum',
        'claim_amount': 'sum'
    })
    specialty_analysis['fwa_pct'] = (specialty_analysis['is_fwa'] / specialty_analysis['claim_id'] * 100).round(1)
    specialty_analysis = specialty_analysis.sort_values('fwa_pct', ascending=False)
    
    specialty_labels = specialty_analysis.index.tolist()
    specialty_fwa_pct = specialty_analysis['fwa_pct'].tolist()
    
    # Calculate KPIs
    total_claims = len(df)
    total_amount = df['claim_amount'].sum()
    fwa_claims = df['is_fwa'].sum()
    fwa_amount = df[df['is_fwa'] == 1]['claim_amount'].sum()
    fwa_rate = (fwa_claims / total_claims * 100)
    high_risk_count = (df['fwa_risk_score'] > 0.8).sum()
    
    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FWA Detection Dashboard - Interactive Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            margin-bottom: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            color: #666;
            font-size: 1.1em;
        }}
        
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .kpi-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            text-align: center;
            transition: transform 0.3s;
        }}
        
        .kpi-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
        }}
        
        .kpi-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        .kpi-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        .chart-container {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }}
        
        .chart-container h2 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 1.3em;
        }}
        
        .table-container {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        
        th {{
            background: #667eea;
            color: white;
            font-weight: 600;
        }}
        
        tr:hover {{
            background: #f5f5f5;
        }}
        
        .risk-high {{
            color: #e74c3c;
            font-weight: bold;
        }}
        
        .risk-medium {{
            color: #f39c12;
        }}
        
        .footer {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            text-align: center;
            color: #666;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🚨 FWA Detection Dashboard</h1>
            <p>Interactive Analysis of {total_claims:,} Insurance Claims</p>
            <p style="font-size: 0.9em; color: #999; margin-top: 10px;">
                Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </div>
        
        <!-- KPI Cards -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Total Claims</div>
                <div class="kpi-value" style="color: #3498db;">{total_claims:,}</div>
                <div style="color: #666; font-size: 0.9em;">${total_amount:,.2f}</div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-label">FWA Detected</div>
                <div class="kpi-value" style="color: #e74c3c;">{fwa_claims:,}</div>
                <div style="color: #666; font-size: 0.9em;">${fwa_amount:,.2f}</div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-label">FWA Rate</div>
                <div class="kpi-value" style="color: #f39c12;">{fwa_rate:.2f}%</div>
                <div style="color: #666; font-size: 0.9em;">Of total claims</div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-label">High Risk</div>
                <div class="kpi-value" style="color: #9b59b6;">{high_risk_count:,}</div>
                <div style="color: #666; font-size: 0.9em;">Score > 0.8</div>
            </div>
        </div>
        
        <!-- Charts -->
        <div class="chart-grid">
            <!-- FWA Type Distribution -->
            <div class="chart-container">
                <h2>📊 FWA Type Distribution</h2>
                <canvas id="fwaTypeChart"></canvas>
            </div>
            
            <!-- Risk Category -->
            <div class="chart-container">
                <h2>⚠️ Risk Category Distribution</h2>
                <canvas id="riskCategoryChart"></canvas>
            </div>
            
            <!-- Monthly Trend -->
            <div class="chart-container">
                <h2>📈 Monthly Trend Analysis</h2>
                <canvas id="monthlyTrendChart"></canvas>
            </div>
            
            <!-- State Analysis -->
            <div class="chart-container">
                <h2>🗺️ State-wise FWA Rate</h2>
                <canvas id="stateChart"></canvas>
            </div>
            
            <!-- Specialty Analysis -->
            <div class="chart-container" style="grid-column: span 2;">
                <h2>🏥 Specialty-wise FWA Percentage</h2>
                <canvas id="specialtyChart"></canvas>
            </div>
        </div>
        
        <!-- Top Providers Table -->
        <div class="table-container">
            <h2 style="margin-bottom: 20px;">🔍 Top 20 High-Risk Providers</h2>
            <table>
                <thead>
                    <tr>
                        <th>Provider ID</th>
                        <th>Specialty</th>
                        <th>Avg Risk Score</th>
                        <th>Total Claims</th>
                        <th>Total Amount</th>
                    </tr>
                </thead>
                <tbody>
                    {generate_provider_rows(provider_data)}
                </tbody>
            </table>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p><strong>FWA Detection System</strong> | Data Source: insurance_fwa_data.csv</p>
            <p style="margin-top: 10px; font-size: 0.9em;">
                For AWS QuickSight upload, run: <code>python upload_to_quicksight.py</code>
            </p>
        </div>
    </div>
    
    <script>
        // Chart.js Configuration
        const chartColors = {{
            primary: '#667eea',
            danger: '#e74c3c',
            warning: '#f39c12',
            success: '#27ae60',
            info: '#3498db',
            purple: '#9b59b6'
        }};
        
        // FWA Type Chart
        new Chart(document.getElementById('fwaTypeChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(fwa_labels)},
                datasets: [{{
                    label: 'Number of Cases',
                    data: {json.dumps(fwa_values)},
                    backgroundColor: chartColors.danger,
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});
        
        // Risk Category Chart
        new Chart(document.getElementById('riskCategoryChart'), {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(risk_labels)},
                datasets: [{{
                    data: {json.dumps(risk_values)},
                    backgroundColor: [
                        chartColors.success,
                        chartColors.info,
                        chartColors.warning,
                        chartColors.danger
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});
        
        // Monthly Trend Chart
        new Chart(document.getElementById('monthlyTrendChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps(monthly_labels)},
                datasets: [
                    {{
                        label: 'Total Claims',
                        data: {json.dumps(monthly_total)},
                        borderColor: chartColors.info,
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        tension: 0.4,
                        fill: true
                    }},
                    {{
                        label: 'FWA Claims',
                        data: {json.dumps(monthly_fwa)},
                        borderColor: chartColors.danger,
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        tension: 0.4,
                        fill: true
                    }}
                ]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ position: 'top' }}
                }},
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});
        
        // State Chart
        new Chart(document.getElementById('stateChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(state_labels)},
                datasets: [{{
                    label: 'FWA Rate (%)',
                    data: {json.dumps(state_fwa_rates)},
                    backgroundColor: chartColors.warning,
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{ 
                        beginAtZero: true,
                        title: {{ display: true, text: 'FWA Rate (%)' }}
                    }}
                }}
            }}
        }});
        
        // Specialty Chart
        new Chart(document.getElementById('specialtyChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(specialty_labels)},
                datasets: [{{
                    label: 'FWA %',
                    data: {json.dumps(specialty_fwa_pct)},
                    backgroundColor: chartColors.purple,
                    borderRadius: 8
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    x: {{ 
                        beginAtZero: true,
                        title: {{ display: true, text: 'FWA Percentage' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""
    
    # Save HTML file
    output_file = 'fwa_dashboard.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Dashboard generated: {output_file}")
    print(f"🌐 Open in browser to view interactive charts")
    print(f"📊 Includes: KPIs, Charts, Tables, and Trend Analysis")
    
    return output_file

def generate_provider_rows(provider_data):
    """Generate HTML table rows for providers."""
    rows = []
    for p in provider_data:
        risk_class = 'risk-high' if p['risk'] > 0.7 else 'risk-medium' if p['risk'] > 0.5 else ''
        rows.append(f"""
                    <tr>
                        <td>{p['provider']}</td>
                        <td>{p['specialty']}</td>
                        <td class="{risk_class}">{p['risk']}</td>
                        <td>{p['claims']}</td>
                        <td>{p['amount']}</td>
                    </tr>""")
    return ''.join(rows)

if __name__ == "__main__":
    import sys
    csv_file = 'insurance_fwa_data.csv'
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    
    output = generate_interactive_dashboard(csv_file)
    
    if output:
        print("\n" + "="*60)
        print("🎉 SUCCESS! Dashboard ready to view")
        print("="*60)
        print(f"\n📂 File: {output}")
        print("\n💡 Next steps:")
        print("   1. Open fwa_dashboard.html in your browser")
        print("   2. Explore interactive charts and data")
        print("   3. Share with your team for review")
        print("   4. When ready, upload to QuickSight with:")
        print("      python upload_to_quicksight.py")
