from unittest import TestCase

from tesla import *

class TestTesla(TestCase):
    garage = TeslaGarage("tesla login email", "base64 encoded tesla password")
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
    print(tesla.drive())
    print(tesla.charge())
    pass
