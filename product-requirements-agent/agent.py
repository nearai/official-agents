import json
from typing import List, Dict, Any

class ProductRequirementsAgent:
    def __init__(self):
        self.notes = []
        self.documents = []

    def create_prd(self, title: str, description: str, objectives: List[str], scope: List[str]) -> str:
        prd = {
            "title": title,
            "description": description,
            "objectives": objectives,
            "scope": scope
        }
        return json.dumps(prd, indent=4)

    def break_down_prd(self, prd: str) -> Dict[str, Any]:
        prd_data = json.loads(prd)
        project = {
            "title": prd_data["title"],
            "description": prd_data["description"],
            "tasks": []
        }
        for objective in prd_data["objectives"]:
            task = {
                "title": objective,
                "description": f"Task related to {objective}"
            }
            project["tasks"].append(task)
        return project

    def accept_input(self, notes: List[str], documents: List[str]):
        self.notes.extend(notes)
        self.documents.extend(documents)

    def brainstorm_suggestions(self, topic: str) -> List[str]:
        suggestions = [
            f"Consider adding more details about {topic}.",
            f"Include examples related to {topic}.",
            f"Research best practices for {topic}."
        ]
        return suggestions

# Example usage
agent = ProductRequirementsAgent()
agent.accept_input(["Initial note"], ["Initial document"])
prd = agent.create_prd("New Product", "This is a new product.", ["Objective 1", "Objective 2"], ["Scope 1", "Scope 2"])
project = agent.break_down_prd(prd)
suggestions = agent.brainstorm_suggestions("Objective 1")

print("PRD:", prd)
print("Project:", project)
print("Suggestions:", suggestions)
