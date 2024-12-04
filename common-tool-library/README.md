# Common Tool Library Agent

This utility agent demonstrates 
 - using standard Tools such as web search, 
 - using a library of prompts to tackle specific problems (sourced from Fabric)
 - using a library of API definitions to interact with external services (in progress)


## Prompt Library
Version 0.0.1 status. Relevant prompts are matched and invoked. Testing initial api definitiions in vector store.

For more on the list of included prompts see [Fabric Prompts](https://github.com/danielmiessler/fabric)


## API Library
Not implemented yet. A few hundred api definitions have been added to the "api" vector store. 

## Example queries
Can answer:
 - what are the available prompts  - uses the Tool prompt_help
 - what is the prompt text for PROMPT_NAME  - uses the Tool prompt_text

Tasks it can do:
 - create a micro summary of an article  - uses the Tool prompt_search and executes the create_micro_summary prompt
Asks for the article text if it is not initially supplied
 - explain this math  - uses the Tool prompt_search and executes the explain_math prompt
 - 157 more, though many are expecting pdfs or videos and have not been tested