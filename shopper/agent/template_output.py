import json
from typing import List, Dict, Any, Optional
from string import Template

from tool_library import CommonTools


class TemplateOutput:
    def __init__(self, nearai_agent_client):
        self.nearai_agent_client = nearai_agent_client

    def load_template(self, template_path: str) -> str:
        """Load HTML template from the specified file path."""
        try:
            with open(template_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            self.nearai_agent_client.add_reply(f"Template file {template_path} not found.")
            return ""

    def render_template(self, template_str: str, context: Dict[str, Any]) -> str:
        """Render HTML template with the given context."""
        template = Template(template_str)
        return template.safe_substitute(context)

    def handle_llm_response(self, products: str | List | Dict, last_search_term: str, chat_message: str,
                            suggestion: str, thread_id, agent_order_id="") -> None:
        """Process JSON data extracted from an LLM response and render templates."""
        try:
            template = self.load_template('template.html')
            item_template = self.load_template('template_item.html')
            near_item_template = self.load_template('template_near_item.html')
        except Exception as e:
            self.nearai_agent_client.add_reply(f"Error loading templates: {e}")
            return

        assert template, "template.html not found"
        assert item_template, "item_template.html not found"

        try:
            items_html = ""
            for item in products:
                try:
                    if("NEAR" in item["payment_methods"]):
                        items_html += self.render_template(near_item_template, item)
                    else:
                        items_html += self.render_template(item_template, item)
                except Exception as e:
                    print(f"Error rendering single item: {item}", e)
        except Exception as e:
            self.nearai_agent_client.add_reply(f"Error rendering items: {e} ")
            return
        try:
            final_html = self.render_template(template,
                                              {'items': items_html,
                                               'last_search_term': last_search_term,
                                               'chat_message': chat_message,
                                               'suggestion': suggestion,
                                               'thread_id': thread_id,
                                               'agent_order_id': agent_order_id})
        except Exception as e:
            self.nearai_agent_client.add_reply(f"Error rendering template: {e}")
            return
        self.nearai_agent_client.write_file("index.html", final_html)


class LocalTestClient:

    def add_reply(self, reply):
        print(reply)

    def write_file(self, filename, content):
        path = '/tmp/nearai/test_output/' + filename
        with open(path, 'w') as file:
            file.write(content)

# Test the TemplateOutput class by invoking it directly
# python template_output.py
if __name__ == "__main__":
    # Load template.html and cached_rapidapi_output.json
    test_client = LocalTestClient()
    template_output = TemplateOutput(test_client)
    template_output.load_template('template.html')
    with open('cached_rapidapi_output.json', 'r', encoding='utf-8') as file:
        data = json.loads(file.read())
    with open('shirt-data.json', 'r', encoding='utf-8') as file:
        shirt_data = json.loads(file.read())
        for shirt in shirt_data:
            data["data"]["products"].insert(0, shirt)
    data = CommonTools.format_products(0, data['data']['products'])
    # print(data)
    template_output.handle_llm_response(data, 'last_search_term', 'chat_message', 'suggestion', 'thread_id')
