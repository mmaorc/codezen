# CodeZen

## Description

CodeZen is a CLI utility that uses LLMs to help you debug and evolve your codebase based on your requests.

Usage examples:
```bash
codezen ask "Why am I getting <some exception message>?"
codezen ask "Write a README.md file for this project"
```

The differences from Github Copilot:
* This is a CLI tool, meaning it can be used regardless of your chosen IDE.
* This provides the LLM with the entire codebase, so it can do things that require a more holistic view of your project.

Current limitations:
* Only works for small codebases- currently it sends the entire codebase on each request (except the ignored files). 😆
* It can't change files autonomously, it only offers a solution.
* It uses gitignore file to know which files to ignore, so you must run this in a git repo and you can't currently ignore files that don't appear there.


## Installation
### Using PyPi
You can install the application using `pip` or `pipx`:
```bash
pip install --user codezen
```
or
```bash
pipx install codezen
```

### Compile from source

You can compile directly from source:
```bash
git clone https://github.com/mmaorc/codezen
cd codezen
poetry build
```


### Development
For development purposes, clone the repository, navigate to the project directory, and install it in a virtual environment:

```bash
git clone https://github.com/mmaorc/codezen
cd codezen
poetry install
poetry shell
```

## Usage

Before running the script, ensure that the `OPENAI_API_KEY` environment variable is set up correctly.

Run CodeZen with the following command:

```bash
codezen ask <issue_description>
```

`<issue_description>`: Describe the issue you are facing with your code

If you want to ignore additional files without adding them to your `.gitignore`, You can create a `.czignore` file at the project's root and add them there.


## Contributing

If you would like to contribute to this project, please feel free to fork the repository, create a feature branch, and submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
