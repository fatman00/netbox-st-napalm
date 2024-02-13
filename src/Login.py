import streamlit as st
import pandas as pd
import pynetbox
import urllib3
import time

#Let me use the .env file for variables
import os
from dotenv import load_dotenv

import napalm

# Disable all SSL errors
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

@st.cache_data()
def nbwrapper_devices(url, token, site):
    # Connect to netbox
    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  # Read only token
    nb.http_session.verify = False

    # Collecting all site switches of type cisco
    if site is not None:
        allDevices = nb.dcim.devices.filter(status='active', manufacturer_id=1, site_id=site["id"])
    else:
        allDevices = nb.dcim.devices.filter(status='active', manufacturer_id=1)
    #st.write(list(allDevices))
    allDevices = list(allDevices)
    
    return allDevices

@st.cache_data()
def nbwrapper_sites(url, token):
    # Connect to netbox
    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  # Read only token
    nb.http_session.verify = False

    # Collecting all site switches of type cisco
    allSites = nb.dcim.sites.filter(status='active')
    #st.write(list(allDevices))
    allSites = list(allSites)
    
    return allSites

@st.cache_data()
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

@st.cache_data()
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

@st.cache_data()
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

def selected_devices_format(option):
    return option["name"]

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
        newly["id"] = site.id
        newSite.append(newly)
    selected_site = st.sidebar.selectbox("Select Site", options=newSite, format_func=selected_devices_format, placeholder="Choose a site", index=None)
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
    selected_devices = st.sidebar.multiselect("Select devices", options=newDevices, format_func=selected_devices_format)
    with st.expander("Show data"):
        st.write(selected_devices)
    if st.sidebar.toggle("Connection Allowed", False):
        for device in selected_devices:
            try:
                output = nap_get_facts(device["ip"], cli_username, cli_password)
                with st.container(border=True):
                    st.subheader(output["hostname"])
                    hcol1, hcol2, hcol3 = st.columns(3)
                    scol1, scol2, scol3 = st.columns(3)
                    ncol1, ncol2, ncol3 = st.columns(3)
                    hcol1.write("Napalm:")
                    scol1.write(f'{output["serial_number"]}')
                    ncol1.write(f'{output["hostname"]}')

                    hcol3.write("Netbox:")
                    if output["serial_number"] == device["serial"]:
                        scol3.write(f':green[{device["serial"]}]')
                        dis = True
                    else:
                        scol3.write(f':red[{device["serial"]}]')
                        dis = False

                    scol2.button("-> Sync ->", key=f'sn_sync_{output["hostname"]}', use_container_width=True, disabled=dis, on_click=nb_dev_patch, args=(device["id"], "serial", output["serial_number"]))

                    if output["hostname"] == device["name"]:
                        ncol3.write(f':green[{device["name"]}]')
                        dis = True
                    else:
                        ncol3.write(f':red[{device["name"]}]')
                        dis = False

                    ncol2.button("-> Sync ->", key=f'name_sync_{output["hostname"]}', use_container_width=True, disabled=dis, on_click=nb_dev_patch, args=(device["id"], "name", output["hostname"]))

                    st.divider()
                    

                    with st.expander(f'Raw Fact Data: {output["hostname"]}'):
                        st.write(output)

                    #with st.expander(f"Raw Interface Data: {output["hostname"]}"):
                        #st.write(nap_get_interfaces(device["ip"], cli_username, cli_password))
                
            except Exception as e:
                st.error(e)
                #st.stop()