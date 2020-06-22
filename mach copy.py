import sys
import bluetooth

if __name__ == "__main__":
    uuid = "skullpos"
    nearby_devices = bluetooth.discover_devices()
    print(nearby_devices)
    for bdaddr in nearby_devices:
        if target_name == bluetooth.lookup_name( bdaddr ):
            target_address = bdaddr
            break

    service_matches = bluetooth.find_service(uuid=uuid, address=addr)
