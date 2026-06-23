import requests
import urllib3
import json
import logging

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NSX_API:
    def __init__(self, manager_fqdn: str = None, username: str = None, password: str = None):
        self.manager_fqdn = manager_fqdn
        self.username = username
        self.password = password
        self.cred = (self.username, self.password)
        self.base_url = "https://" + manager_fqdn

    def __execute_search_request(self, url):
        print(f"Search requested URL: {url}")
        try:
            response = requests.get(url=url, verify=False, auth=self.cred)

            if response.status_code == 200:
                response_json = response.json()
                return response_json
            else:
                response.raise_for_status()
                logging.error(response)
        except requests.exceptions.HTTPError as error_http:
            print(f"ERROR! search query failed, Code: {response.status_code} Message {str(error_http)}")
            raise "ERROR! search query failed"

    def search_query(self, queries:list):
        url = self.base_url + "/policy/api/v1/search/query?query="
        and_string = " AND "

        queries_string = and_string.join(queries)
        queries_string = queries_string.replace(' ', '%20')
        queries_string = queries_string.replace('"', '%22')
        queries_string = queries_string.replace('\/', '%5C')

        url += queries_string

        response_json = self.__execute_search_request(url=url)
        results = response_json["results"]

        while "cursor" in response_json.keys():
            url_with_cursor = url + "&cursor=" + response_json["cursor"]
            response_json = self.__execute_search_request(url=url_with_cursor)
            response_results = response_json["results"]
            if len(response_results) > 0:
                results = results + response_results

        return results

    def get_resource_by_type_and_queries(self, resource_type:str, queries:list):
        new_queries = ["resource_type:" + resource_type]
        new_queries += queries

        return self.search_query(queries=new_queries)

    def get_resource_by_type_and_name(self, resource_type:str, resource_name:str):
        return self.get_resource_by_type_and_queries(resource_type=resource_type, queries=['display_name:"' + resource_name + '"'])

    def get_resource_by_type_and_path(self, resource_type:str, resource_path:str):
        return self.get_resource_by_type_and_queries(resource_type=resource_type, queries=['path:"' + resource_path + '"'])

    def get_resource_by_type_and_id(self, resource_type:str, resource_id:str):
        return self.get_resource_by_type_and_queries(resource_type=resource_type, queries=['id:"' + resource_id + '"'])

    #def get_all_tags(self):...

    #def get_tag_effective_resources(self, tag_name:str):...

    #def get_discovered_vm_info(self, vm_name:str):...

    def save_mapping_to_file(self, mapping:dict, file_path:str):
        with open(file_path, "w") as file:
            json.dump(mapping, file, indent=2)

    def read_mapping_from_file(self, file_path:str):
        with open(file_path, "r") as f:
            return json.loads(f.read())

    #def add_tags_to_vm(self, vm_external_id:str, tags:list):...

    #def _get_site_from_path(self, path:str):...

    #def create_gfw_rulebase_mapping(self):...

    def get_local_groups(self):
        return self.get_resource_by_type_and_queries(resource_type="group", queries=['parent_path:"/infra/domains/default"'])

    def get_group_by_path(self, path:str):
        return self.get_resource_by_type_and_queries(resource_type="group", queries=['path:"' + path + '"'])

    def create_group_from_dict(self, group_data:dict):
        group_id = group_data["id"]
        url = self.base_url + "/policy/api/v1/infra/domains/default/groups/" + group_id

        payload = group_data

        try:
            print(f"PATCH {url}")
            pprint(payload)
            response = requests.patch(url=url, auth=self.cred, json=payload, verify=False)

            if response.status_code == 200:
                print(f"Successfully created group {group_id}")
                return

            try:
                err = response.json().get("error_message", response.text)
            except ValueError:  # not JSON
                err = response.text
            raise requests.exceptions.HTTPError(
                f"{response.status_code} - {err}", response=response
            )
        except requests.exceptions.HTTPError as error_http:
            print(f"ERROR! unable to create group, Code: {response.status_code} Message {str(error_http)}")
            raise "ERROR! unable to create group"
  
    def get_virtual_machines(self):
        results = []
        url = self.base_url + "/api/v1/fabric/virtual-machines"
        try:
            response = requests.get(url=url, verify=False, auth=self.cred)

            if response.status_code == 200:
                response_json = response.json()
                results += response_json["results"]

                while "cursor" in response_json:
                    curr_cursor = response_json["cursor"]
                    url_with_cursor = url + "?cursor=" + curr_cursor
                    try:
                        print("GET " + url_with_cursor)
                        response = requests.get(url=url_with_cursor, verify=False, auth=self.cred)

                        if response.status_code == 200:
                            response_json = response.json()
                            results += response_json["results"]
                        else:
                            response.raise_for_status()
                            logging.error(response)
                    except requests.exceptions.HTTPError as error_http:
                        print(f"ERROR! couldn't get VMs, Code: {response.status_code} Message {str(error_http)}")
                        raise "ERROR! couldn't get VMs"
            else:
                response.raise_for_status()
                logging.error(response)
        except requests.exceptions.HTTPError as error_http:
            print(f"ERROR! couldn't get VMs, Code: {response.status_code} Message {str(error_http)}")
            raise "ERROR! couldn't get VMs"

        return results

    def map_vm_names_to_tags(self):
        mapping = {}
        vms_without_tag_counter = 0
        all_vms_info = self.get_virtual_machines()
        
        for vm_info in all_vms_info:
            vm_name = vm_info["display_name"]
            vm_external_id = vm_info["external_id"]
            
            if "tags" not in vm_info:
                arr_tags = None
                vms_without_tag_counter += 1
            else:
                arr_tags = vm_info["tags"]
                
            if vm_name not in mapping.keys():
                mapping[vm_name] = {
                    "external_id": vm_external_id,
                    "tags": arr_tags
                }
        
        print(f"A total of {len(mapping.keys())} VMs were mapped.\nNumber of VMs without tag: {vms_without_tag_counter}")
        return mapping

    def add_tags_to_vm(self, vm_external_id: str, tags: list):
        url = self.base_url + "/policy/api/v1/fabric/virtual-machines?action=add_tags"
        
        body = {
            "external_id": vm_external_id,
            "tags": tags
        }
        
        try:
            response = requests.post(url=url, json=body, verify=False, auth=self.cred)
            
            if response.status_code >= 200 and response.status_code <= 300:
                print("Successfully assigned tags to requested vm!")
            else:
                response.raise_for_status()
                logging.error(response)
        except requests.exceptions.HTTPError as error_http:
            print(f"ERROR! couldn't assign tags, Code: {response.status_code} Message {str(error_http)}")
            raise "ERROR! couldn't assign tags"

    def replenish_tags_from_mapping(self, original_mapping: dict):
        new_mapping = self.map_vm_names_to_tags()
        for vm_name in new_mapping.keys():
            if vm_name not in original_mapping.keys():
                continue
            
            curr_tags = new_mapping[vm_name]["tags"]
            vm_external_id = new_mapping[vm_name]["external_id"]
            original_tags = original_mapping[vm_name]["tags"]
            
            found_missing_tags = (curr_tags == None) and (original_tags != None)
            
            if found_missing_tags:
                print(f"Replenishing missing tags for VM named: {vm_name} !")
                self.add_tags_to_vm(vm_external_id=vm_external_id, tags=original_tags)

def main():
    print("------------------------------------")

if __name__ == "__main__":
    main()

    
    def create_service_from_dict(self, service_data:dict):
        service_id = service_data["id"]
        url = self.base_url + "/policy/api/v1/infra/services/" + service_id
        
        payload = service_data
        
        try:
            print(f"PATCH {url}")
            pprint(payload)
            response = requests.patch(url=url, auth=self.cred, json=payload, verify=False)
            
            if response.status_code == 200:
                print(f"Successfully created service {service_id}")
                return
                
            try:
                err = response.json().get("error_message", response.text)
            except ValueError:  # not JSON
                err = response.text
            raise requests.exceptions.HTTPError(
                f"{response.status_code} - {err}", response=response
            )
        except requests.exceptions.HTTPError as error_http:
            print(f"ERROR! unable to create service, Code: {response.status_code} Message {str(error_http)}")
            raise "ERROR! unable to create service"
            









    
