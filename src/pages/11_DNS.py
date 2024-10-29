import streamlit as st
import pynetbox
import pandas as pd
import urllib3
from io import StringIO

#Let me use the .env file for variables
import os
from dotenv import load_dotenv

# Disable all SSL errors
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()


@st.cache_data()
def nbwrapper_getVrfs(url, token):
    # Connect to netbox
    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  
    nb.http_session.verify = False

    # Collecting all ip addresses with active, in vrf =1 with a dns tag and not empty
    allVrfs = nb.ipam.vrfs.all()

    allVrfs = list(allVrfs)
    
    return allVrfs


#@st.cache_data()
def nbwrapper_ipv4addr(url, token):
    # Connect to netbox
    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  
    nb.http_session.verify = False

    # Collecting all ip addresses with active, in vrf =1 with a dns tag and not empty
    allAddr = nb.ipam.ip_addresses.filter(status='active', present_in_vrf_id=1, tag="dns")

    allAddr = list(allAddr)
    
    return allAddr

@st.cache_data()
def nbwrapper_findIpv4Addr(url, token, addr):
    # Connect to netbox
    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"])  
    nb.http_session.verify = False

    # Collecting all ip addresses with active, in vrf =1 with a dns tag and not empty
    #allAddr = nb.ipam.ip_addresses.filter(status='active', present_in_vrf_id=vrfid, q=addr)
    allAddr = nb.ipam.ip_addresses.filter(status='active', q=addr)

    allAddr = list(allAddr)
    
    if len(allAddr) == 0: 
        raise Exception(f"No matching addresses found for {addr}")
    else: 
        return allAddr[0]

def nb_ip_patch(id, dns_name):
    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"]) 
    nb.http_session.verify = False
    nbip = nb.ipam.ip_addresses.get(id)
    if nbip.dns_name != dns_name:
        nbip.dns_name = dns_name
        nbip.tags.append(236)
        saved = nbip.save()
        #st.sidebar.write(saved)

def nb_address_add(status, address, vrf):
    nb = pynetbox.api(st.session_state["netbox_url"], token=st.session_state["netbox_token"]) 
    nb.http_session.verify = False

    newIpAddr = {}
    newIpAddr['address'] = address
    newIpAddr['vrf'] = vrf
    newIpAddr['status'] = status

    return nb.ipam.ip_addresses.create(newIpAddr)

st.title("Authentication")
with st.form("Netbox"):
    if "netbox_url" in st.session_state and "netbox_token" in st.session_state:
        netbox_url = st.text_input("Netbox URL", st.session_state["netbox_url"])
        netbox_token = st.text_input("Netbox Token", st.session_state["netbox_token"])
    else:
        netbox_url = st.text_input("Netbox URL", os.getenv('NB_URL'))
        netbox_token = st.text_input("Netbox Token", os.getenv('NB_TOKEN'))
    submit1 = st.form_submit_button("Submit")

if submit1:

    st.session_state["netbox_url"] = netbox_url
    st.session_state["netbox_token"] = netbox_token
uploaded_file = None
if "netbox_url" in st.session_state and "netbox_token" in st.session_state:
    # Make a sidebar with filters for netbox IP address
    st.sidebar.write("Netbox filters for IP adderess matching:")
    vrfs = nbwrapper_getVrfs(st.session_state["netbox_url"], st.session_state["netbox_token"])
    #vrfs = [vrf['name'] for vrf in vrfs]
    newvrfs = []
    for vrf in vrfs:
        tempvrf = {}
        tempvrf['name'] = vrf['name']
        tempvrf['id'] = vrf['id']
        tempvrf['display'] = vrf['display']
        newvrfs.append(tempvrf)

    vrf = st.sidebar.selectbox(label="Select a VRF:", options=newvrfs, format_func=lambda x: x['display'])
    
    uploaded_file = st.file_uploader("Upload CSV file", type=['csv'],accept_multiple_files=False,key="fileUploader")

if uploaded_file is not None:

    # To read file as bytes:
    bytes_data = uploaded_file.getvalue()
    #st.write(bytes_data)

    # Can be used wherever a "file-like" object is accepted:
    dataframe = pd.read_csv(uploaded_file, sep=';')
    st.header("Raw formatted data")
    st.dataframe(dataframe, use_container_width=True, hide_index=True)
    newdata = []
    for idx, data in dataframe.iterrows():
        tempdata = {}
        tempdata['apply'] = False
        tempdata['Name'] = data['Name']
        tempdata['IP'] = data['IP']
        tempdata['nbid'] = None
        tempdata['nbdns'] = None
        tempdata['nbvrfid'] = None
        tempdata['nbvrfdis'] = None
        try:
            addr1 = nbwrapper_findIpv4Addr(st.session_state["netbox_url"], st.session_state["netbox_token"], data['IP']+"/")
            print("NB OBJ:" + str(addr1))
            #st.write(dict(addr1))
            if data['IP'] in addr1['address']:
                #st.write(addr1['id'])
                #nb_ip_patch(addr1['id'], data['Name'])
                tempdata['nbid'] = addr1['id']
                tempdata['nbdns'] = addr1['dns_name']
                if addr2 := addr1['vrf']:
                    tempdata['nbvrfid'] = addr2['id']
                    tempdata['nbvrfdis'] = addr2['display']
            else:
                pass
        except Exception as e:
            print(e)
            pass
        newdata.append(tempdata)
    st.header("Combined data with Netbox")
    with st.form("myform"):
        st.dataframe(newdata, use_container_width=True, hide_index=True)
        col1, col2, col3 = st.columns(3)
        prefix = col1.text_input("prefix length:", value="/24", label_visibility='collapsed')
        if col2.form_submit_button("Create missing prefixes"):
            for data in newdata:
                st.write(f"Will now create {data['IP']}")
                if data['nbid'] == None:
                    try:
                        print(nb_address_add('active', data['IP'] + prefix, vrf['id']))
                    except:
                        pass
        
        if col3.form_submit_button("Update DNS"):
            for data in newdata:
                st.write(f"Will now update {data['Name']}")
                if data['nbdns'] == "":
                    try:
                        print(nb_ip_patch(data['nbid'], data['Name']))
                    except:
                        pass
    #st.write(dict(nbwrapper_findIpv4Addr(st.session_state["netbox_url"], st.session_state["netbox_token"], "10.0.70.100/")))

st.stop()


if "netbox_url" in st.session_state and "netbox_token" in st.session_state:
    allIpv4Addr = nbwrapper_ipv4addr(st.session_state["netbox_url"], st.session_state["netbox_token"])
    for addr in allIpv4Addr:
        st.write(f"{addr['address'].split('/')[0]} = {addr['dns_name']}")
        #st.write(dict(addr))
else:
    st.write("This will import a lot of files from csv file to netbox.")