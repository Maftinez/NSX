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

    def __execute_search_request(self,

  
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

    def save_mapping_to_file(self, mapping: dict, file_path: str):
        with open(file_path, "w") as file:
            json.dump(mapping, file, indent=2)

    def read_mapping_from_file(self, file_path: str):
        with open(file_path, "r") as f:
            return json.loads(f.read())

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
    print("-----    PLEASE CHOOSE ACTION  -----")
    print("------------------------------------")
    print("1) Create Tags mapping from source NSX")
    print("2) Replenish VMs tags using a mapping to destination NSX")
    print("------------------------------------")
    
    chosen_action_num = input('Action Number: ')
    
    if chosen_action_num == "1":
        source_nsx_fqdn = input('NSX Fqdn: ')
        source_nsx_username = input('Username: ')
        source_nsx_password = input('Password: ')
        file_path = input('File Path: ')
        
        source_nsx = NSX_API(manager_fqdn=source_nsx_fqdn, username=source_nsx_username, password=source_nsx_password)
        source_mapping = source_nsx.map_vm_names_to_tags()
        source_nsx.save_mapping_to_file(mapping=source_mapping, file_path=file_path)
        
    elif chosen_action_num == "2":
        destination_nsx_fqdn = input('NSX Fqdn: ')
        destination_nsx_username = input('Username: ')
        destination_nsx_password = input('Password: ')
        file_path = input('Source mapping file path: ')
        
        destination_nsx = NSX_API(manager_fqdn=destination_nsx_fqdn, username=destination_nsx_username, password=destination_nsx_password)
        source_mapping = destination_nsx.read_mapping_from_file(file_path=file_path)
        destination_nsx.replenish_tags_from_mapping(original_mapping=source_mapping)

if __name__ == "__main__":
    main()
  
