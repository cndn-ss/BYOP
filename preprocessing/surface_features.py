import pandas as pd
import json

df = pd.read_csv('data\\raw\\surface featuresGarhwal-Himalaya (2).csv')
print(df.head())

df['lon'] = df['.geo'].apply(lambda x: json.loads(x)['coordinates'][0])
df['lat'] = df['.geo'].apply(lambda x: json.loads(x)['coordinates'][1])

df = df.drop(columns=['.geo', 'system:index'])
df = df[['lat','lon','elevation','slope','aspect','curvature','NDVI','rainfall']]
print(df.isnull().sum())
df = df.dropna()

print('Final rows:',len(df))
print('NDVI range:',df['NDVI'].min().round(3), 'to', df['NDVI'].max().round(3))
print('Nulls remaining:', df.isnull().sum().sum())

df.to_csv('data/processed/surface_features_clean.csv', index=False)
