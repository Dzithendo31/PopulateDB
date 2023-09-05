import json
import requests
import re
import time
from pymongo import MongoClient
import time
import requests
from pymongo.server_api import ServerApi
#In this function we will Populate the AS-Info collections with no partivlar ordering or classifcation
#Stores details about the 
countryASN = {"DZ": [], "AO": [], "BJ": [], "BW": [], "BF": [], "BI": [], "CV": [], "CM": [], "CF": [], "TD": [], "KM": [], "CG": [], "CD": [], "DJ": [], "EG": [], "GQ": [], "ER": [], "SZ": [], "ET": [], "GA": [], "GM": [], "GH": [], "GN": [], "GW": [], "CI": [], "KE": [], "LS": [], "LR": [], "LY": [], "MG": [], "MW": [], "ML": [], "MR": [], "MU": [], "MA": [], "MZ": [], "NA": [], "NE": [], "NG": [], "RE": [], "RW": [], "ST": [], "SN": [], "SC": [], "SL": [], "SO": [], "ZA": [], "SS": [], "SD": [], "TZ": [], "TG": [], "TN": [], "UG": [], "EH": [], "ZM": [], "ZW": []}
countryASNComplete= {"DZ": [], "AO": [], "BJ": [], "BW": [], "BF": [], "BI": [], "CV": [], "CM": [], "CF": [], "TD": [], "KM": [], "CG": [], "CD": [], "DJ": [], "EG": [], "GQ": [], "ER": [], "SZ": [], "ET": [], "GA": [], "GM": [], "GH": [], "GN": [], "GW": [], "CI": [], "KE": [], "LS": [], "LR": [], "LY": [], "MG": [], "MW": [], "ML": [], "MR": [], "MU": [], "MA": [], "MZ": [], "NA": [], "NE": [], "NG": [], "RE": [], "RW": [], "ST": [], "SN": [], "SC": [], "SL": [], "SO": [], "ZA": [], "SS": [], "SD": [], "TZ": [], "TG": [], "TN": [], "UG": [], "EH": [], "ZM": [], "ZW": []}

def extract_asn_number(asn_string):
    # Using a regular expression to find the number in the string
    match = re.search(r'\((\d+)\)', asn_string)
    return int(match.group(1)) if match else None

def parse_asn_set(asn_set_str):
    # Remove leading and trailing curly brackets and split by comma
    asn_list_str = asn_set_str[1:-1].split(", ")

    # Extract ASN numbers
    return [extract_asn_number(asn_str) for asn_str in asn_list_str]

def getASperCountry(code):
    # Making the API call
    url = f'https://stat.ripe.net/data/country-asns/data.json?resource={code}&lod=1'

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return

    # Parse the JSON response
    api_data = response.json()
    # Accessing specific data
    routed_asns_str = api_data['data']['countries'][0]['routed']
    non_routed_asns_str = api_data['data']['countries'][0]['non_routed']

    # Parse ASN sets
    routed_asns = parse_asn_set(routed_asns_str)
    non_routed_asns = parse_asn_set(non_routed_asns_str)
    all_asns = routed_asns + non_routed_asns
    countryASN[code] = (all_asns)
    print(countryASN[code])


def getAsInfo(code):
    #get the ASN list for the countires
    asns = countryASN[code]
    # Loop through each ASN in the routed list and make an API call
    for asn in asns:
        url = f"https://www.peeringdb.com/api/net?asn={asn}"
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"An error occurred: {e}")
            #we create the object here
            api_data =    {
            "id": asn,
            "asn":asn,
            "name": "",
            "long_name": "",
            "website": "",
            "IX_count": "",
            "info_traffic": "",
            "info_type": "",
            "info_scope": "Africa",
            "policy_general": "Open",
            "notes": "",
            "created": "",
            "status": "ok",
            "group": "AS"
    }
            countryASNComplete[code].append(api_data)
            time.sleep(2)
            continue

        # Parse the JSON response
        api_data = response.json()
        #get the data
        as_data = api_data['data'][0]
        #Tranform The Data to the correct format
        as_transformed = {
                "id": as_data.get("asn", ""),
                "asn": as_data.get("asn", ""),
                "Organisation": as_data.get("org_id", ""),
                "name": as_data.get("name", ""),
                "long_name": as_data.get("name_long", "name"),
                "website": as_data.get("website", ""),
                "IX_count": as_data.get("ix_count",0),
                "info_traffic": as_data.get("info_traffic", ""),
                "info_type" : as_data.get("info_type",""),
                "info_scope" : as_data.get("info_scope",""),
                "policy_general" : as_data.get("policy_general",""),
                "notes": as_data.get("notes", ""),
                "created" : as_data.get("created",""),
                "status": as_data.get("status", ""),
                "group" : "AS"
                # other -- please check
            }
        countryASNComplete[code].append(as_transformed)
        time.sleep(4)
    print(f"Done with {code}")

def main():


    #Publish to the DATABASE
    url = "mongodb+srv://zyonmathegu:hmFK9DmKUFuG2kxs@cluster0.yatajyo.mongodb.net/?retryWrites=true&w=majority"
    
    # Connect to the MongoDB server running on localhost at the default port 27017
    #client = MongoClient("mongodb://localhost:27017/")
    client = MongoClient(url, server_api=ServerApi('1'))
    # # Access the database named 'mydatabase'
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)

    database = client['AfricaHope']
    collection = database["AS-INFO"]
    for country_code in countryASNComplete:
        print(f"processing {country_code}")
        #Get the ASN
        getASperCountry(country_code)
        #add the AS details to the database
        getAsInfo(country_code)
        #put all these details in the Database(one database)
        collection.insert_many(countryASNComplete[country_code])

main()
