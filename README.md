# AgentForge Generative AI Project

This project demonstrates the use of AgentForge, a low-code framework for building AI-powered autonomous agents and cognitive architectures, tailored for industry use cases.

## Installation

1. Ensure you have Python 3.8+ installed.
2. Clone or download this repository.
3. Create a virtual environment: `python -m venv .venv`
4. Activate the virtual environment: `.venv\Scripts\activate` (Windows)
5. Install dependencies: `pip install -r requirements.txt`

## Configuration

1. Edit `settings/settings.yaml` to add your API keys for the LLMs you want to use (OpenAI, Anthropic, Google).
2. Customize personas in `personas/`, agents in `agents/`, and cogs in `cogs/` as needed.

## Usage

Run the example: `python main.py`

This will execute the example cog, which runs the example agent to answer a question.

## Project Structure

- `agents/`: YAML files defining agents
- `cogs/`: YAML files defining multi-agent workflows
- `personas/`: YAML files defining agent personalities
- `settings/`: Configuration files
- `storage/`: ChromaDB storage for memory
- `main.py`: Entry point script
- `requirements.txt`: Python dependencies

## Documentation

For more information, visit the [AgentForge documentation](https://pypi.org/project/agentforge/docs/).