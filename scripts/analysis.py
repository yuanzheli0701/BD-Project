'''
Statistical Analysis: Pearson Correlation + Linear Regression
City Mood x Weather Project
'''
import pandas as pd, numpy as np
from scipy import stats
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jobs.common import get_combined_path

dates = [f'2026-05-{d:02d}' for d in range(1,32)] + [f'2026-06-{d:02d}' for d in range(1,9)]
dfs = []
for d in dates:
    p = get_combined_path(d) / 'combined.parquet'
    if p.exists():
        dfs.append(pd.read_parquet(p))

merged = pd.concat(dfs, ignore_index=True)

print('=' * 60)
print('PEARSON CORRELATION WITH CDI')
print('=' * 60)
for col in ['temp_avg','humidity_avg','clouds_avg','total_rain_3h','wind_speed_avg','avg_valence','avg_energy','avg_danceability']:
    r, p = stats.pearsonr(merged['depression_index'], merged[col])
    sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
    print(f'  {col:<20s}  r={r:+.3f}  p={p:.4f} {sig}')

print()
print('=' * 60)
print('RAINY vs SUNNY CDI')
print('=' * 60)
rainy = merged[merged['is_rainy'] == True]['depression_index']
sunny = merged[merged['is_rainy'] == False]['depression_index']
print(f'Rainy: n={len(rainy)} mean={rainy.mean():.3f} std={rainy.std():.3f}')
print(f'Sunny: n={len(sunny)} mean={sunny.mean():.3f} std={sunny.std():.3f}')
print(f'Ratio: {rainy.mean()/sunny.mean():.2f}x')
t, p = stats.ttest_ind(rainy, sunny)
print(f't-test p={p:.6f}')

print()
print('=' * 60)
print('LINEAR REGRESSION: Weather -> CDI')
print('=' * 60)
from sklearn.linear_model import LinearRegression
X = merged[['temp_avg','humidity_avg','clouds_avg','total_rain_3h','wind_speed_avg']].fillna(0)
y = merged['depression_index']
model = LinearRegression().fit(X, y)
print(f'R2={model.score(X,y):.3f}')
for name, coef in zip(X.columns, model.coef_):
    print(f'  {name:<20s}  coef={coef:+.4f}')
print(f'  intercept={model.intercept_:.3f}')
