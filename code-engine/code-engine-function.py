def main(params):
    import subprocess
    import sys
    import json
    import os

    def install(package):
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    # Ensure TM1py is installed
    install("TM1py")
    
    from TM1py.Services import TM1Service

    # PA credentials
    credentials = {
    "address": os.environ['address'],
    "port": os.environ['port'],
    "user": os.environ['user'],
    "password": os.environ['password'],
    "ssl":True,
    "namespace":None}


    # Extract Parameter from watsonx Assistant Trigger
    parameter = {
        "organization": params.get('organization', ''),
        "channel": params.get('channel', ''),
        "product": params.get('product', ''),
        "month": params.get('month', ''),
        "year": params.get('year', ''),
        "units": params.get('units', 0)}

    try:
        with TM1Service(address=credentials["address"], port=credentials["port"], user=credentials["user"], password=credentials["password"], ssl=False, namespace=credentials["namespace"]) as tm1:
            # Cellset = Data Record written into PA
            cellset = {
                (parameter["organization"],
                 parameter["channel"],
                 parameter["product"],
                 parameter["month"],
                 parameter["year"],
                 "Forecast",
                 "Units Sold"): parameter["units"]}

            # Write values into PA Cube using TM1py
            tm1.cubes.cells.write_values("Revenue", cellset)
            response = {
                "status": "success",
                "message": "Cell updated successfully",
                "parameters": parameter}
            return {
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps(response)}
    except Exception as e:
        error_message = f"Error occurred: {str(e)}"
        if hasattr(e, 'args') and e.args:
            try:
                error_details = json.loads(e.args[0])
                error_message = f"{error_message}. Details: {error_details}"
            except (json.JSONDecodeError, TypeError):
                pass
        response = {
            "status": "error",
            "message": error_message
        }
        return {
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(response)}

