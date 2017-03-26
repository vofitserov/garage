# http://docs.timdorr.apiary.io/#reference/authentication/tokens/get-an-access-token

import requests
import requests.exceptions
import threading

import time
import sys

TESLA_CLIENT_ID = "e4a9949fcfa04068f59abb5a658f2bac0a3428e4652315490b659d5ab3f35a9e"
TESLA_CLIENT_SECRET = "c75f14bbadc8bee3a7594412c31416f8300256d7668ea7e6e7f06727bfb9d220"

#except requests.exceptions.RequestException as e:
#sys.stderr.write("Failed to create new access token:" + str(e))
#pass


class TeslaToken:
    def __init__(self, input):
        self.access_token = input["access_token"]
        self.created_at = int(input["created_at"])
        self.expires_in = int(input["expires_in"])
        self.current_time = time.time()
        pass

    def valid(self):
        return time.time() < self.created_at + self.expires_in

class Tesla:
    def __init__(self, garage, vehicle, timeout = 30*60):
        self.garage = garage
        self.vehicle_id = vehicle["vehicle_id"]
        self.vin = vehicle["vin"]
        self.display_name = vehicle["display_name"]
        self.id = vehicle["id_s"]
        self.option_codes = vehicle["option_codes"]
        self.timeout = timeout
        pass

    def get_token_headers(self):
        return self.garage.get_token_headers()

    def get_drive_state(self):
        headers = self.get_token_headers()
        if not headers: return None
        url = "%s/api/1/vehicles/%s/data_request/drive_state" % \
              (self.garage.host, self.id)
        r = requests.get(url=url, headers=headers)
        drive_state = r.json()["response"]
        return drive_state

    def get_charge_state(self):
        headers = self.get_token_headers()
        if not headers: return None
        url = "%s/api/1/vehicles/%s/data_request/charge_state" % \
              (self.garage.host, self.id)
        r = requests.get(url=url, headers=headers)
        charge_state = r.json()["response"]
        return charge_state

    # power': 0,
    # timestamp': 1490560781190,
    # longitude': -122.270959,
    # heading': 56,
    # gps_as_of': 1490557255,
    # latitude': 37.550591,
    # speed': None,
    # shift_state': None
    def drive(self):
        state = self.get_drive_state()
        drive_str = "tesla<br>"
        #"as of %d seconds ago<br>" % int(time.time() - state["timestamp"]/1000.0)
        url = "http://maps.google.com/maps?z=12&t=m&q=loc:%f+%f" % \
              (state["latitude"], state["longitude"])
        drive_str += "located at <a href=\"%s\"%s</a><br>" % (url, url)
        if state["speed"]:
            drive_str += "current speed is %.1f mph<br>" % state["speed"]
            pass
        return drive_str


    # user_charge_enable_request': None,
    # time_to_full_charge': 0.0,
    # charge_current_request': 23,
    # charge_enable_request': False,
    # charge_port_led_color': # Green',
    # charge_to_max_range': False,
    # charger_phases': None,
    # battery_heater_on': None,
    # managed_charging_start_time': None,
    # battery_range': 244.49,
    # charger_power': 0,
    # charge_limit_soc': 90,
    # charger_pilot_current': None,
    # charge_port_latch': # Engaged',
    # battery_current': 0.0,
    # charger_actual_current': 0,
    # scheduled_charging_pending': False,
    # fast_charger_type': # <invalid>',
    # usable_battery_level': 90,
    # motorized_charge_port': True,
    # charge_limit_soc_std': 90,
    # not_enough_power_to_heat': False,
    # battery_level': 90,
    # charge_energy_added': 8.09,
    # charge_port_door_open': True,
    # max_range_charge_counter': 0,
    # timestamp': 1490560782898,
    # charge_limit_soc_max': 100,
    # ideal_battery_range': 308.27,
    # managed_charging_active': False,
    # charging_state': # Complete',
    # fast_charger_present': False,
    # trip_charging': False,
    # managed_charging_user_canceled': False,
    # scheduled_charging_start_time': 1490594400,
    # est_battery_range': 208.14,
    # charge_rate': 0.0,
    # charger_voltage': 0,
    # charge_current_request_max': 24,
    # eu_vehicle': False,
    # charge_miles_added_ideal': 35.0,
    # charge_limit_soc_min': 50,
    # charge_miles_added_rated': 28.0
    def charge(self):
        state = self.get_charge_state()
        charge_str = "tesla<br>"
        #"as of %d seconds ago<br>" % int(time.time() - state["timestamp"]/1000.0)
        charge_str += "battery range is %.1f miles<br>" % state["battery_range"]
        charge_str += "%.0f%% full<br>" % state["battery_level"]
        charge_str += "charging is %s<br>" % state["charging_state"]
        if state["charge_port_door_open"]:
            charge_str += "charge port door is open<br>"
        else:
            charge_str += "charge port door is closed<br>"
            pass
        charge_str += "%.0f seconds to full charge<br>" % state["time_to_full_charge"]
        return charge_str

class TeslaGarage:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.token = None
        self.host = "https://owner-api.teslamotors.com"
        self.vehicles = None
        self.lock = threading.Lock()
        pass

    def get_token(self):
        with self.lock:
            if not self.token or not self.token.valid():
                self.token = self.new_token()
                pass
            pass
        return self.token

    def new_token(self):
        self.token = None
        data = {}
        data["grant_type"] = "password"
        data["client_id"] = TESLA_CLIENT_ID
        data["client_secret"] = TESLA_CLIENT_SECRET
        data["email"] = self.email
        data["password"] = self.password.decode("base64")
        url = "%s/oauth/token" % self.host
        r = requests.post(url=url, data=data)
        self.token = TeslaToken(r.json())
        return self.token

    def get_token_headers(self):
        token = self.get_token()
        if not token: return None
        headers = {}
        headers['Authorization'] = 'Bearer ' + token.access_token
        return headers

    def get_vehicles(self):
        if self.vehicles and self.token.valid():
            return self.vehicles
        headers = self.get_token_headers()
        if not headers: return None
        url = "%s/api/1/vehicles" % (self.host)
        r = requests.get(url=url, headers=headers)
        vehicles = r.json()
        self.vehicles = []
        for vehicle in vehicles["response"]:
            self.vehicles.append(Tesla(self, vehicle))
            pass
        return self.vehicles

