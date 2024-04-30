import streamlit as st
import pandas as pd
import pynetbox
import urllib3
import time

#Let me use the .env file for variables
import os
from dotenv import load_dotenv

import random

# Import Ginie
from pyats.topology import loader
from genie.libs import ops
from genie.conf import Genie

# Disable all SSL errors
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()


@st.cache_data
def nbwrapper_vrfs(url, token, vrf=None):
    # Connect to netbox
    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  # Read only token
    nb.http_session.verify = False
    if vrf == None:
        allVrfs = nb.ipam.vrfs.all()
    else:
        allVrfs = nb.ipam.vrfs.filter(name=vrf)

    return list(allVrfs)

@st.cache_data
def nbwrapper_ip_address(url, token, address=None):
    # Connect to netbox
    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  # Read only token
    nb.http_session.verify = False
    if address == None:
        allVrfs = nb.ipam.ip_addresses.all()
    else:
        allVrfs = nb.ipam.ip_addresses.filter(address=address)

    return list(allVrfs)

@st.cache_data
def nbwrapper_devices(url, token, site=None):
    # Connect to netbox
    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  # Read only token
    nb.http_session.verify = False

    # Collecting all site switches of type cisco
    if site is not None:
        allDevices = nb.dcim.devices.filter(status='active', platform=['ios', 'ios-xe'], manufacturer_id=1, site_id=site["id"])
    else:
        allDevices = nb.dcim.devices.filter(status='active', platform=['ios', 'ios-xe'], manufacturer_id=1)
    #st.write(list(allDevices))
    allDevices = list(allDevices)
    
    return allDevices

@st.cache_data
def nbwrapper_sites(url, token):
    # Connect to netbox
    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  # Read only token
    nb.http_session.verify = False

    # Collecting all site switches of type cisco
    allSites = nb.dcim.sites.filter(status='active')
    #st.write(list(allDevices))
    allSites = list(allSites)
    
    return allSites

@st.cache_data
def nbwrapper_interface(url, token, dev_id, ifname=None):
    # Connect to netbox
    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  # Read only token
    nb.http_session.verify = False

    # Collecting all site switches of type cisco
    allIf = nb.dcim.interfaces.filter(device_id=dev_id, name=ifname)
    #st.write(list(allDevices))
    allIf = list(allIf)
    if allIf:
        return dict(allIf[0])
    else:
        return None
    
@st.cache_data
def nbwrapper_interface_all(dev_id):
    # Connect to netbox
    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  # Read only token
    nb.http_session.verify = False

    # Collecting all site switches of type cisco
    allIf = nb.dcim.interfaces.filter(device_id=dev_id)
    #st.write(list(allDevices))
    allIf = list(allIf)
    if allIf:
        return allIf
    else:
        return None

@st.cache_data
def atswrapper_cdp(dev_ip, cli_username, cli_password):
    atsnbrs = None
    testbed = loader.load(
        {
            "devices": {
                device["name"]: {
                    "connections": {"cli": {"protocol": "ssh", "ip": dev_ip, "init_exec_commands": [], "init_config_commands": []}}, # Find a better way to do this: https://github.com/CiscoTestAutomation/genielibs/issues/12
                    "credentials": {
                        "default": {
                            "username": cli_username,
                            "password": cli_password,
                        }
                    },
                    "type": "Device",
                    "os": "iosxe"
                }
            }
        }
    )
    atsdevice = testbed.devices[device["name"]]
    atsdevice.connect(via='cli', log_stdout=True, learn_hostname=True, connection_timeout=10)

    atsnbrs = atsdevice.parse('show cdp neighbors detail')
    return atsnbrs


def selected_site_format(option):
    return f'{option["name"]}({option["short"]})'

def selected_devices_format(option):
    return option["name"]

def nb_if_patch(intid, parameter, value):
    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  # Read only token
    nb.http_session.verify = False
    nbif_def = nb.dcim.interfaces.get(intid)
    match parameter:
        case "lag":
            nbif_def.lag = value
        case "name":
            nbif_def.name = value
    st.sidebar.write(f"{intid}: {parameter} = {value}")
    nbif_def.save()

def nb_if_add(deviceid, ifdata):
    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  # Read only token
    nb.http_session.verify = False

    ifdata['device']= deviceid
    nb.dcim.interfaces.create(ifdata)

def nb_dev_patch(deviceid, parameter, value):
    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  # Read only token
    nb.http_session.verify = False

    nbdevice = nb.dcim.devices.get(deviceid)
    match parameter:
        case "serial":
            nbdevice.serial = value
        case "name":
            nbdevice.name = value
    nbdevice.save()
    #st.write("Now we save")
    #nbwrapper_devices.clear()


st.title("Authentication")
with st.form("Netbox"):
    if "netbox_url" in st.session_state and "netbox_token" in st.session_state:
        netbox_url = st.text_input("Netbox URL", st.session_state["netbox_url"])
        netbox_token = st.text_input("Netbox Token", st.session_state["netbox_token"])
    else:
        netbox_url = st.text_input("Netbox URL", os.getenv('NB_URL'))
        netbox_token = st.text_input("Netbox Token", os.getenv('NB_TOKEN'))
    cli_username = st.text_input("CLI Username", os.getenv('CLI_USERNAME'))
    cli_password = st.text_input("CLI password", os.getenv('CLI_PASSWORD'), type="password")
    submit1 = st.form_submit_button("Submit")

