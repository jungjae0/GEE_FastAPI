import ee
import pandas as pd
import datetime

ee.Authenticate()
ee.Initialize()

def get_polygon(region_name):

    dct = {}
    if region_name == '부안':
        roi1 = ee.Geometry.MultiPolygon(
        [[[
            [126.83344314831722, 35.69853080347812],
            [126.83401177662837, 35.69946743167022],
            [126.83303008812892, 35.69985079259434],
            [126.83244000214565, 35.69893595097654],
            [126.83344314831722, 35.69853080347812],
        ]]])
        roi2 = ee.Geometry.MultiPolygon(
        [[[
            [126.83386693734157, 35.699097138118546],
            [126.83349679249751, 35.698495951984235],
            [126.83441947239864, 35.69810822808759],
            [126.83480571049678, 35.69867892215711],
            [126.83386693734157, 35.699097138118546],
        ]]])
        dct = {'roi1': roi1, 'roi2': roi2}
    elif region_name == "익산":
        roi1 = ee.Geometry.MultiPolygon(
            [[[[126.90885474205147, 36.01743572955867],
               [126.90820028305184, 36.017001833802304],
               [126.90887083530556, 36.016337968671635],
               [126.90953065872323, 36.0167848850283]]]])

        roi2 = ee.Geometry.MultiPolygon(
            [[[[126.90804471492898, 36.0182384304104],
               [126.90737952709328, 36.01777416659031],
               [126.90811445236336, 36.017062579351986],
               [126.90881719112527, 36.01753118630448]]]])
        dct = {'roi1': roi1, 'roi2': roi2}
    elif region_name == '남원':
        roi1 = ee.Geometry.MultiPolygon(
            [[[[127.52903233306779, 35.43925642346706],
               [127.52839396732224, 35.43833204554555],
               [127.52882580297364, 35.43811570024398],
               [127.52948830860032, 35.4389570398177],
               [127.52903233306779, 35.43925642346706]]]])

        roi2 = ee.Geometry.MultiPolygon(
            [[[[127.52903233306779, 35.43925642346706],
               [127.52839396732224, 35.43833204554555],
               [127.52882580297364, 35.43811570024398],
               [127.52948830860032, 35.4389570398177],
               [127.52903233306779, 35.43925642346706]]]])

        dct = {'roi1': roi1, 'roi2': roi2}
    return dct



def apply_scale_factors(image, img_key):
    # 1. 위성영상에 따라 스케일링 팩터 적용
    if 'landsat' in img_key:
        optical_bands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
        thermal_bands = image.select('ST_B.*').multiply(0.00341802).add(149.0)
        return image.addBands(optical_bands, None, True).addBands(thermal_bands, None, True)
    elif 'sentinel' in img_key:
        return image.divide(10000)
def mask_clouds(image, img_key):
    # 1. 위성영상에 따라 클라우드 마스킹
    if 'sentinel' in img_key:
        qa = image.select('QA60')

        # 1.1. 구름과 권운 비트 마스크
        cloud_bit_mask = 1 << 10
        cirrus_bit_mask = 1 << 11

        # 1.2. 마스킹 조건 정의

        mask = (qa.bitwiseAnd(cloud_bit_mask).eq(0)
                .And(qa.bitwiseAnd(cirrus_bit_mask).eq(0)))

        return image.updateMask(mask)

    elif 'landsat' in img_key:
        qa = image.select('QA_PIXEL')

        # 1.1. 구름과 그림자 비트 마스크
        cloud_shadow_bit_mask = 1 << 3
        clouds_bit_mask = 1 << 5

        # 1.2. 마스킹 조건 정의
        mask = (qa.bitwiseAnd(cloud_shadow_bit_mask).eq(0)
                .And(qa.bitwiseAnd(clouds_bit_mask).eq(0)))

        return image.updateMask(mask)
def calculate_indices(image, image_name):
    band_dct = {}

    if image_name == 'landsat8':
        band_dct = {'NIR': 'B5', 'RED': 'B4', 'GREEN': 'B3', 'RED_EDGE': 'B6', 'BLUE': 'B2'}

    elif image_name == 'landsat9':
        band_dct = {'NIR': 'SR_B5', 'RED': 'SR_B4', 'GREEN': 'SR_B3', 'RED_EDGE': 'SR_B6', 'BLUE': 'SR_B2'}

    elif image_name == 'sentinel2':
        band_dct = {'NIR': 'B8', 'RED': 'B4', 'GREEN': 'B3', 'RED_EDGE': 'B5', 'BLUE': 'B2', 'SWIR': 'B11'}

    # 1. 식생지수 산출

    # 1.1. NDVI = (NIR - RED) / (NIR + RED)
    ndvi = image.normalizedDifference([band_dct['NIR'], band_dct['RED']]).rename('NDVI')

    # 1.2. NDRE = (NIR - RED_EDGE) / (NIR + RED_EDGE)
    ndre = image.normalizedDifference([band_dct['NIR'], band_dct['RED_EDGE']]).rename('NDRE')

    # 1.3. GNDVI = (NIR - GREEN) / (NIR + GREEN)
    gndvi = image.normalizedDifference([band_dct['NIR'], band_dct['GREEN']]).rename('GNDVI')

    # 1.4. RVI = NIR / RED
    rvi = image.select(band_dct['NIR']).divide(image.select(band_dct['RED'])).rename('RVI')

    # 1.5. CVI = (RED / GREEN^2) * NIR
    cvi = image.expression(
        '(RED / GREEN ** 2) * NIR', {
            'NIR': image.select(band_dct['NIR']),
            'GREEN': image.select(band_dct['GREEN']),
            'RED': image.select(band_dct['RED'])
        }).rename('CVI')


    return image.addBands([ndvi, cvi, ndre, gndvi, rvi])


