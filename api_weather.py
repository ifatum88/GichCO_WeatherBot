import requests
import json

class WeatherAPI():
    def __init__(self) -> None:
        self.api_keys_jsonfile = "api_keys.json"
        self.api_keys = self.import_apikeys()
        
    def import_apikeys(self) -> dict: 
        with open(self.api_keys_jsonfile,"r",encoding="utf-8") as json_file:
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
            'q':city_name,
            'appid':self.api_keys['openweathermap']['key']
        }
        
        request = requests.get(url=url,params=params)
        request_data = request.json()
        return_data = None
        
        for location in request_data:
            if location['country'] == 'RU':
                return_data = {
                    'name':location['name'],
                    'local_name':location['local_names']['ru'],
                    'country':location['country'],
                    'state':location['state'],
                    'coords':{
                        'lat':location['lat'],
                        'lon':location['lon']
                    }
                }
                
        return return_data