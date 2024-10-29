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
def nbwrapper_interface(dev_id, ifname=None):
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
def nbwrapper_device(dev_name):
    # Connect to netbox
    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  # Read only token
    nb.http_session.verify = False

    # Collecting all site switches of type cisco
    allDev = nb.dcim.devices.filter(name=dev_name)
    #st.write(list(allDevices))
    allDev = list(allDev)
    if allDev:
        return dict(allDev[0])
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

def nb_cable_add(cable):
    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  # Read only token
    nb.http_session.verify = False

    return nb.dcim.cables.create(cable)

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
                allNbIf=nbwrapper_interface_all(device["id"])


                neighbors = atscdp['index'] # Interfaces from PyATS
                neighbors = neighbors.values()

                #print(neighbors)
                connections = []
                for neighbor in neighbors:
                    newConnection = {}
                    newConnection['add_me'] = True
                    newConnection['local_device'] = device["name"]
                    newConnection['local_interface'] = neighbor['local_interface']
                    newConnection['local_nbInterface'] = nbwrapper_interface(device["id"], neighbor['local_interface'])['id']
                    newConnection['remote_device'] = neighbor['device_id'].split('.')[0]
                    nbDevID = nbwrapper_device(neighbor['device_id'].split('.')[0])
                    if nbDevID is not None:
                        newConnection['remote_nbDevice'] = nbDevID['id']
                        newConnection['remote_nbInterface'] = nbwrapper_interface(nbDevID['id'], neighbor['port_id'])['id']
                    newConnection['remote_interface'] = neighbor['port_id']
                    if nbwrapper_interface(device["id"], neighbor['local_interface']).get("cable") is not None:
                        newConnection['add_me'] = False
                    if len(newConnection.values()) == 8:
                        connections.append(newConnection)
                cableUpdate = st.data_editor(connections, key=f'{device["id"]}_data_edit', use_container_width=True)
                cableUpdate = [item for item in cableUpdate if item["add_me"]]
                
                with st.expander(f'Raw Interface IP Data: {device["name"]}'):
                    st.write(cableUpdate)
                if fixall:
                    for newCable in cableUpdate:
                        cable = {
                            "a_terminations": [{"object_type": "dcim.interface", "object_id": newCable['local_nbInterface']}],
                            "b_terminations": [{"object_type": "dcim.interface", "object_id": newCable['remote_nbInterface']}]
                        }
                        
                        try:
                            print(nb_cable_add(cable))
                        except Exception as e:
                            print(str(e))
                            #st.error(str(e))

            
            
            
            