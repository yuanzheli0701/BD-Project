#!/usr/bin/env python3
import io, json, os, random, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jobs.common import get_raw_path, CITY_MAP
# -- Song pools --
SONGS = [
    ("Blinding Lights","The Weeknd"),("Shape of You","Ed Sheeran"),
    ("Stay","The Kid LAROI"),("As It Was","Harry Styles"),
    ("Flowers","Miley Cyrus"),("Cruel Summer","Taylor Swift"),
    ("Anti-Hero","Taylor Swift"),("Vampire","Olivia Rodrigo"),
    ("Bad Guy","Billie Eilish"),("Someone You Loved","Lewis Capaldi"),
    ("Levitating","Dua Lipa"),("Good 4 U","Olivia Rodrigo"),
    ("Heat Waves","Glass Animals"),("Drivers License","Olivia Rodrigo"),
    ("Easy On Me","Adele"),("Shivers","Ed Sheeran"),
    ("Cold Heart","Elton John"),("Unholy","Sam Smith"),
    ("Kill Bill","SZA"),("Die For You","The Weeknd"),
    ("Calm Down","Rema"),("Greedy","Tate McRae"),
    ("Water","Tyla"),("Houdini","Dua Lipa"),("Lovin On Me","Jack Harlow"),
    ("Escapism","RAYE"),("Golden Hour","JVKE"),("Players","Coi Leray"),
    ("What Was I Made For","Billie Eilish"),("About Damn Time","Lizzo"),
    ("Paint The Town Red","Doja Cat"),("Strangers","Kenya Grace"),
    ("Running Up That Hill","Kate Bush"),("I'm Good","David Guetta"),
    ("Kiss Me More","Doja Cat"),("Peaches","Justin Bieber"),
    ("Montero","Lil Nas X"),("Industry Baby","Lil Nas X"),
    ("First Class","Jack Harlow"),("Save Your Tears","The Weeknd"),
    ("Made You Look","Meghan Trainor"),("Rich Flex","Drake"),
    ("Super Freaky Girl","Nicki Minaj"),("TQG","Karol G"),
    ("People","Libianca"),("My Love Mine All Mine","Mitski"),
    ("Dance Monkey","Tones and I"),("Watermelon Sugar","Harry Styles"),
]

def gen_features(vibe='mixed'):
    d,e,v,a = random.uniform,random.uniform,random.uniform,random.uniform
    if vibe=='sad':
        return {'danceability':max(.1,d(.2,.45)),'energy':max(.05,d(.15,.4)),
            'key':random.randint(0,11),'loudness':random.gauss(-14,3),
            'mode':random.choices([0,1],weights=[.55,.45])[0],
            'speechiness':max(.02,d(.03,.08)),'acousticness':max(.1,d(.5,.85)),
            'instrumentalness':max(0,d(0,.25)),'liveness':max(.02,d(.05,.2)),
            'valence':max(.02,d(.1,.35)),'tempo':max(40,random.gauss(72,18)),
            'duration_ms':random.randint(160000,300000),'time_signature':4}
    if vibe=='happy':
        return {'danceability':max(.3,d(.55,.85)),'energy':max(.3,d(.6,.9)),
            'key':random.randint(0,11),'loudness':random.gauss(-6,2.5),
            'mode':random.choices([0,1],weights=[.1,.9])[0],
            'speechiness':max(.02,d(.04,.12)),'acousticness':max(0,d(.05,.35)),
            'instrumentalness':max(0,d(0,.1)),'liveness':max(.02,d(.08,.25)),
            'valence':max(.4,d(.6,.9)),'tempo':max(100,random.gauss(122,15)),
            'duration_ms':random.randint(140000,260000),'time_signature':4}
    return {'danceability':max(.1,d(.4,.8)),'energy':max(.05,d(.3,.75)),
        'key':random.randint(0,11),'loudness':random.gauss(-8,3.5),
        'mode':random.choice([0,1]),'speechiness':max(.02,d(.03,.15)),
        'acousticness':max(0,d(.1,.6)),'instrumentalness':max(0,d(0,.2)),
        'liveness':max(.02,d(.05,.25)),'valence':max(.02,d(.2,.75)),
        'tempo':max(50,random.gauss(115,25)),
        'duration_ms':random.randint(120000,320000),'time_signature':4}

def gen_tracks(region, weather=None):
    n = random.sample(SONGS, min(50,len(SONGS)))
    random.shuffle(n)
    if weather and weather.get('is_rainy'):
        w = {'sad':.40,'happy':.15,'mixed':.45}
    elif weather:
        w = {'sad':.12,'happy':.40,'mixed':.48}
    else:
        w = {'sad':.25,'happy':.30,'mixed':.45}
    vibes = random.choices(list(w.keys()),weights=list(w.values()),k=len(n))
    tracks = []
    for i,(name,artist) in enumerate(n):
        f = gen_features(vibes[i])
        tracks.append({'track_id':f'mock_{region}_{i:04d}',
            'name':name,'artists':[artist],**f})
    return tracks

