import json
import requests

def debug(message):
    print(f"DEBUG: {message}")

def error(message):
    print(f"ERROR: {message}")

class IsMonApi:
    """
    An interface for the Intelsat Monitoring API.
    """

    def __init__(self, username, password, apikey):
        """
        Initializes an instance of IsMonApi.

        Args:
            username (str): The username for authentication.
            password (str): The password for authentication.
            apikey (str): The API key to use.
        """
        self._username = username
        self._password = password
        self._apikey = apikey
        self._base_url = "https://api.intelsat.com/i1/api-monitoring/v1"
        self._sessionid = None
    
    def login(self):
        """
        Logs in to the API and stores the session ID.
        """
        debug("Logging in...")
        data = self._api_call("POST", "auth/login", {
            "username": self._username,
            "password": self._password
        })
        debug(f"Using API key for user: {data["data"]["email"]}")
        self._sessionid = data["data"]["sessionid"]
        return True
    
    def logout(self):
        """
        Logs out of the API.
        """
        debug("Logging out...")
        resp = self._api_call("POST", "auth/logout")
        debug("Logged out.")
        return resp
    
    def _api_call(self, method, endpoint, data=None, params = None):
        """
        Makes a call to the API.

        Args:
            method (str): The HTTP method to use.
            endpoint (str): The endpoint to call.
            data (dict): The data to send in the request.

        Returns:
            dict: The response data.
        """
        url = f"{self._base_url}/{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._sessionid:
            headers["Authorization"] = f"SESSID {self._sessionid}"
        elif endpoint != "auth/login":
            if not self.login():
                return None
        if endpoint == "auth/logout":
            headers["Cache-Control"] = "no-cache"
        if endpoint != "auth/login":
            headers["Ocp-Apim-Subscription-Key"] = self._apikey
        ret = []
        cur_page = 1
        last_page = 2
        session = requests.Session()
        while cur_page < last_page:
            # filter params with None value
            page_params = {k: v for k, v in params.items() if v is not None}
            # add page params
            page_params["__page"] = cur_page
            page_params["__pageSize"] = 100
            # make the request
            req = requests.PreparedRequest()
            req.prepare_url(url, page_params)
            req.method = method
            if method == "POST":
                req.body = json.dumps(data)
            req.headers = headers
            response = session.send(req)
            # check for errors
            if response.status_code != 200:
                debug(f"Error: {response.status_code} - {response.text}")
                return None
            response = response.json()
            if "meta" not in response or data["meta"]["status"] != 200:
                if "statusCode" in response:
                    error(f"{response['statusCode']} - {response['message']}")
                elif "errors" in response and len(response["errors"]) > 0:
                    for err in response["errors"]:
                        error(f"{err['message']}")
                else:
                    error(f"Unhandled Response : {response}")
                return None
            last_page = (response["meta"]["countTotal"] + response["meta"]["pageSize"] - 1) / response["meta"]["pageSize"]
            ret.append(response)
        return ret

    def get_terminal_list(self, id=None, org_id=None, name=None, identifier=None, terminal_subscription_id=None, 
                          network_type_id=None, terminal_type_id=None, longitude=None, latitude=None, last_updated=None,
                          last_sync=None, locked=None, external_id=None, external_name=None):
        """
        Gets a list of terminals.

        Returns:
            list: The list of terminals.
        """
        debug("Getting terminal list...")
        params = {
            "ID": id,
            "OrganizationID": org_id,
            "name": name,
            "identifier": identifier,
            "TerminalSubscriptionID": terminal_subscription_id,
            "NetworkTypeID": network_type_id,
            "TerminalTypeID": terminal_type_id,
            "longitude": longitude,
            "latitude": latitude,
            "lastUpdated": last_updated,
            "lastSync": last_sync,
            "locked": locked,
            "externalID": external_id,
            "externalName": external_name
        }
        return self._api_call("GET", "/terminal/listing", params = params)
    
    def get_metric_list(self, id=None, name=None, unit=None, aggregation_type=None, type=None, element_type=None):
        """
        Gets a list of metrics.

        Returns:
            list: The list of metrics.
        """
        debug("Getting metric list...")
        params = {
            "ID": id,
            "name": name,
            "unit": unit,
            "aggregationType": aggregation_type,
            "type": type,
            "elementType": element_type
        }
        return self._api_call("GET", "/metric/listing", params = params)
    
    def get_terminal_alarms(self, terminal_id, id = None, alarm_type_id = None, severity = None, description = None,
                            acknowledged = None, acknowled_date = None, start_date = None, end_date = None):
        """
        Gets a list of alarms for a terminal.
        """
        debug("Getting terminal alarms...")
        params = {
            "ID": id,
            "AlarmTypeID": alarm_type_id,
            "severity": severity,
            "description": description,
            "acknowledged": acknowledged,
            "acknowledgedDate": acknowled_date,
            "startDate": start_date,
            "endDate": end_date
        }
        return self._api_call("GET", "/terminal/{terminal_id}/alarms", params = params)
    
    def get_terminal_events(self, terminal_id, id = None, event_type_id = None, severity = None, description = None,
                            date = None):
        """
        Gets a list of events for a terminal.
        """
        debug("Getting terminal events...")
        params = {
            "ID": id,
            "EventTypeID": event_type_id,
            "severity": severity,
            "description": description,
            "date": date
        }
        return self._api_call("GET", "/terminal/{terminal_id}/events", params = params)
    
    def get_login_status(self):
        """
        Gets the login status.
        """
        debug("Getting login status...")
        return self._api_call("GET", "/auth/login")
    
    def get_systemwide_filters(self):
        """
        Gets the systemwide filters.
        """
        debug("Getting systemwide filters...")
        return self._api_call("GET", "/core/availableSystemwidefilter")
    
    def get_last_metric_status(self, element_id, metric_id, element_type, human_readable = False):
        """
        Gets the last metric status for an element.
        """
        debug("Getting last metric status...")
        params = {
            "ElementID": element_id,
            "MetricID": metric_id,
            "elementType": element_type,
            "humanReadable": human_readable
        }
        return self._api_call("GET", f"/monitoring/latestStatus", params = params)
        
    def get_monitoring_stats(self, date_from, element_id, metric_id, element_type = None, date_to = None, 
                             limit = None, sort_order = None, resolution = None):
        """
        Gets monitoring statistics.
        """
        debug("Getting monitoring statistics...")
        params = {
            "from": date_from,
            "to": date_to,
            "ElementID": element_id,
            "MetricID": metric_id,
            "elementType": element_type,
            "limit": limit,
            "sortOrder": sort_order,
            "resolution": resolution
        }
        return self._api_call("GET", "/monitoring/stats", params = params)
    

def main():
    """
    The main function.
    """
    api = IsMonApi("username", "password", "apikey")
    api.login()
    res = api.get_monitoring_stats('2024-06-04', 43901, 14)
    print(res)
    api.logout()

if __name__ == "__main__":
    main()

