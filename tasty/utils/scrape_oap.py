import requests
import os
import json

url = "https://oap.buildingsiot.com/api"

functions_query = """
    {
      functions(version: "1.1"){
        version
        code
        name
        points{
          code
          name
        }
      }
    }
"""

points_query = """
    {
      points(version: "1.1"){
        version
        code
        name
        haystack{
          types{
            tag{
              type
              name
              source
            }
            required
          }
        }
      }
    }
"""

temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
if not os.path.isdir(temp_dir):
    os.mkdir(temp_dir)
functions_file = os.path.join(temp_dir, 'oap_functions_1_1.json')
points_file = os.path.join(temp_dir, 'oap_points_1_1.json')
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}


functions = requests.post(url, json={'query': functions_query}, headers=headers)
points = requests.post(url, json={'query': points_query}, headers=headers)

if functions.status_code == 200:
    with open(functions_file, 'w+') as f:
        f.write(json.dumps(functions.json()))
else:
    print(f"Functions: {functions.status_code}")
    print(f"Content: {functions.content}")

if points.status_code == 200:
    with open(points_file, 'w+') as f:
        f.write(json.dumps(points.json()))
else:
    print(f"Points: {points.status_code}")
    print(f"Content: {points.content}")
