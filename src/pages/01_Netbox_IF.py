import streamlit as st
import pandas as pd
import pynetbox
import urllib3
import time
#Let me use the .env file for variables
import os
from dotenv import load_dotenv

import napalm
import random

# Disable all SSL errors
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

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
def nap_get_facts(host, username, password):
    driver = napalm.get_network_driver("ios")
    device_conn = driver(
        hostname=host,
        username=username,
        password=password,
        optional_args={"port": 22},
    )
    device_conn.open()
    output = device_conn.get_facts()
    device_conn.close()
    return output

@st.cache_data
def nap_get_interfaces(host, username, password):
    driver = napalm.get_network_driver("ios")
    device_conn = driver(
        hostname=host,
        username=username,
        password=password,
        optional_args={"port": 22},
    )
    device_conn.open()
    output = device_conn.get_interfaces()
    device_conn.close()
    return output

@st.cache_data
def nap_get_interfaces_ip(host, username, password):
    driver = napalm.get_network_driver("ios")
    device_conn = driver(
        hostname=host,
        username=username,
        password=password,
        optional_args={"port": 22},
    )
    device_conn.open()
    output = device_conn.get_interfaces_ip()
    device_conn.close()
    return output

def selected_site_format(option):
    return f"{option["name"]}({option["short"]})"

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