def gen_weather(city_name, info, date_str, weather_type='seasonal'):
    target = datetime.strptime(date_str,'%Y-%m-%d')
    lat, month = info['lat'], target.month
    if lat >= 0:
        shift = 15*(1-abs(month-7)/6); base = 10+shift
    else:
        shift = 15*(1-abs(month-1)/6); base = 10+shift
    records = []
    for off in range(-2,3):
        day = target+timedelta(days=off); ds = day.strftime('%Y-%m-%d')
        if weather_type=='rainy':
            rainy=True; rain=round(random.uniform(3,25),1)
            clouds=random.randint(75,100); hum=random.randint(75,98)
        elif weather_type=='sunny':
            rainy=False; rain=0.0; clouds=random.randint(0,15); hum=random.randint(30,55)
        elif weather_type=='seasonal':
            wet_months = [10,11,12,1,2,3] if lat>=0 else [4,5,6,7,8,9]
            if month in wet_months:
                rainy=random.random()<0.5
                rain=round(random.uniform(1,12),1) if rainy else 0.0
                clouds=random.randint(40,95) if rainy else random.randint(20,70)
                hum=random.randint(60,90)
            else:
                rainy=random.random()<0.15
                rain=round(random.uniform(0,3),1) if rainy else 0.0
                clouds=random.randint(5,40); hum=random.randint(35,65)
        else:
            rainy=random.random()<0.35
            rain=round(random.uniform(1,10),1) if rainy else 0.0
            clouds=random.randint(30,90) if rainy else random.randint(5,60)
            hum=random.randint(55,90) if rainy else random.randint(35,70)
        dt = base+random.uniform(-3,3)
        records.append({'date':ds,'temp_avg':round(dt,1),
            'temp_min':round(dt-random.uniform(1,5),1),
            'temp_max':round(dt+random.uniform(1,5),1),
            'humidity_avg':float(hum),'clouds_avg':float(clouds),
            'wind_speed_avg':round(random.uniform(1,15),1),
            'total_rain_3h':rain,'is_rainy':rainy})
    return records

def generate_mock_data(date_str=None, weather_scenario='seasonal'):
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    print(f'\nGenerating mock data for {date_str} (scenario: {weather_scenario})')
    print('='*55)

    # Weather data
    weather_data = []
    for city_name, info in CITY_MAP.items():
        daily = gen_weather(city_name, info, date_str, weather_scenario)
        weather_data.append({'city':city_name,'country':info['country'],
            'region':info['region'],'lat':info['lat'],'lon':info['lon'],
            'fetch_date':date_str,
            'fetched_at':datetime.now(timezone.utc).isoformat(),
            'forecast_daily':daily})

    # Spotify data
    spotify_dir = get_raw_path('spotify',date_str)
    spotify_dir.mkdir(parents=True, exist_ok=True)

    for city_name, info in CITY_MAP.items():
        region = info['region']
        city_w = None
        for w in weather_data:
            if w['city']==city_name:
                for d in w['forecast_daily']:
                    if d['date']==date_str: city_w=d; break
                break
        rain_tag = '[RAIN]' if (city_w and city_w.get('is_rainy')) else '[SUN]'
        mood = 'sadder' if (city_w and city_w.get('is_rainy')) else 'happier'
        print(f'  [{region}] {city_name}: {rain_tag} -> {mood} music')
        tracks = gen_tracks(region, city_w)
        data = {'region':region,'fetch_date':date_str,
            'fetched_at':datetime.now(timezone.utc).isoformat(),
            'track_count':len(tracks),'tracks':tracks}
        out = spotify_dir/f'{region}.json'
        with open(out,'w',encoding='utf-8') as f:
            json.dump(data,f,ensure_ascii=False,indent=2)

    # Save weather
    weather_dir = get_raw_path('weather',date_str)
    weather_dir.mkdir(parents=True,exist_ok=True)
    wf = weather_dir/'cities_weather.json'
    with open(wf,'w',encoding='utf-8') as f:
        json.dump(weather_data,f,ensure_ascii=False,indent=2)

    # Summary
    print(f'\nSpotify: {spotify_dir}')
    print(f'Weather: {wf}')
    print(f'\nSummary for {date_str}:')
    print(f'  {"City":<12} {"Temp":>5} {"Rain":>7} {"Clouds":>7}  Mood')
    print(f'  {"-"*45}')
    for w in weather_data:
        for d in w['forecast_daily']:
            if d['date']==date_str:
                t = '[RAIN]' if d['is_rainy'] else '[SUN]'
                print(f'  {w["city"]:<12} {d["temp_avg"]:>4.1f}C {d["total_rain_3h"]:>5.1f}mm {d["clouds_avg"]:>6.0f}% {t}')
                break
    return date_str


if __name__=='__main__':
    import argparse
    p = argparse.ArgumentParser(description='Mock data generator')
    p.add_argument('date',nargs='?',default=datetime.now(timezone.utc).strftime('%Y-%m-%d'))
    p.add_argument('--days',type=int,default=1)
    p.add_argument('--weather',choices=['rainy','sunny','mixed','seasonal'],default='seasonal')
    a = p.parse_args()
    base = datetime.strptime(a.date,'%Y-%m-%d')
    for off in range(a.days-1,-1,-1):
        d = base-timedelta(days=off)
        generate_mock_data(d.strftime('%Y-%m-%d'),a.weather)
    print(f'\nDone! Generated {a.days} day(s).')