if submit1:

    st.session_state["netbox_url"] = netbox_url
    st.session_state["netbox_token"] = netbox_token

    

if "netbox_url" in st.session_state and "netbox_token" in st.session_state:
    allSites = nbwrapper_sites(st.session_state["netbox_url"], st.session_state["netbox_token"])
    newSite = []
    for site in allSites:
        newly = {}
        newly["name"] = site.name
        newly["short"] = site.custom_fields["short"]
        newly["id"] = site.id
        newSite.append(newly)
    if st.sidebar.button("Reload NB sites"):
        nbwrapper_sites.clear()
        nbwrapper_devices.clear()
        nbwrapper_interface.clear()
    selected_site = st.sidebar.selectbox("Select Site", options=newSite, format_func=selected_site_format, placeholder="Choose a site", index=None)
    allDevices = nbwrapper_devices(st.session_state["netbox_url"], st.session_state["netbox_token"], selected_site)
    newDevices = []
    for dev in allDevices:
        newly = {}
        newly["name"] = dev.name
        newly["serial"] = dev.serial
        newly["id"] = dev.id
        newly["ip"] = str(dev.primary_ip4).split("/")[0]
        newDevices.append(newly)

    selected_devices = st.sidebar.multiselect("Select devices", newDevices, format_func=selected_devices_format)

    with st.expander("Show data"):
        st.write(selected_devices)
    if st.sidebar.toggle("Connection Allowed", False):
        if st.button("Reload NB Data"):
            nbwrapper_interface_all.clear()
            nbwrapper_ip_address.clear()
        for device in selected_devices:
            atsinterfaces = None
            try:
                #atsinterfaces = atswrapper_interfaces(device["ip"], cli_username, cli_password)
                atscdp = atswrapper_cdp(device["ip"], cli_username, cli_password)


            except Exception as error:
                with st.container(border=True):
                    st.subheader(f'{device["name"]}')
                    st.error(error)
                continue
            
            with st.container(border=True):
                hcol1, hcol2, hcol3 = st.columns([3,1,1])
                hcol1.subheader(f'{device["name"]}')
                hcol2.link_button("Netbox", f'https://netbox.dccat.dk/dcim/devices/{device["id"]}/', use_container_width=True)
                fixall = hcol3.button("-> Fix all ->", key=f'{device["id"]}_sync_fixit', use_container_width=True, disabled=False)
                ipData = []
                allNbIf=nbwrapper_interface_all(device["id"])


                neighbors = atscdp['index'] # Interfaces from PyATS
                neighbors = neighbors.values()

                print(neighbors)
                for neighbor in neighbors:
                    st.write(neighbors)
                
                with st.expander(f'Raw Interface IP Data: {device["name"]}'):
                    st.write(neighbors)

                '''
                            #Get the remove device object from netbox
            neiDev = nb.dcim.devices.get(name=sanDeviceId)
            # Get the connection if the interface has been connected
            cableData = dict(nbLocalInt[0]).get("cable")['display'] if dict(nbLocalInt[0]).get("cable") is not None else f"[green]{dict(nbLocalInt[0]).get('cable')}[/green]"
            #nbPort = f'[green]{neighbor.get("port_id", "unknown")}[/green]' if dict(nbLocalInt[0]).get("cable") is None else f'{neighbor.get("port_id", "unknown")}'
            if neiDev is None:
                table.add_row(str(device.name), f"{nbLocalInt[0].name}(None)", str("<None>"),  neighbor.get("port_id", "unknown"), sanDeviceId,  "<Not Found>")
                continue
            nbPortID = 0
            nbPort = ""
            #If we dont have a cable in the local interface everything is fine
            if dict(nbLocalInt[0]).get("cable") is None:
                nbLocalInterface = nb.dcim.interfaces.get(device=neiDev, name=neighbor.get("port_id"))
                nbPortID = nbLocalInterface.id
                nbPort = f'[green]{neighbor.get("port_id", "unknown")}({nbPortID})[/green]'
                # >>> nb.dcim.cables.create(a_terminations=[{"object_type": "dcim.interface", "object_id": 68861}], b_terminations=[{"object_type": "dcim.interface", "object_id": 68946}])
                # GigabitEthernet1/0/7 <> GigabitEthernet1/2
                cable = {
                    "a_terminations": [{"object_type": "dcim.interface", "object_id": nbLocalInt[0].id}],
                    "b_terminations": [{"object_type": "dcim.interface", "object_id": nbPortID}]
                }
                newCables.append(cable)
            elif dict(nbLocalInt[0]).get("cable") is not None:
                # If we have a cable in local interface and neighbor if name is the same
                if dict(nbLocalInt[0]).get("link_peers")[0].get("display") == neighbor.get("port_id"):
                    nbPort = f'[blue]{neighbor.get("port_id", "unknown")}[/blue]'
                # Else we have an error
                else:
                    nbPort = f'[red]{neighbor.get("port_id", "unknown")}[/red]'
            nbRow = f"[blue]{neiDev.name}({neiDev.id})[/blue]" if sanDeviceId in neiDev.name else f"[red]{neiDev.name}({neiDev.id})[/red]"
            table.add_row(str(device.name), f"{nbLocalInt[0].name}({nbLocalInt[0].id})", str(cableData),  nbPort, sanDeviceId,  nbRow)
'''