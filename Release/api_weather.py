import requests
import json

"""
TODO:
1. Сделать обработку, когда возращается несколько городов с одним названием.
   Пока прикрыто кастылем. Ищет только по городам РФ.
"""

class WeatherAPI():
    def __init__(self) -> None:
        self.api_keys = self.import_apikeys()
        self.weather_brokers = self.set_brokers()
        
    def import_apikeys(self) -> dict: 
        json_file_name = "api_keys.json"
        
        with open(json_file_name,"r",encoding="utf-8") as json_file:
            return json.loads(json_file.read())

    def get_city_by_name(self, city_name:str):
        """
        Args:
            city_name (str): city_name
            
        Returns:
            dict: {"name","local_name","country","state","coords":{"lat","lon"}}
        """
        url = "https://api.openweathermap.org/geo/1.0/direct"
        params = {
            'q':f"{city_name},RU",
            'appid':self.api_keys['openweathermap']['key'],
            'limit':1
        }
        
        request = requests.get(url=url,params=params)
        request_data = request.json()
        return_data = None
        
        try:
            return_data = {
            'name':request_data[0]['name'],
            'local_name':request_data[0]['local_names']['ru'],
            'country':request_data[0]['country'],
            'state':request_data[0]['state'],
            'coords':{
                'lat':request_data[0]['lat'],
                'lon':request_data[0]['lon']
            }
        }
        except:
            pass
  
        return return_data
    
    def set_brokers(self) -> list:
        out_list = []
        
        #Add openweathermap
        out_list.append({
            'name':"openweathermap",
            'url':"https://api.openweathermap.org/data/2.5/weather",
            'params':{
                'lat':"",
                'lon':"",
                'appid':self.api_keys['openweathermap']['key'],
                'units':"metric",
                'lang':"ru"
            }
        })
        
        return out_list
    
    def get_weather(self,city_data:dict) -> list:
        
        brokers_list = self.weather_brokers
        return_data = []
        for broker in brokers_list:
            broker['params']['lat'] = city_data['coords']['lat']
            broker['params']['lon'] = city_data['coords']['lon']
            
            request = requests.get(url=broker['url'],params=broker['params'])
            request_data = request.json()
            
            broker['weather'] = dict()
            
            # ПРИВЕДЕНИЕ ДАННЫХ API В СТАНДАРТНЫЙ ВИД
            match broker['name']:
                # Для openweathermap
                case "openweathermap":
                    broker['weather']['main'] = request_data['weather'][0]['main']
                    broker['weather']['temp'] = int(round(request_data['main']['temp'],0))
                    broker['weather']['feels_like'] = int(round(request_data['main']['feels_like'],0))
                    broker['weather']['temp_min'] = int(round(request_data['main']['temp_min'],0))
                    broker['weather']['temp_max'] = int(round(request_data['main']['temp_max'],0))
                    broker['weather']['pressure'] = request_data['main']['pressure']
                    broker['weather']['humidity'] = request_data['main']['humidity']
            
            return_data.append(broker) 
            
        return return_data