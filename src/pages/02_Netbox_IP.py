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

    selected_devices = st.sidebar.multiselect("Select devices", newDevices, format_func=selected_devices_format)

    #allVrfs = nbwrapper_vrfs(st.session_state["netbox_url"], st.session_state["netbox_token"])
    #print(allVrfs[0]["name"])
    #allVrfs = [vrf["name"] for vrf in allVrfs]
    #selected_vrf = st.sidebar.selectbox("Select VRF", options=allVrfs)

    with st.expander("Show data"):
        st.write(selected_devices)
    if st.sidebar.toggle("Connection Allowed", False):
        if st.button("Reload NB Data"):
            nbwrapper_interface_all.clear()
            nbwrapper_ip_address.clear()
        for device in selected_devices:
            try:
                napIps = nap_get_interfaces_ip(device["ip"], cli_username, cli_password)
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
                ipData = []
                allNbIf=nbwrapper_interface_all(device["id"])
                for interface in napIps.keys():
                    ifmatch = [inter for inter in allNbIf if inter["name"] == str(interface)]
                    ifmatch = ifmatch[0] if len(ifmatch) > 0 else None
                    if not napIps[interface].get("ipv4"):
                        continue
                    newip = {}
                    newip["ifname"] = str(interface)
                    newip["ipv4"]= list(napIps[interface]["ipv4"].keys())[0]
                    newip["v4prefix"]= napIps[interface]["ipv4"][newip["ipv4"]]["prefix_length"]
                    newip["nbif"] = ifmatch["id"] if ifmatch is not None else None
                    nbaddr = nbwrapper_ip_address(st.session_state["netbox_url"], st.session_state["netbox_token"], address=newip["ipv4"]+"/" + str(newip["v4prefix"]))
                    newip["nbipif"] = nbaddr[0]["assigned_object_id"] if len(nbaddr) > 0 else None
                    newip["nbip"] = nbaddr[0]["id"] if len(nbaddr) > 0 else None
                    newip["nbipaddress"] = nbaddr[0]["address"] if len(nbaddr) > 0 else None
                    ipData.append(newip)
                st.dataframe(ipData, use_container_width=True)
                missingip = [ip for ip in ipData if ip["nbif"] != ip["nbipif"]]
                missingip = [dict(item, **{'update': True}) for item in missingip]
                missingip = st.data_editor(missingip, use_container_width=True, key=f'{device["id"]}_sync_edit', column_order=["update", "ifname", "ipv4", "nbif", "nbipif", "nbip", "nbipaddress"])
                missingip = [item for item in missingip if item["update"]]
                if st.button("-> add ->", key=f'{device["id"]}_sync_add', use_container_width=True, disabled=not len(missingip)):
                    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  # Read only token
                    nb.http_session.verify = False
                    ipadder = []
                    for ipaddr in missingip:
                        # If the ipaddress is assigned to an interface in netbox, we want to reasign it to the correct one
                        if ipaddr["nbipif"] is not None:
                            nbaddr = nb.ipam.ip_addresses.get(int(ipaddr["nbip"]))
                            nbaddr.assigned_object_id = ipaddr["nbif"]
                            nbaddr.save()
                        # Otherwise we just create it and assign it to the interface directly
                        else:
                            newIpAddr = {}
                            newIpAddr['address']= ipaddr["ipv4"]+"/" + str(ipaddr["v4prefix"])
                            newIpAddr['vrf'] = 1
                            newIpAddr['status'] = "active"
                            newIpAddr['assigned_object_type'] = "dcim.interface"
                            newIpAddr['assigned_object_id'] = ipaddr["nbif"]
                            ipadder.append(newIpAddr)
                    nb.ipam.ip_addresses.create(ipadder)

                
                #nbwrapper_interface(url, token, dev_id, ifname=None):
                
                
                with st.expander(f'Raw Interface IP Data: {device["name"]}'):
                    st.write(napIps)