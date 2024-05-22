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
def atswrapper_bfd(dev_ip, cli_username, cli_password):
    atsbfd = None
    testbed = loader.load(
        {
            "devices": {
                device["name"]: {
                    "connections": {
                        "cli": {
                            "protocol": "ssh",
                            "ip": dev_ip,
                            "init_exec_commands": [],
                            "init_config_commands": []
                        },
                        "settings": {
                            "GRACEFUL_DISCONNECT_WAIT_SEC": 1,
                            "POST_DISCONNECT_WAIT_SEC": 1 # Fix this: https://community.cisco.com/t5/tools/graceful-disconnect-wait-sec-does-not-work/m-p/5092505#M3524
                        }
                    }, # Find a better way to do this: https://github.com/CiscoTestAutomation/genielibs/issues/12
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
    atsdevice.settings.GRACEFUL_DISCONNECT_WAIT_SEC = 0
    atsdevice.settings.POST_DISCONNECT_WAIT_SEC  = 0

    atsbfd = atsdevice.parse('show bfd neighbors details')
    atsdevice.disconnect()
    return atsbfd

@st.cache_data
def atswrapper_hsrp(dev_ip, cli_username, cli_password):
    atsbfd = None
    testbed = loader.load(
        {
            "devices": {
                device["name"]: {
                    "connections": {
                        "cli": {
                            "protocol": "ssh",
                            "ip": dev_ip,
                            "init_exec_commands": [],
                            "init_config_commands": []
                        },
                        "settings": {
                            "GRACEFUL_DISCONNECT_WAIT_SEC": 1,
                            "POST_DISCONNECT_WAIT_SEC": 1
                        }
                    }, # Find a better way to do this: https://github.com/CiscoTestAutomation/genielibs/issues/12
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
    atsdevice.settings.GRACEFUL_DISCONNECT_WAIT_SEC = 0
    atsdevice.settings.POST_DISCONNECT_WAIT_SEC  = 0

    atsbfd = atsdevice.parse('show standby all')
    atsdevice.disconnect()
    return atsbfd

@st.cache_data
def atswrapper_int(dev_ip, cli_username, cli_password):
    atsbfd = None
    testbed = loader.load(
        {
            "devices": {
                device["name"]: {
                    "connections": {
                        "cli": {
                            "protocol": "ssh",
                            "ip": dev_ip,
                            "init_exec_commands": [],
                            "init_config_commands": []
                        },
                        "settings": {
                            "GRACEFUL_DISCONNECT_WAIT_SEC": 1,
                            "POST_DISCONNECT_WAIT_SEC": 1
                        }
                    }, # Find a better way to do this: https://github.com/CiscoTestAutomation/genielibs/issues/12
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
    atsdevice.settings.GRACEFUL_DISCONNECT_WAIT_SEC = 0
    atsdevice.settings.POST_DISCONNECT_WAIT_SEC  = 0

    atsbfd = atsdevice.parse('show interfaces')
    atsdevice.disconnect()
    return atsbfd

def atswrapper_config(dev_ip, cli_username, cli_password, configs):
    atsbfd = None
    testbed = loader.load(
        {
            "devices": {
                device["name"]: {
                    "connections": {
                        "cli": {
                            "protocol": "ssh",
                            "ip": dev_ip,
                            "init_exec_commands": [],
                            "init_config_commands": []
                        },
                        "settings": {
                            "GRACEFUL_DISCONNECT_WAIT_SEC": 1,
                            "POST_DISCONNECT_WAIT_SEC": 1
                        }
                    }, # Find a better way to do this: https://github.com/CiscoTestAutomation/genielibs/issues/12
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
    atsdevice.settings.GRACEFUL_DISCONNECT_WAIT_SEC = 0
    atsdevice.settings.POST_DISCONNECT_WAIT_SEC  = 0

    atsdevice.configure(configs)
    atsdevice.disconnect()

def selected_site_format(option):
    return f'{option["name"]}({option["short"]})'

def selected_devices_format(option):
    return option["name"]


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
        if st.button("Reload ATS Data"):
            atswrapper_bfd.clear()
            atswrapper_int.clear()
            atswrapper_hsrp.clear()
        for device in selected_devices:
            atsinterfaces = None
            try:
                atsint = atswrapper_int(device["ip"], cli_username, cli_password)
                atshsrp = atswrapper_hsrp(device["ip"], cli_username, cli_password)
                atsbfd = atswrapper_bfd(device["ip"], cli_username, cli_password)

            except Exception as error:
                if error != "Parser Output is empty":
                    atsbfd = dict([])
                    with st.container(border=True):
                        st.subheader(f'{device["name"]}')
                        st.error(error)
                        print(error)
            
            with st.container(border=True):
                hcol1, hcol2, hcol3 = st.columns([3,1,1])
                hcol1.subheader(f'{device["name"]}')
                hcol2.link_button("Netbox", f'https://netbox.dccat.dk/dcim/devices/{device["id"]}/', use_container_width=True)
                fixall = hcol3.button("-> Add BFD ->", key=f'{device["id"]}_sync_fixit', use_container_width=True, disabled=False)
                
                with st.expander(f'Raw BFD Data: {device["name"]}'):
                    our_addr = atsbfd.get("our_address", [])
                    allBFDNeiInt = []
                    for addr in our_addr:
                        neiaddr = our_addr[addr].get("neighbor_address", None)
                        neiint = [nei.get("interface") for nei in neiaddr.values()]
                        allBFDNeiInt.extend(neiint)
                    st.write("BFD Interfaces")
                    st.write(allBFDNeiInt)
                    st.write("HSRP Interfaces")
                    allHSRPInt = list(atshsrp.keys())
                    st.write(allHSRPInt)
                    missingBFDint = [int for int in allHSRPInt if int not in allBFDNeiInt]
                    st.write(missingBFDint)


                with st.expander(f'Raw interface Data: {device["name"]}', expanded=True):
                    for interface in atsint:
                        if interface in missingBFDint:
                            st.warning(interface)

                if fixall:
                    globalBFD = ['bfd-template single-hop DC-Template', 'interval min-tx 75 min-rx 75 multiplier 3']
                    for int in missingBFDint:
                        globalBFD.extend([f"interface {int}", "bfd template DC-Template"])
                    st.write(atswrapper_config(device["ip"], cli_username, cli_password, globalBFD))
                    #st.write(globalBFD)

            
            
            
            