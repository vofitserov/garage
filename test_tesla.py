from unittest import TestCase

from tesla import *

TESLA_LOGIN = "vladimir@ofitserov.us"
TESLA_PASSWORD = "dm9sb2R5YTE5NzI="

class TestTesla(TestCase):
    garage = TeslaGarage(TESLA_LOGIN, TESLA_PASSWORD)
    token = garage.get_token()
    print(token.access_token)
    vehicles = garage.get_vehicles()
    print(len(vehicles))
    tesla = vehicles[0]
    #drive_state = tesla.get_drive_state()
    #print(drive_state)
    #charge_state = tesla.get_charge_state()
    #print(charge_state)
    #print("Charge port open:", charge_state["charge_port_door_open"])
    #print("Scheduled charging:", charge_state["scheduled_charging_pending"])
    print(tesla.get_token_headers())
    print(tesla.wake_up())
    print(tesla.drive())
    print(tesla.charge())
    pass
