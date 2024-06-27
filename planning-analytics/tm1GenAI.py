#!/usr/bin/env python
# coding: utf-8

#%% Library imports
import pandas as pd
import numpy as np
import subprocess
import calendar
import requests
import sys
import json
from TM1py.Services import TM1Service
from TM1py.Utils.Utils import build_pandas_dataframe_from_cellset
from TM1py.Utils.Utils import build_cellset_from_pandas_dataframe
from ibm_cloud_sdk_core import IAMTokenManager
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator, BearerTokenAuthenticator

#%% Environment variables
port_number = 59997  # this is the HTTPPortNumber of the TM1 server
address = "localhost"
# Retrieve parameters from the TI process
print(sys.argv)
api_key = str(sys.argv[1])
project_id = str(sys.argv[2])
cube_name = str(sys.argv[3])
view_name = str(sys.argv[4])
prompt = str(sys.argv[5])

tm1_credentials = {
    "address":address,
    "port": str(port_number),
    "user":"admin",
    "password":"apple",
    "ssl":False,
	"namespace":None
}

# Initiate Prompt class to communicate with LLM
class Prompt:
    def __init__(self, access_token, project_id):
        self.access_token = access_token
        self.project_id = project_id

    def generate(self, input, model_id, parameters):
        wml_url = "https://us-south.ml.cloud.ibm.com/ml/v1-beta/generation/text?version=2023-05-28"
        Headers = {
            "Authorization": "Bearer " + self.access_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "model_id": model_id,
            "input": input,
            "parameters": parameters,
            "project_id": self.project_id
        }
        response = requests.post(wml_url, json=data, headers=Headers)
        if response.status_code == 200:
            return response.json()["results"][0]["generated_text"]
        else:
            return response.text
            
# Generate IBM Cloud access token using the API Key
access_token = IAMTokenManager(
    apikey = api_key,
    url = "https://iam.cloud.ibm.com/identity/token"
).get_token()

# Define LLM to use and its decoding parameters
model_id = "meta-llama/llama-3-70b-instruct"
parameters = {
    "decoding_method": "greedy",
    "max_new_tokens": 1000,
    "repetition_penalty": 1
}

# Establish TM1py session
with TM1Service(address=tm1_credentials["address"], 
                port=tm1_credentials["port"], 
                user=tm1_credentials["user"], 
                password=tm1_credentials["password"], 
                namespace=tm1_credentials["namespace"],
                ssl=False) as tm1:    
    # Load defined view as pandas dataframe: 
    df = tm1.cubes.cells.execute_view_dataframe_shaped(cube_name=cube_name,view_name=view_name, private=False, mdx_headers=True)
    # Pull all dimensions and translate technical element IDs to more comprehensible Aliases:
    dimensions = tm1.cubes.get_dimension_names(cube_name, skip_sandbox_dimension=True)
    captions = {}
    for d in dimensions:
        try:
            captions.update(tm1.elements.get_attribute_of_elements(d, d, 'Caption'))
        except Exception:
            continue
            
    for c in df.columns:
        try:
            df[c] = df[c].astype(float)
        except Exception:
            continue
    df = df.rename(captions, axis=1)
    df = df.replace(captions)
    df = df.round(0)
    # Convert dataframe to markdown table to make it interpretable by LLM: 
    df_md = df.to_markdown(index=False, floatfmt='')
    print(df_md)
    
    # Build prompt
    prompt_input = """ <s>[INST] <<SYS>>
You are a helpful, respectful and honest data analyst who is provided with tabular data. Always answer the question asked about the data or follow the instruction on what action to perform on the data, without doing own calculations or adding new rows to the table. 

Your answers should not include any further rows that were not part of the initial tabular data. Only play back the numbers that are provided in the tables. You are not permitted to generate any KPI or statistic that is not reflected in the provided data, like average or deviations.

<</SYS>>

""" + str(prompt) + """

""" + str(df_md) + """

[/INST]
"""
    print(prompt_input)
    
    # Send prompt to LLM
    prompt = Prompt(access_token, project_id)
    prompt_output = prompt.generate(prompt_input, model_id, parameters)
    print(prompt_output)

    #%% Write answer of LLM to TM1 cube
    cell_dict = {(view_name, 'Text'): prompt_output}
    tm1.cubes.cells.write_values('watsonx.ai Output', cell_dict, dimensions=['View', 'Text'])

