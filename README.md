# CodeZen

## Description

CodeZen is your indispensable partner in programming. It is a CLI utility that uses LLMs to help you debug and evolve your codebase based on your requests.

The differences from Github Copilot:
* This is a CLI tool, meaning it can be used regardless of your chosen IDE.
* This provides the LLM with the entire codebase, so it can do things that require a more wholistic view of your project.

Current limitations:
* Only Work for small codebases- currently we send the entire codebase in each request. 😆
* It can't change files autonomously, it only offers a solution.
* It uses hard coded direcory names to know which files to ignore. Currently it only contains Python and Node.js common ignorable directories.


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
For development purposes, clone the repository, navigate to the project directory, and install in a virtual environment:

```bash
git clone https://github.com/mmaorc/codezen
cd codezen
poetry install
poetry shell
```

## Usage

Prior to running the script, ensure that the `OPENAI_API_KEY` environment variable is set up correctly.

Run CodeZen with the following command:

```bash
codezen <issue_description>
```

`<issue_description>`: Describe the issue you are facing with your code

Example:

```bash
codezen "Im getting the following error: ValueError: invalid literal for int() with base 10: a"
codezen "Write a readme.md file for this project"
```

## Contributing

If you would like to contribute to this project, please feel free to fork the repository, create a feature branch, and submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
