# import logging
# import subprocess

# # def set_location(address, port, lat: float, lng: float):
# #     try:
# #         subprocess.Popen(
# #             ['pymobiledevice3', 'developer', 'dvt', 'simulate-location', 'set', '--rsd', address, str(port), '--', str(lat), str(lng)],
# #             stdin=subprocess.PIPE,  # 重定向标准输入
# #             stdout=subprocess.PIPE,  # 重定向标准输出
# #             stderr=subprocess.PIPE  # 重定向标准错误
# #         )
# #     except subprocess.CalledProcessError as e:
# #         logging.error(f"Error simulating location: {e}")

# # from pymobiledevice3.lockdown import create_using_usbmux
# # from pymobiledevice3.lockdown import LockdownClient
# # from pymobiledevice3.services.simulate_location import DtSimulateLocation

# # def set_location(address, port, lat: float, lng: float):
# #     try:
# #         # 连接到设备
# #         lockdown = create_using_usbmux()
# #         print(1)
# #         DtSimulateLocation(lockdown).set(lat, lng)

# #     except Exception as e:
# #         logging.error(f"Error simulating location: {e}")





# # from pymobiledevice3.lockdown import LockdownClient
# # from pymobiledevice3.service_connection import ServiceConnection
# # from pymobiledevice3.services.simulate_location import DtSimulateLocation


# # def set_location(address, port, lat: float, lng: float):
# #     try:
# #         service = ServiceConnection.create_using_tcp(address, port)
# #         lockdown_client = LockdownClient(service)
# #         DtSimulateLocation(lockdown_client).set(lat, lng)
# #         lockdown_client.stop_session()
# #         lockdown_client.close()


# #     except Exception as e:
# #         logging.error(f"Error simulating location: {e}")


# from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService
# from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation
# from pymobiledevice3.services.dvt.dvt_secure_socket_proxy import DvtSecureSocketProxyService

# # Assuming 
# host = 'fdc3:16b1:5cac::1'
# port = 52954
# rsd = RemoteServiceDiscoveryService((host, port))
# await rsd.connect()

# # Use it to create a DVT instance
# dvt = DvtSecureSocketProxyService(rsd)
# dvt.perform_handshake()
# LocationSimulation(dvt).set(LAT, LON)