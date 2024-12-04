import chardet # type: ignore
import json
import openai
import os
import tempfile
import time

from nearai.config import Config, load_config_file
from nearai.shared.models import StaticFileChunkingStrategyParam

# This file is run manually to create the vector store of prompts
# It requires that nearai be installed locally and a user logged in:
#   pip install nearai
#   nearai login
#   python3 setup.py
# The resulting vector store ids are then manually set in the agent for use in the agent.py file.


# Load NEAR AI Hub configuration
CONFIG = Config()
# Update config from global config file
config_data = load_config_file(local=False)
CONFIG = CONFIG.update_with(config_data)
if CONFIG.api_url is None:
    raise ValueError("CONFIG.api_url is None")

base_url = CONFIG.api_url + "/v1"

client = openai.OpenAI(base_url=base_url, api_key=json.dumps(config_data["auth"]))

# Specify existing vector store id to skip files uploading
prompt_vector_store_id = "vs_eede93d96fc9461b8fad5b11" # prompts
api_vector_store_id = "vs_c8166130e69e488e90163e06" # apis

# Upload and add files to the vector store
prompt_files = [
    os.path.join(root, file)
    for root, directory, files in os.walk(os.path.abspath("../data/common-tool-library/prompts"))
    for file in files
    if file.endswith(".md") and os.path.basename(file) != "README.md"
]
#print(prompt_files)

api_files = [
    os.path.join(root, file)
    for root, directory, files in os.walk(os.path.abspath("../data/common-tool-library/apis"))
    for file in files
    if file.endswith(".yaml")
]
# print(api_files)

def detect_encoding(file_path):
    with open(file_path, "rb") as f:
        result = chardet.detect(f.read())
        return result["encoding"]


def convert_to_utf8(file_path, temp_dir):
    try:
        encoding = detect_encoding(file_path)
        if not encoding:
            raise ValueError("Wrong encoding")

        with open(file_path, "rb") as f:
            content = f.read()

        text = content.decode(encoding)
        utf8_content = text.encode("utf-8")

        temp_file_path = os.path.join(temp_dir, os.path.basename(file_path))
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(utf8_content)

        return temp_file_path

    except Exception as e:
        print(f"Error with {file_path}: {e}")
        return None


def create_vector_store_from_files(files, vector_store_name, vs_id=None):
    # Create a vector store or operate on an existing one
    if vs_id:
        existing = True
        vs = client.beta.vector_stores.retrieve(vs_id)
        print(f"Updating Vector store: {vs}")
    else:
        existing = False
        chunking_strategy = StaticFileChunkingStrategyParam(chunk_overlap_tokens=0, max_chunk_size_tokens=800)
        vs = client.beta.vector_stores.create(name=vector_store_name, chunking_strategy=chunking_strategy)
        print(f"Vector store created: {vs}")
    error_count = 0
    success_count = 0
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_files = []

        for file_path in files:
            temp_file_path = convert_to_utf8(file_path, temp_dir)
            if temp_file_path:
                temp_files.append(temp_file_path)

                # todo handle updating existing vector store

                print(f"Processing {os.path.basename(temp_file_path)}")
                try:
                    uploaded_file = client.files.create(
                        file=open(temp_file_path, "rb"),
                        purpose="assistants",
                    )
                    attached_file = client.beta.vector_stores.files.create(
                        vector_store_id=vs.id,
                        file_id=uploaded_file.id,
                    )
                    print(f"File uploaded and attached: {uploaded_file.filename}")
                    success_count += 1
                    # time.sleep(3)
                except Exception as e:
                    error_count += 1
                    print(f"Error uploading {os.path.basename(temp_file_path)}: {e}")
                    if error_count > 100:
                        print("Too many errors. Exiting.")
                        break
    # Poll the vector store status until processing is complete
    print("Polling vector store status...")
    while True:
        status = client.beta.vector_stores.retrieve(vs.id)
        if status.file_counts.completed == success_count:
            print(f"All files processed. {success_count} successful, {error_count} errors. Proceeding with search query.")
            break
        print(f"Files processed: {status.file_counts.completed}/{len(files)}. Waiting...")
        time.sleep(1)
    return vs.id


if prompt_vector_store_id is None:
    print("Creating prompt vector store...")
    prompt_vector_store_id = create_vector_store_from_files(prompt_files, "fabric_prompts", prompt_vector_store_id)
    retrieved_store = client.beta.vector_stores.retrieve(prompt_vector_store_id)
    print(f"Prompt Vector Store details: {retrieved_store}")

if api_vector_store_id is None:
    print("Creating api vector store...")
    api_vector_store_id = create_vector_store_from_files(api_files, "openapi_directory", api_vector_store_id)
    retrieved_store = client.beta.vector_stores.retrieve(api_vector_store_id)
    print(f"API Vector Store details: {retrieved_store}")

