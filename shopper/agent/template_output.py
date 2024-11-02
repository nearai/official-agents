from typing import List, Dict, Any
from string import Template


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
                            suggestion: str) -> None:
        """Process JSON data extracted from an LLM response and render templates."""
        try:
            template = self.load_template('template.html')
            item_template = self.load_template('template_item.html')
        except Exception as e:
            self.nearai_agent_client.add_reply(f"Error loading templates: {e}")
            return

        assert template, "template.html not found"
        assert item_template, "item_template.html not found"

        try:
            items_html = ""
            for item in products:
                try:
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
                                               'suggestion': suggestion})
        except Exception as e:
            self.nearai_agent_client.add_reply(f"Error rendering template: {e}")
            return
        self.nearai_agent_client.write_file("index.html", final_html)
