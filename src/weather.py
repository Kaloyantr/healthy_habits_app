import requests

def get_weather(city):
    api_key = "VDPPR2UEY2YU6JBH2EAWAXCWN"
    complete_url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}?unitGroup=metric&key={api_key}&contentType=json"

    response = requests.get(complete_url)
    data = response.json()

    temperature = data['currentConditions']['temp']
    conditions = data["currentConditions"]["conditions"]
    return temperature, conditions
    
print(get_weather('Sofia'))
