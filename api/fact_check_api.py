
import requests

API_KEY = "AIzaSyAeQ1_xFg1sFN439TerYDNhjpYoF-X7tUQ"
BASE_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

def search_fact_check(query):
    params = {
        'query': query,
        'key': API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json().get('claims', [])
    else:
        return []
