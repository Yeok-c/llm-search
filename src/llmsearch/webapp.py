import argparse
import os
from io import StringIO

import streamlit as st
import yaml
from dotenv import load_dotenv
from loguru import logger
from streamlit import chat_input, chat_message
import langchain

from llmsearch.config import Config
from llmsearch.process import get_and_parse_response
from llmsearch.utils import get_llm_bundle

st.set_page_config(page_title="LLMSearch", page_icon=":robot:", layout="wide")
load_dotenv()

langchain.debug = True

@st.cache_data
def parse_cli_arguments():
    parser = argparse.ArgumentParser(description="Web application for LLMSearch")
    parser.add_argument("--config_path", dest="cli_config_path", type=str, default="")
    try:
        args = parser.parse_args()
    except SystemExit as e:
        os._exit(e.code)
    return args


def hash_func(obj: Config) -> str:
    return str(obj.embeddings.embeddings_path)


@st.cache_data
def load_config(config_file):
    if isinstance(config_file, str):
        logger.info(f"Loading data from a file: {config_file}")
        with open(config_file, "r") as f:
            string_data = f.read()
    else:
        stringio = StringIO(config_file.getvalue().decode("utf-8"))
        string_data = stringio.read()

    config_dict = yaml.safe_load(string_data)
    return Config(**config_dict)


@st.cache_resource(hash_funcs={Config: hash_func})
def get_bundle(config):
    return get_llm_bundle(config)


@st.cache_data
def generate_response(question: str, _config: Config, _bundle):
    # _config and _bundle are under scored so paratemeters aren't hashed
    
    output = get_and_parse_response(
        query=question, config=_config.semantic_search, llm_bundle=_bundle
    )
    return output


st.title(":sparkles: LLMSearch")
args = parse_cli_arguments()
st.sidebar.subheader(":hammer_and_wrench: Configuration")

if args.cli_config_path:
    config_file = args.cli_config_path
else:
    config_file = st.sidebar.file_uploader("Select tempate to load", type=["yml", "yaml"])


if config_file is not None:
    config = load_config(config_file)

    config_file_name = config_file if isinstance(config_file, str) else config_file.name
    with st.sidebar.expander(config_file_name):
        st.json(config.json())

    st.sidebar.write(f"**Model type:** {config.llm.type}")

    st.sidebar.write(f"**Docuemnt path**: {config.embeddings.document_settings[0].doc_path}")
    st.sidebar.write(f"**Embedding path:** {config.embeddings.embeddings_path}")
    st.sidebar.write(f"**Max char size (semantic search):** {config.semantic_search.max_char_size}")

    llm_bundle = get_bundle(config)

    text = st.chat_input("Enter text")

    if text:
        print(text)
        print(llm_bundle)
        output = generate_response(question = text, _bundle = llm_bundle, _config = config)

        for source in output.semantic_search[::-1]:
            source_path = source.metadata.pop("source")
            score = source.metadata.get("score", None)
            with st.expander(label=f":file_folder: {source_path}", expanded=True):
                st.write(f'<a href="{source.chunk_link}">{source.chunk_link}</a>', unsafe_allow_html=True)
                if score is not None:
                    st.write(f"\nScore: {score}")

                st.text(f"\n\n{source.chunk_text}")

        with chat_message("assistant"):
            st.write(output.response)

else:
    st.info("Choose a configuration template to start...")
