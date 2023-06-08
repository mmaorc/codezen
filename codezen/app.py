import logging
from pathlib import Path
from typing import Annotated, List

import typer
from binaryornot.check import is_binary
from langchain import LLMChain, PromptTemplate
from langchain.callbacks import get_openai_callback
from langchain.chat_models import ChatOpenAI
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from codezen.ignore_files import (
    filter_files,
    get_filepaths_not_gitignored,
    load_ignore_file,
)


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


def load_files_to_langchain_documents(
    root_dir: Path, project_files_paths: list[Path]
) -> List[Document]:
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


def build_context_string_from_docs(docs: List[Document]) -> str:
    all_context = []
    for doc in docs:
        current_file = f"""Relative file path: {doc.metadata["source"]}\nFile content:\n{doc.page_content}\n---\n"""
        all_context.append(current_file)
    all_context_string = "\n".join(all_context)
    return all_context_string


def get_relevant_filepaths(root_dirpath: Path, czignore_filepath: Path) -> List[Path]:
    project_files_paths = get_filepaths_not_gitignored(root_dirpath)
    czignore_patterns = load_ignore_file(czignore_filepath)
    project_files_paths = (
        filter_files(project_files_paths, czignore_patterns)
        if czignore_patterns
        else project_files_paths
    )
    return project_files_paths


def create_model(model_name: str) -> ChatOpenAI:
    return ChatOpenAI(model_name=model_name)


def build_context_string(root_dirpath: Path, relevant_filepaths: List[Path]) -> str:
    docs = load_files_to_langchain_documents(root_dirpath, relevant_filepaths)
    logging.info(
        f"Loaded {len(docs)} documents, total of {sum([len(doc.page_content) for doc in docs])} characters"
    )
    context_string = build_context_string_from_docs(docs)
    return context_string


app = typer.Typer(add_completion=False)


@app.command(
    name="list-files", help="Show the files that will be included in the prompt context"
)
def list_files(
    model_name: Annotated[
        str,
        typer.Option("-m", "--model", help="The model name to use for the LLMChain"),
    ] = "gpt-4",
    root_dir: Annotated[
        str, typer.Option("-d", "--root-dir", help="The root directory of the project")
    ] = "./",
    czignore_file: Annotated[
        str, typer.Option("--czignore-file", help="The path to the .czignore file")
    ] = "./.czignore",
):
    relevant_filepaths = get_relevant_filepaths(
        root_dirpath=Path(root_dir), czignore_filepath=Path(czignore_file)
    )

    # Calculate total number of tokens
    model = create_model(model_name=model_name)
    context_string = build_context_string(Path(root_dir), relevant_filepaths)
    token_count = model.get_num_tokens(context_string)

    print("Total number of request tokens:")
    print(token_count)
    print()

    print("Included files:")
    print("\n".join([str(p) for p in relevant_filepaths]))


@app.command(help="Ask the LLM a question or make a request")
def ask(
    issue_description: Annotated[str, typer.Argument(help="The issue description")],
    verbose: Annotated[
        bool, typer.Option("-v", "--verbose", help="Enable verbose logging")
    ] = False,
    model_name: Annotated[
        str,
        typer.Option("-m", "--model", help="The model name to use for the LLMChain"),
    ] = "gpt-4",
    root_dir: Annotated[
        str, typer.Option("-d", "--root-dir", help="The root directory of the project")
    ] = "./",
    czignore_file: Annotated[
        str, typer.Option("--czignore-file", help="The path to the .czignore file")
    ] = "./.czignore",
):
    # Set logging level
    logging.basicConfig(level=logging.WARNING)
    if verbose:
        logging.basicConfig(level=logging.INFO)

    model = create_model(model_name=model_name)
    llm = LLMChain(llm=model, prompt=prompt_template)

    relevant_filepaths = get_relevant_filepaths(
        root_dirpath=Path(root_dir), czignore_filepath=Path(czignore_file)
    )

    context_string = build_context_string(Path(root_dir), relevant_filepaths)

    with get_openai_callback() as cb:
        result = llm.run(
            file_context=context_string, issue_description=issue_description
        )

    print()
    print("Answer:")
    print(result)

    print()
    print("OpenAI stats:")
    print(cb)