@st.cache_data
def merge_if(nap_ifs, _nb_ifs):
    ifmerge = []
    # Matching the interface name to the rigth interface Type
    for interface in nap_ifs:
        interfaceType = "other"
        if "GigabitEthernet" in interface:
            interfaceType = "1000base-t"
        if "FastEthernet" in interface:
            interfaceType = "100base-tx"
        if "TenGigabitEthernet" in interface:
            interfaceType = "10gbase-x-sfpp"
        if "TwentyFiveGigE" in interface:
            interfaceType = "25gbase-x-sfp28"
        if "FortyGigabitEthernet" in interface: 
            interfaceType = "40gbase-x-qsfpp"
        if "HundredGigE" in interface: 
            interfaceType = "100gbase-x-qsfp28"
        if "BVI" in interface:
            interfaceType = "virtual"
        if "BDI" in interface:
            interfaceType = "virtual"
        if "Vlan" in interface:
            interfaceType = "virtual"
        if "Tunnel" in interface:
            interfaceType = "virtual"
        if "Loopback" in interface:
            interfaceType = "virtual"
        if "Port-channel" in interface:
            interfaceType = "lag"
        if "." in interface:
            interfaceType = "virtual"
        if "AppGigabitEthernet" in interface:
            interfaceType = "virtual"
        if "Trans" in interface:
            interfaceType = "other"
        if "Embedded-Service-Engine" in interface:
            interfaceType = None
        if "NVI0" in interface:
            interfaceType = "other"
        if interfaceType is not None:
            newif = {}
            newif["nap_name"] = interface
            newif["nap_desc"] = nap_ifs[interface]["description"]
            newif["nap_type"] = interfaceType
            ifmatch = [inter for inter in _nb_ifs if inter["name"] == str(interface)]
            ifmatch = ifmatch[0] if len(ifmatch) > 0 else None
            #st.write(ifmatch)
            newif["nb_name"] = str(ifmatch) if ifmatch is not None else None
            newif["nb_desc"] = ifmatch["description"] if ifmatch is not None else None
            newif["nb_id"] = ifmatch["id"] if ifmatch is not None else None
            ifmerge.append(newif)
    return ifmerge

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
    #allDevices = [(dev.name, dev.id) for dev in allDevices]
    #allDevices = {dev.name: dev.serial for dev in allDevices}
    newDevices = []
    for dev in allDevices:
        newly = {}
        newly["name"] = dev.name
        newly["serial"] = dev.serial
        newly["id"] = dev.id
        newly["ip"] = str(dev.primary_ip4).split("/")[0]
        newDevices.append(newly)
    select_all = {}
    select_all["name"] = "--All--"
    
    optionDevices = newDevices
    #optionDevices.insert(0, select_all)
    selected_devices = st.sidebar.multiselect("Select devices", optionDevices, format_func=selected_devices_format)

    with st.expander("Show data"):
        st.write(selected_devices)
    if st.sidebar.toggle("Connection Allowed", False):
        if st.button("Reload NB Data"):
            nbwrapper_interface_all.clear()
            merge_if.clear()
        for device in selected_devices:
            try:
                output = nap_get_facts(device["ip"], cli_username, cli_password)
            except Exception as error:
                with st.container(border=True):
                    st.subheader(f"{device["name"]}")
                    st.error(error)
                continue
            interfaces = nap_get_interfaces(device["ip"], cli_username, cli_password)
            allNbIf=nbwrapper_interface_all(device["id"])
            #merge_if(nap_ifs, nb_ifs)
            ifmerge = merge_if(interfaces, allNbIf)
            with st.container(border=True):
                hcol1, hcol2, hcol3 = st.columns([3,1,1])
                hcol1.subheader(f"{device["name"]}")
                hcol2.link_button("Netbox", f"https://netbox.dccat.dk/dcim/devices/{device["id"]}/", use_container_width=True)
                fixall = hcol3.button("-> Fix all ->", key=f"{device["id"]}_sync_fixit", use_container_width=True)
                
                
                # Find all interfaces that are missing in Netbox but exist on the devices
                missingif = [interface for interface in ifmerge if interface["nb_name"] is None]
                with st.expander(f"Missing interfaces...({len(missingif)})"):
                    st.dataframe(missingif, use_container_width=True)
                    if st.button("-> add ->", key=f"{device["id"]}_sync_add", use_container_width=True, disabled=not len(missingif)) or fixall:
                        nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  # Read only token
                        nb.http_session.verify = False
                        #st.sidebar.write(updateif)
                        ifadder = []
                        for interface in missingif:
                            newInterface = {}
                            newInterface['device']= device["id"]
                            newInterface['name'] = interface["nap_name"]
                            newInterface['type'] = interface["nap_type"]
                            newInterface['description'] = interface["nap_desc"]
                            ifadder.append(newInterface)
                        nb.dcim.interfaces.create(ifadder)

                # Find all interfaces where description is not the same on device and Netbox
                updateif = [interface for interface in ifmerge if interface["nb_desc"] != interface["nap_desc"] and interface["nb_name"] is not None]
                with st.expander(f"Update Netbox Data...({len(updateif)})"):
                    st.dataframe(updateif, use_container_width=True)
                    if st.button("-> Sync ->", key=f"{device["id"]}_sync_update", use_container_width=True, disabled=not len(updateif)) or fixall:
                        nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  # Read only token
                        nb.http_session.verify = False
                        #st.sidebar.write(updateif)
                        nbifarr = []
                        for interface in updateif:
                            #st.stop()
                            nbif = nb.dcim.interfaces.get(interface["nb_id"])
                            nbif.description = interface["nap_desc"]
                            nbifarr.append(nbif)
                        nb.dcim.interfaces.update(nbifarr)

                # Find all interfaces where interface exists in netbox but not on the device
                nap_name = [interface["nap_name"] for interface in ifmerge]
                delif = [interface for interface in allNbIf if str(interface) not in nap_name]
                with st.expander(f"Delete Netbox Data...({len(delif)})"):
                    st.write([int.name for int in delif])
                    if st.button("-> Delete ->", key=f"{device["id"]}_sync_del", use_container_width=True, disabled=not len(delif)) or fixall:
                        nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  # Read only token
                        nb.http_session.verify = False
                        #st.sidebar.write(updateif)
                        nb.dcim.interfaces.delete([int.id for int in delif])
                
                with st.expander(f"Raw Interface Data: {output["hostname"]}"):
                    st.write(interfaces)