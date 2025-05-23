import platform
import netifaces
import scapy.all as scapy
from mac_vendor_lookup import MacLookup
import json
from datetime import datetime
import os
from app.camera.camera import Camera
from app.logger import get_logger

logger = get_logger("ARP SCAN")

"""ARP scanning utilities for detecting Axis Communications cameras on a subnet."""


def get_interface_for_subnet(subnet="192.168.0.0/24"):
    """Return network interface name matching subnet, with Windows NPCAP prefix if needed."""
    subnet_prefix = subnet.split("/")[0][: subnet.rfind(".")]  # e.g., '192.168.0'
    try:
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr["addr"]
                    if ip.startswith(subnet_prefix) and ip != "127.0.0.1":
                        if platform.system() == "Windows":
                            # Convert GUID to NPCAP format
                            return f"\\Device\\NPF_{iface}"
                        return iface
    except:
        pass
    # Fallback to Scapy's interface list
    for iface in scapy.conf.ifaces:
        if platform.system() == "Windows":
            if iface.ip.startswith(subnet_prefix):
                return iface.name
        else:
            if iface.ip.startswith(subnet_prefix) and iface.name != "lo":
                return iface.name
    raise Exception("No interface found for subnet " + subnet)


def arp_scan(ip_range, interface):
    """Perform ARP scan on ip_range via interface; return list of (IP, MAC, Manufacturer)."""
    arp = scapy.ARP(pdst=ip_range)
    ether = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp
    result = scapy.srp(packet, timeout=3, verbose=0, iface=interface)[0]

    mac_lookup = MacLookup()
    devices = []
    for sent, received in result:
        ip = received.psrc
        mac = received.hwsrc
        try:
            manufacturer = mac_lookup.lookup(mac)
        except:
            manufacturer = "Unknown"
        devices.append((ip, mac, manufacturer))
    return devices


def save_results(devices, output_file="cameras.json"):
    """Filter Axis devices, assign IDs, save to JSON file, and return list of tuples."""
    timestamp = datetime.now().strftime("%Y-%m-01 %H:%M:%S")
    axis_devices = [d for d in devices if d[2] == "Axis Communications AB"]

    # Assign sequential IDs starting from 1
    axis_devices_with_id = [
        {
            "ID": i + 1,
            "Timestamp": timestamp,
            "IP Address": ip,
            "MAC Address": mac,
            "Manufacturer": manufacturer,
        }
        for i, (ip, mac, manufacturer) in enumerate(axis_devices)
    ]

    # Save to JSON in the same directory as the script
    output_path = os.path.join(os.path.dirname(__file__), output_file)
    with open(output_path, "w") as f:
        json.dump(axis_devices_with_id, f, indent=4)

    return [
        (d["ID"], d["IP Address"], d["MAC Address"], d["Manufacturer"])
        for d in axis_devices_with_id
    ]


def scan_axis_cameras(ip_range="192.168.0.0/24", output_file="cameras.json"):
    """
    Perform an ARP scan to find Axis Communications cameras, assign IDs, and save results to JSON.
    Returns a list of tuples (ID, IP, MAC, Manufacturer) for Axis devices.
    """
    try:
        # Get the interface dynamically
        interface = get_interface_for_subnet(ip_range)

        # Perform ARP scan
        logger.info(f"Scanning {ip_range} using interface {interface}...")
        devices = arp_scan(ip_range, interface)

        # Save and return Axis devices with IDs
        axis_devices = save_results(devices, output_file)

        if axis_devices:
            logger.info(
                "\t" * 3 + f"-- ARP Scan Results - {len(axis_devices)} cameras: --"
            )
            logger.info("====================================" * 2)
            logger.info("ID\t\tIP Address\tMAC Address\t\tManufacturer")
            for id, ip, mac, manufacturer in axis_devices:
                logger.info(f"{id}\t\t{ip}\t{mac}\t{manufacturer}")
            logger.info("====================================" * 2)
        else:
            logger.info("No Axis cameras found.")

        return axis_devices

    except Exception as e:
        logger.error(
            f"Error during ARP scan: {str(e)}. Ensure you have NPCAP (Windows) or root privileges (Linux/macOS)."
        )
        return []


def find_cameras():
    """Discover Axis cameras and return list of Camera instances with IP and ID."""
    cameras = []
    try:
        scan_results = scan_axis_cameras()
        if scan_results:
            for id, ip, mac, manufacturer in scan_results:
                cameras.append(Camera(ip=ip, id=id))
            return cameras
        else:
            logger.info("No Axis cameras found on 192.168.0.0/24 subnet")
            return []
    except Exception as e:
        logger.error(f"Error during camera discovery: {str(e)}")


if __name__ == "__main__":
    scan_axis_cameras()


def add_cameras():
    """Add cameras manually for testing purposes."""
    cameras = []
    cameras.append(Camera(ip="192.168.0.101", id=1))
    cameras.append(Camera(ip="192.168.0.103", id=2))
    return cameras
