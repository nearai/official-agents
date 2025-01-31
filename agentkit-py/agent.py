import os
import json
import boto3
import base64
import requests
from nearai.agents.environment import Environment
from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper
from cdp_langchain.tools import CdpTool
from cdp import *

class Agent:
    S3_BUCKET_NAME = "memecoins-cash-prod"
    CLOUDFRONT_URL = "https://memecoins.cash"
    wallet_data_file = "wallet_data.txt"
    wallet_data = None

    def __init__(self, env: Environment):
        self.env = env
        self.agentkit = self.initialize_agentkit()
        self.cdp_toolkit = CdpToolkit.from_cdp_agentkit_wrapper(self.agentkit)
        self.tools = self.cdp_toolkit.get_tools()
        self.load_wallet_data()

    def initialize_agentkit(self):
        if os.path.exists(self.wallet_data_file):
            with open(self.wallet_data_file) as f:
                self.wallet_data = f.read()
        return CdpAgentkitWrapper(cdp_wallet_data=self.wallet_data if self.wallet_data else None)

    def load_wallet_data(self):
        self.wallet_data = self.agentkit.export_wallet()
        with open(self.wallet_data_file, "w") as f:
            f.write(self.wallet_data)

    def upload_to_s3(self, bucket_name, path, content):
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "us-east-2"),
        )
        s3.put_object(Bucket=bucket_name, Key=path, Body=content, ContentType='text/html')
        return f"{self.CLOUDFRONT_URL}/{path}"

    def generate_memecoin_content(self, messages, retries=3):
        res = self.env.completion(
            [{"role": "system", "content": "You are a memecoin creator. Output JSON only."}] + messages
        ).strip()
        try:
            return json.loads(res)
        except json.JSONDecodeError:
            if retries > 0:
                messages.append({"role": "user", "content": "Please output only JSON."})
                return self.generate_memecoin_content(messages, retries - 1)
            return None

    def task(self):
        messages = self.env.list_messages()
        if not messages:
            return
        memecoin_data = self.generate_memecoin_content(messages)
        if memecoin_data is None:
            self.env.add_system_log("Failed to generate memecoin JSON.")
            self.env.mark_done()
            return
        memecoin_symbol = memecoin_data["memecoin_symbol"]
        html_content = memecoin_data["html"]
        s3_path = f"{memecoin_symbol}/index.html"
        file_url = self.upload_to_s3(self.S3_BUCKET_NAME, s3_path, html_content)
        memecoin_data["url"] = file_url
        self.env.add_message('assistant', f"Memecoin website online at {file_url}")
        self.generate_logo(memecoin_data, memecoin_symbol)
        self.perform_onchain_interaction()
        self.env.mark_done()

    def generate_logo(self, memecoin_data, memecoin_symbol):
        self.env.add_message('assistant', "Generating memecoin logo...")
        image = self.env.generate_image(f"Create a memecoin logo for {memecoin_data['memecoin']} ({memecoin_symbol})")
        icon_base64 = image.data[0].b64_json
        image_data = base64.b64decode(icon_base64)
        logo_s3_path = f"{memecoin_symbol}/logo.jpg"
        logo_url = self.upload_to_s3(self.S3_BUCKET_NAME, logo_s3_path, image_data)
        self.env.add_message('assistant', f"Memecoin logo saved at {logo_url}")

    def perform_onchain_interaction(self):
        cdp_tool = self.tools.get("transfer")
        if cdp_tool:
            transfer_result = cdp_tool.run({
                "recipient": self.agentkit.get_wallet_address(),
                "amount": "0.01",
                "token": "USDC"
            })
            self.env.add_message('assistant', f"Onchain transaction executed: {transfer_result}")
        else:
            self.env.add_message('assistant', "CDP Tool missing. Cannot perform onchain actions.")

if globals().get('env', None):
    agent = Agent(globals().get('env'))
    agent.task()