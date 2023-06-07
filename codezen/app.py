import argparse
import logging
import subprocess
from pathlib import Path

from binaryornot.check import is_binary
from langchain import LLMChain, PromptTemplate
from langchain.callbacks import get_openai_callback
from langchain.chat_models import ChatOpenAI
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from codezen.ignore_files import filter_files, load_ignore_file


prompt = """You are an AI coder who is trying to help the user develop and debug an application based on their file system. The user has provided you with the following files and their contents, finally folllowed by the error message or issue they are facing.

The file list is given between the triple backticks (```), Each file is separated by three dashes (---). There are no files in the project besides the ones listed here.
```
{file_context}
```

The issue is given between the triple hashes (###):
###
{issue_description}
###

If you are not sure what the answer is, say that explicitly.
"""
prompt_template = PromptTemplate(
    input_variables=["file_context", "issue_description"], template=prompt
)


def get_project_files_paths(root_dir: str) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=root_dir, capture_output=True, text=True
    ).stdout
    file_paths_strings = result.splitlines()
    file_paths = [Path(root_dir) / Path(fp) for fp in file_paths_strings]
    return file_paths


def load_files_to_langchain_documents(root_dir: Path, project_files_paths: list[Path]):
    text_splitter = RecursiveCharacterTextSplitter()

    docs = []
    for file_path in project_files_paths:
        try:
            if is_binary(str(file_path)):
                logging.info(f"Skipping binary file {file_path}")
                continue
            with open(file_path, encoding="utf-8") as f:
                text = f.read()
            relative_path = file_path.relative_to(root_dir)  # Maybe we don't need this?
            natural_document = Document(
                page_content=text,
                metadata={"source": relative_path},
            )
            split_document = text_splitter.split_documents([natural_document])
            docs.extend(split_document)
        except Exception as e:
            raise Exception(f"Exception loading the document {file_path}:\n") from e

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
        "-i",
        "--ignore-file",
        dest="ignore_file",
        default="./.czignore",
        help="The path to the .czignore file",
    )
    parser.add_argument(
        "issue_description",
        help="The issue description",
    )
    args = parser.parse_args()

    # Set logging level
    logging.basicConfig(level=logging.WARNING)
    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    model = ChatOpenAI(model_name=args.model_name)
    llm = LLMChain(llm=model, prompt=prompt_template)

    project_files_paths = get_project_files_paths(args.root_dir)
    czignore_patterns = load_ignore_file(args.ignore_file)
    project_files_paths = (
        filter_files(project_files_paths, czignore_patterns)
        if czignore_patterns
        else project_files_paths
    )

    docs = load_files_to_langchain_documents(args.root_dir, project_files_paths)
    context_string = build_context_string(docs)

    logging.info(
        f"Loaded {len(docs)} documents, total of {sum([len(doc.page_content) for doc in docs])} characters"
    )

    with get_openai_callback() as cb:
        result = llm.run(
            file_context=context_string, issue_description=args.issue_description
        )

    print()
    print("Answer:")
    print(result)

    print()
    print("OpenAI stats:")
    print(cb)
