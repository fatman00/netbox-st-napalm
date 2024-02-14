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


def selected_site_format(option):
    return f'{option["name"]}({option["short"]})'

def selected_devices_format(option):
    return option["name"]

def nb_if_patch():
    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  # Read only token
    nb.http_session.verify = False
    #st.sidebar.write(updateif)
    for interface in updateif:
        #st.stop()
        nbif = nb.dcim.interfaces.get(interface["nb_id"])
        nbif.description = interface["nap_desc"]
        saved = nbif.save()
        st.sidebar.write(saved)
        st.sidebar.write(interface)

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
                device_info = {
                    'device_type': 'ios',
                    'ip': device["ip"],
                    'username': cli_username,
                    'password': cli_password,
                }
                testbed = loader.load(
                    {
                        "devices": {
                            device["name"]: {
                                "connections": {"cli": {"protocol": "ssh", "ip": device_info["ip"], "init_exec_commands": [], "init_config_commands": []}}, # Find a better way to do this: https://github.com/CiscoTestAutomation/genielibs/issues/12
                                "credentials": {
                                    "default": {
                                        "username": device_info["username"],
                                        "password": device_info["password"],
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

                atsinterfaces = atsdevice.learn('interface')
                atsinterfaces = atsinterfaces.to_dict().get('info')


            except Exception as error:
                with st.container(border=True):
                    st.subheader(f'{device["name"]}')
                    st.error(error)
                continue
            
            with st.container(border=True):
                hcol1, hcol2, hcol3 = st.columns([3,1,1])
                hcol1.subheader(f'{device["name"]}')
                hcol2.link_button("Netbox", f'https://netbox.dccat.dk/dcim/devices/{device["id"]}/', use_container_width=True)
                #fixall = hcol3.button("-> Fix all ->", key=f'{device["id"]}_sync_fixit', use_container_width=True, disabled=True)
                ipData = []
                allNbIf=nbwrapper_interface_all(device["id"])
                for interface in atsinterfaces:
                    st.write(interface)
                
                
                with st.expander(f'Raw Interface IP Data: {device["name"]}'):
                    st.write(atsinterfaces)