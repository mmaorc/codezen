import argparse
import logging
from langchain import LLMChain, PromptTemplate
from langchain.chat_models import ChatOpenAI

import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

# I should try to use .gitignore file here
ignored_directories = [
    ".git",
    "node_modules",
    "public",
    ".mypy_cache",
    "venv",
    ".venv",
    "__pycache__",
    "dist",
    "docs",
    ".mypy_cache",
]
ignored_filenames = ["package-lock.json", ".DS_Store", "poetry.lock"]

prompt = """You are an AI debugger who is trying to debug a program for a user based on their file system. The user has provided you with the following files and their contents, finally folllowed by the error message or issue they are facing.

The file list is given between the triple backticks (```), Each file is separated by three dashes (---). There are no files in the project besides the ones listed here.
```
{file_context}
```

The issue is given between the triple hashes (###):
###
{issue_description}
###

If you need further information please ask. If you don't know the answer, say that you don't know.
"""
prompt_template = PromptTemplate(
    input_variables=["file_context", "issue_description"], template=prompt
)


def load_files(root_dir):
    text_splitter = RecursiveCharacterTextSplitter()

    docs = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        relpath = os.path.relpath(dirpath, root_dir)
        if not any(d in relpath for d in ignored_directories):
            for file in filenames:
                if file not in ignored_filenames:
                    abs_file_path = os.path.join(dirpath, file)
                    try:
                        with open(abs_file_path, encoding="utf-8") as f:
                            text = f.read()
                        natural_document = Document(
                            page_content=text,
                            metadata={"source": os.path.join(relpath, file)},
                        )
                        split_document = text_splitter.split_documents(
                            [natural_document]
                        )
                        docs.extend(split_document)
                    except Exception as e:
                        print(
                            f"Exception loading the document {abs_file_path}:\n"
                            + str(e)
                        )

    return docs


def build_context_string(docs):
    all_context = []
    for doc in docs:
        current_file = f"""Relative file path: {doc.metadata["source"]}\nFile content:\n{doc.page_content}\n---\n"""
        all_context.append(current_file)
    all_context_string = "\n".join(all_context)
    return all_context_string


def main():
    parser = argparse.ArgumentParser(description="LLMChain CLI")
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "-m",
        "--model",
        dest="model_name",
        default="gpt-4",
        help="The model name to use for the LLMChain",
    )
    parser.add_argument(
        "-d",
        "--root-dir",
        dest="root_dir",
        default=".//",
        help="The root directory of the project",
    )
    parser.add_argument(
        "issue_description",
        help="The issue description",
    )
    args = parser.parse_args()

    # Set logging level
    logging.basicConfig(level=logging.WARNING)
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    model = ChatOpenAI(model_name=args.model_name)
    llm = LLMChain(llm=model, prompt=prompt_template)

    docs = load_files(args.root_dir)
    context_string = build_context_string(docs)

    logging.info(
        f"Loaded {len(docs)} documents, total of {sum([len(doc.page_content) for doc in docs])} characters"
    )

    result = llm.run(
        file_context=context_string, issue_description=args.issue_description
    )

    print(result)
