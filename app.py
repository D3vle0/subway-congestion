from flask import Flask, render_template, request
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from pytz import timezone

import json, requests, os, time

load_dotenv(verbose=True)
app = Flask(__name__)

@app.route('/', methods=["GET"])
def init():
    return render_template("index.html")

@app.route('/', methods=["POST"])
def searchnum():
    searchDay=""
    with open('data/subway_num.json', 'r') as f:
        json_data = json.load(f)
    if request.form["station"][-1] != "역":
        searchStation = request.form["station"] + "역"
    else:
        searchStation = request.form["station"]
    if request.form["time"] == "0":
        now = datetime.now(timezone('Asia/Seoul'))
        searchTime = now.strftime('%H%M')
    else:
        searchTime = request.form["time"]
    if request.form["day"] == "0":
        now = datetime.now(timezone('Asia/Seoul'))
        tmp = now.weekday()
        if tmp == 0:
            searchDay = "MON"
        elif tmp == 1:
            searchDay = "TUE"
        elif tmp == 2:
            searchDay = "MON"
        elif tmp == 3:
            searchDay = "WED"
        elif tmp == 4:
            searchDay = "THU"
        elif tmp == 5:
            searchDay = "FRI"
        elif tmp == 6:
            searchDay = "SAT"
        elif tmp == 7:
            searchDay = "SUN"
    else:
        searchDay = request.form["day"]
    station_code = []
    startStation=[]
    endStation=[]
    congestion=[]
    metroLine=[]
    for i in json_data["contents"]:
        if searchStation == i["stationName"]:
            station_code.append(str(i["stationCode"]))
    for j in station_code:
        url = f"https://apis.openapi.sk.com/puzzle/congestion-car/stat/stations/{j}?dow={searchDay}&hh={searchTime[:2]}"

        headers = {
            "Accept": "application/json",
            "appkey": os.getenv('APPKEY')
        }

        response = requests.get(url, headers=headers)
        data=json.loads(response.text)
        for i in data["contents"]["stat"]:
            if i["data"][int(searchTime[2])]["congestionCar"][0]:
                startStation.append(i["startStationName"])
                endStation.append(i["endStationName"])
                congestion.append(i["data"][int(searchTime[2])]["congestionCar"])
                metroLine.append(data["contents"]["subwayLine"])
    return render_template("stat_result.html", startStation=startStation, endStation=endStation, congestion=congestion, searchStation=searchStation, searchTime=searchTime, searchDay=searchDay, metroLine=metroLine)

@app.route('/search', methods=["GET"])
def searchNum():
    if request.args.get('station'):
        station_code = []
        metroLine = []
        if request.args.get('station')[-1] != "역":
            searchStation = request.args.get('station') + "역"
        else:
            searchStation = request.args.get('station')
        with open('data/subway_num.json', 'r') as f:
            json_data = json.load(f)
        for i in json_data["contents"]:
            if searchStation == i["stationName"]:
                station_code.append(str(i["stationCode"]))
                metroLine.append(str(i["subwayLine"]))
        return render_template("search.html", station_code=station_code, metroLine=metroLine, searchStation=searchStation)
    return render_template("search.html")

@app.route('/realtime', methods=["GET"])
def realtime():
    if request.args.get('train'):
        url = f"https://apis.openapi.sk.com/puzzle/congestion-train/rltm/trains/2/{request.args.get('train')}"

        headers = {
            "Accept": "application/json",
            "appkey": os.getenv('APPKEY')
        }

        response = requests.get(url, headers=headers)
        res=json.loads(response.text)
        if res["success"] == True:
            data = {
                'line': '2',
                'isCb': 'N',
            }

            response = requests.post('https://smapp.seoulmetro.co.kr:58443/traininfo/traininfoUserMap.do', data=data)
            html = response.text.split('<div class="2line_metro">')[1].split('<div class="3line">')[0].strip()
            soup = BeautifulSoup(html, 'html.parser')
            title = soup.select('.tip')
            currentLocation = []
            for i in title:
                currentLocation.append(i.attrs['title'])
            for i in currentLocation:
                if request.args.get('train') in i:
                    location = i.split("열차")[1]
                    break
            return render_template("realtime_result.html", congestion=list(map(int, res["data"]["congestionResult"]["congestionCar"].split("|"))), num=request.args.get('train'), location=location, err=0)
        else:
            return render_template("realtime_result.html", num=request.args.get('train'), err=1)
    data = {
        'line': '2',
        'isCb': 'N',
    }

    response = requests.post('https://smapp.seoulmetro.co.kr:58443/traininfo/traininfoUserMap.do', data=data)
    html = response.text.split('<div class="2line_metro">')[1].split('<div class="3line">')[0].strip()
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.select('.tip')
    currentLocation = []
    for i in title:
        currentLocation.append(i.attrs['title'].replace("열차", " -"))
    currentLocation.sort()

    return render_template("realtime.html", currentLocation=currentLocation)

app.run(host="0.0.0.0",port=os.environ.get('PORT', 5001), debug=1)