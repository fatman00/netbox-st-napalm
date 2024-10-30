import streamlit as st
import pandas as pd
from ncclient import manager
import pynetbox
import xmltodict
import urllib3

#Let me use the .env file for variables
import os
from dotenv import load_dotenv

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
            #merge_if.clear()
        for device in selected_devices:
            try:
                #output = nap_get_facts(device["ip"], cli_username, cli_password)
                #m = manager.connect(host=device["ip"], port=830, username="admin", password="master", hostkey_verify=False, device_params={'name':'iosxe'})
                st.write(f'{device["name"]}')
            except Exception as error:
                with st.container(border=True):
                    st.subheader(f'{device["name"]}')
                    st.error(error)
                continue
            
            with st.container(border=True):
                hcol1, hcol2, hcol3 = st.columns([3,1,1])
                hcol1.subheader(f'{device["name"]}')
                hcol2.link_button("Netbox", f'https://netbox.dccat.dk/dcim/devices/{device["id"]}/', use_container_width=True)
                fixall = hcol3.button("-> Fix all ->", key=f'{device["id"]}_sync_fixit', use_container_width=True, disabled=True)
                allNbIf=nbwrapper_interface_all(device["id"])
                for int in allNbIf:
                    # Filter using top-level container namespace and node matching
                    int_filter = f'''
<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
        <name>{int.name}</name>
    </interface>
</interfaces>
'''
                    with manager.connect(host=device["ip"], port=830, username=cli_username, password=cli_password, hostkey_verify=False, device_params={'name':'iosxe'}) as m:
                        # get-config RPC against the running datastore using a subtree filter
                        reply = m.get_config('running', filter=('subtree', int_filter))

                    reply = xmltodict.parse(reply.data_xml)["data"]
                    description = ""
                    try:
                        description = reply["interfaces"]["interface"].get("description","")
                    except:
                        pass
                    
                    st.write(f"{int.name}({int.id}): '{int.description}' <-> '{description}'")
                    if int.description != description:
                        int.description = description
                        st.write(f"Updating Netbox...{int.save()}")
                