from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import gee_data
app = FastAPI()

templates = Jinja2Templates(directory="frontend")
app.mount("/static", StaticFiles(directory="static"), name="static")



def get_location(station_name):
    if station_name == '부안':
        return {'lot': 126.83344314831722, 'lat': 35.69853080347812}
    elif station_name == "익산":
        return {'lot': 126.9094862178911, 'lat': 36.017287819982705}
    elif station_name == '남원':
        return {'lot': 127.52977233306779, 'lat': 35.43890642346706}

@app.get("/", response_class=HTMLResponse)
async def get_index():
    """HTML 페이지 반환"""
    with open("templates/index.html", encoding='UTF8') as f:
        return f.read()

@app.get("/load-data")
async def load_data(image_name: str, station_name: str, start_date: str = '2022-11-01', end_date: str = '2023-07-01'):
    """주어진 날짜 범위를 기반으로 데이터프레임 생성"""
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    datas = gee_data.get_data(image_name, station_name, start_date, end_date)
    value_df = datas[0]
    image_df = datas[1]

    response = {
        'value_data': value_df.to_dict(orient='records'),
        'image_data': image_df.to_dict(orient='records'),
        'location': get_location(station_name)
    }

    return JSONResponse(response)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8900)


