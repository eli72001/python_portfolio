import os
class OutputParser:
    """Class to read an output from an LLM and parse it into a file path, pages, and values
    """
    def __init__(self, output):
        """Creates object based on llm output, splits it into a list based on new line characters

        Args:
            output (str): response from llm
        """
        self.output = output.split('\n')

    def delete_before_colon(self, string):
        """Helper function to delete everything before a ':' in a specific line. 

        Args:
            string (str): text to be edited

        Raises:
            ValueError: If the string does not have a colon, this will raise an error

        Returns:
            str: cleaned string without the : and anything before
        """
        if ':' in string:
            index = string.index(':')
            return string[index+2:]
        else:
            raise ValueError("Expected String: [Metadata_Name]:[Value] \n':' not found. Check LLM Output")

    def get_pages(self):
        try:
            page_and_docs = self.output[-1].split('|')
            page_ranges = self.delete_before_colon(page_and_docs[1])
            result = []
            for page_range in page_ranges.split(','):
                page_range = page_range.strip()

                if '-' in page_range:
                    start, end = map(int, page_range.split('-'))
                    result.extend(range(start, end + 1))
                else:
                    result.append(int(page_range))

            return sorted(set(result))
        except Exception as err:
            print(err)
            print(f"Check LLM Output. Expected Page Range, got {page_ranges} instead")
    
    def get_file(self):
        page_and_docs = self.output[-1].split('|')
        file_path = self.delete_before_colon(page_and_docs[0])
        try:

            return os.path.join('company-10ks',file_path).strip()
        except Exception as err:
            print(err)

    def clean_name(self, string):
        """Helper function to clean the output of a llm. Assumes that every line starts with a '-' and if we encounter a name with a position, the name ends right before a '--'
        If a name is not found, it returns everything after the first '-'. If a name is found, it returns everything in between the first '-' and first '--'

        Args:
            string (str): value to be cleaned

        Returns:
            str: cleaned llm output
        """
        start = string.find('*')
        if start == -1:
            start = string[0:3].find('-')
        
        #if start == -1:
        #    return string
        end = string.find('--', start+1)
        if end == -1:
            return string
        if start < 0:
            return string[:end-1]
        return string[start+2:end-1]
    
    def get_values(self):
        """Function to get the actual output from the llm, without the page number or file name

        Returns:
            list: list of values which have been taken from the pdf and put in the llm response, cleaned. 
        """
        values = []
        for name in self.output[:-1]:
            parsed_name = self.clean_name(name)
            if parsed_name:
                values.append(parsed_name)
        return values