def extract_indices_timeseries(image, target_area):
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=target_area,
        scale=10
    )
    date = image.date().format()
    return ee.Feature(None, {
        'date': date,
        'NDVI': stats.get('NDVI'),
        'NDRE': stats.get('NDRE'),
        'GNDVI': stats.get('GNDVI'),
        'CVI': stats.get('CVI'),
        'RVI': stats.get('RVI')
    })

def to_dataframe(feature_collection):
    features = feature_collection.getInfo()['features']
    rows = [
        {
            'date': feature['properties']['date'],
            'NDVI': feature['properties']['NDVI'],
            'NDRE': feature['properties']['NDRE'],
            'GNDVI': feature['properties']['GNDVI'],
            'CVI': feature['properties']['CVI'],
            'RVI': feature['properties']['RVI']
        }
        for feature in features
    ]
    df = pd.DataFrame(rows)
    # Convert to datetime, coercing errors to NaT
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['date'] = df['date'].dt.date
    df = df.drop_duplicates(subset='date')

    df['RVI'] = df['RVI'] / 10
    df['CVI'] = df['CVI'] / 10

    return df

def to_image(collection, area):
    vis_params = {
        'NDVI': {'min': -0.1, 'max': 1, 'palette': ['brown', 'yellow', 'green', 'blue']},
        'NDRE': {'min': 0, 'max': 1, 'palette': ['yellow', 'orange', 'red', 'green']},
        'GNDVI': {'min': -0.1, 'max': 1, 'palette': ['brown', 'yellow', 'green', 'blue']},
        'CVI': {'min': 0, 'max': 1, 'palette': ['blue', 'green', 'yellow', 'red']},
        'RVI': {'min': 0, 'max': 10, 'palette': ['brown', 'yellow', 'green', 'darkgreen']}
    }

    band_names = ['NDVI', 'NDRE', 'GNDVI', 'CVI', 'RVI']

    data = []

    for band in band_names:
        vi_values = collection.select(band).sort('system:time_start', False).first().clip(area)
        map_dict = vi_values.getMapId(vis_params[band])
        map_url = map_dict['tile_fetcher'].url_format
        data.append({'band_name': band, 'map_url': map_url})

    df = pd.DataFrame(data)

    return df


def get_data(image_name, region_name, start_date, end_date,):
    image_collection = ''
    if image_name == 'sentinel2':
        image_collection = 'COPERNICUS/S2_SR_HARMONIZED'
    elif image_name == 'landsat8':
        image_collection = 'LANDSAT/LC08/C02/T1'
    elif image_name == 'landsat9':
        image_collection = 'LANDSAT/LC09/C02/T1_L2'

    region_area_dct = get_polygon(region_name)

    value_df = pd.DataFrame()
    image_df = pd.DataFrame()
    for key, area in region_area_dct.items():

        collection = (
            ee.ImageCollection(image_collection)
            .filterBounds(area)
            .filterDate(start_date, end_date)
            # .map(lambda image: mask_clouds(image, image_name))
            # .map(lambda image: apply_scale_factors(image, image_name))
            .map(lambda image: calculate_indices(image, image_name))
        )

        time_series = collection.map(lambda image: extract_indices_timeseries(image, area))

        each_value_df = to_dataframe(time_series)
        each_value_df['date'] = pd.to_datetime(each_value_df['date'])
        each_value_df['date'] = each_value_df['date'].dt.strftime('%Y-%m-%d')
        each_value_df['area'] = key
        value_df = pd.concat([value_df, each_value_df])

        value_df['RVI'] = value_df['RVI'] * 10
        value_df['CVI'] = value_df['CVI'] / 10

        each_image_df = to_image(collection, area)
        each_image_df['area'] = key
        image_df = pd.concat([image_df, each_image_df])


    return value_df, image_df

# def main():
#     get_data('sentinel2', 'buan', '2024-01-01', '2024-10-31',)
#
# if __name__ == '__main__':
#     main()