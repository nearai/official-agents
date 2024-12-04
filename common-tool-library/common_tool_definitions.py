import requests

class CommonTools:

    def __init__(
            self,
            nearai_agent_client,
            google_api_key: str,
            process_search_results_function = None):
        self.query_vector_store = nearai_agent_client.query_vector_store
        self.hub_client = nearai_agent_client.hub_client
        self.google_programmatic_search_api_key = google_api_key
        self.google_search_engine_id = "67ecbcdfba7584807" # normal google search
        self.process_search_results_function = process_search_results_function or self._process_search_results

    def _process_search_results(self, search_results):
        """Default processing of search results from the google search API, returns result titles

        search_results: the search results from the google search API.
        """
        search_results = search_results["items"]
        search_results = [result["title"] for result in search_results]
        return search_results

    def google_search(self, query):
        """Search the web to find recent information with which to answer questions.

        query: the search query containing what you want to search for.
        """
        api_key = self.google_programmatic_search_api_key
        url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={self.google_search_engine_id}&q={query}"
        response = requests.get(url)
        json = response.json()
        return self._process_search_results(json)

    def api_call(self, api_url, params):
        """Make an API call to a given URL with a query.

        api_url: the URL to make the API call to.
        query: the query to send to the API.
        """
        response = requests.get(api_url, params=params)
        return response.json()

    def prompt_help(self):
        """Provide a list of the prompts available in the common tool library. This is a good tool for general requests for help."""
        with open("prompts.txt") as f:
            prompts = f.read()

        prompts = prompts.replace("\n", ", ")
        return "The following prompts are available in the common tool library: " + prompts

    def prompt_text(self, prompt_id):
        """Retrieve the text of a prompt from the common tool library. Only use if the user specifically asks for information about the prompt.

        prompt_id: the id of the prompt to retrieve.
        """
        prompt_results = self.hub_client.query_vector_store(prompt_id, True)
        return f"The prompt text for {prompt_id} is: \n" + prompt_results[0]["file_content"]
