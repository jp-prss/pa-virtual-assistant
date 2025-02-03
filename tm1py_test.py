#%% import 
from TM1py.Services import TM1Service
from TM1py import MDXView, NativeView
from TM1py.Utils.Utils import build_pandas_dataframe_from_cellset
from TM1py.Utils.Utils import build_cellset_from_pandas_dataframe

#%% Environment variables
tm1_credentials = {
    "address":"xxx",
    "user":"xxx",
    "password":"xxx",
    "port": "xxx",
    "ssl":False,
	"namespace":None
}

#%% Test connectivity
try:
    with TM1Service(address=tm1_credentials["address"], 
                    port=tm1_credentials["port"], 
                    user=tm1_credentials["user"], 
                    password=tm1_credentials["password"], 
                    ssl=tm1_credentials["ssl"], 
                    namespace=tm1_credentials["namespace"]) as tm1:    
        server_name = tm1.server.get_server_name()
        print("Connection to TM1 established!! your Servername is: {}".format(server_name))
except Exception as e:
    print("\nERROR:")
    print("\t" + str(e))


# %%
