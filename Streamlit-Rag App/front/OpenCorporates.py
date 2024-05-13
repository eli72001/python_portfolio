import json
import requests


class OpenCorporates:
    """_summary_
    """
    def __init__(self):
        pass

    def call_api(self, jurisdiction: str, company_number: str, token: str): #calls api based on company number

        #url to call
        statements_url = 'https://api.opencorporates.com/v0.4/companies/' + jurisdiction + '/' + company_number + '?api_token=' + token
        r = requests.get(url = statements_url,
                         timeout=5)
        data = r.json()
        return data # returns json data from opencorporates

    @staticmethod
    def loose_search_api(company_name: str, jurisdiction_code: str, token: str): #calls a search based on company name and jurisdiction
        #url to call
        statements_url = 'https://api.opencorporates.com/v0.4/companies/search?q='+ company_name + '&jurisdiction_code='+ jurisdiction_code + '&per_page=1&page=1&order=score&amp;api_token=' + token
        r = requests.get(url = statements_url,
                         timeout=5)
        data = r.json()
        return data

    def pad_cik(self, cik): # function that pads cik
        """_summary_

        Args:
            cik (_type_): _description_

        Returns:
            _type_: _description_
        """
        desired_length = 10
        num_zeros = desired_length - len(cik)
        padded_cik = '0' * num_zeros + cik
        return padded_cik
  
    def updated_search_api(self, token: str, jurisdiction_code: str, company_name: str, cik = ''): #calls api to search for company
        if cik == '': #no cik input go straight to loose search
            data = self.loose_search_api(company_name, jurisdiction_code, token)
            return self.call_api(jurisdiction_code, data['company']['company_number'], token)
        #first call with no leading zeros ASSUMES NO LEADING ZEROS
        statements_url = 'https://api.opencorporates.com/v0.4/companies/search?q='+ '' + '&jurisdiction_code='+ jurisdiction_code + '&identifier_uids='+ cik + '&per_page=1&page=1&order=score&amp;api_token=' + token
        r = requests.get(url = statements_url,
                         timeout=5)
        data = r.json()
        if data['results']['total_count'] == 0: # if no company is returned pad cik with zeros
            pad_cik = pad_cik(cik)
            statements_url = 'https://api.opencorporates.com/v0.4/companies/search?q='+ '' + '&jurisdiction_code='+ jurisdiction_code + '&identifier_uids='+ pad_cik + '&per_page=1&page=1&order=score&amp;api_token=' + token
            r = requests.get(url = statements_url, 
                             timeout=5)
            data = r.json()
            if data['results']['total_count'] == 0: # if no company is returned run loose search
                data = self.loose_search_api(company_name, jurisdiction_code, token)
                return self.call_api(jurisdiction_code, data['company']['company_number'], token)

        #if we successfully pull the company from api exit and check for registered addresss
        return self.call_api(jurisdiction_code, data['results']['companies'][0]['company']['company_number'], token) #json format

    def clean_data(self, data): # goes through inputted opencorporates json file and returns only specific items

        #has_registerered_address is true if registered_address is really a reg address, else it is agent address or not available

        if list(data.keys())[0] != 'company': #not pared down to specific company
            data = data['results'] #get results
        if list(data.keys())[0] == 'companies':
            data = data['companies'][0]

        data = data['company'] #pare down to company data

        clean_data = {}
        clean_data.update({'has_registered_address': False}) #default false
        keep_items = ['name', 'agent_name', 'agent_address', 'company_number', 'jurisdiction_code', 'incorporation_date', 'registry_url', 'source','opencorporates_url', 'registered_address', 'officers', 'directors']
        for i in keep_items:
            if i in list(data.keys()):
                if i == 'registered_address':
                    clean_data.update({'has_registered_address': True}) #update to show file contains a true registered address
                    clean_data.update({i:data[i]})
                if i == 'agent_address':
                    clean_data.update({'registered_address': data[i]}) #label agent address as registered address
                else:
                    clean_data.update({i:data[i]})
        return clean_data

    def save_file(self, filename, data): # saves a file with json dataikbuikb
        title = filename +'.json' # build custom filename
        file = open(f'db-rag-llm/front/company_json/{title}', 'a') 
        json.dump(data, file) # add data to file
        file.close()
        return file
    
    @staticmethod
    def get_jurisdiction_code(location, file): #takes location pulled from document and opencorportates jurisdiction file
        with open(file,"r") as f:
                data = json.load(f)
        location = location.lower() #control for different capitalizations
        for jurisdiction in data['results']['jurisdictions']:
            if jurisdiction['jurisdiction']['name'].lower() == location:
                return jurisdiction['jurisdiction']['code'] #return opencorporates code for jurisdiction
        return None #jurisdiction not found