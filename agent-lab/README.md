# Agent Lab

This lab will provide you with a gentle introduction to AI Agents.

If you're totally new to Agents and Generative AI applications in general, you might start with this brief [introduction](docs/agent-introduction.md).

In order to complete the lab, it is helpful to have:

- Basic knowledge of [Python](https://python.org), you don't need to be a python ninja, but it is encouraged to play with the examples provided.
- Elementary knowledge of how to use [Jupyter notebooks](https://jupyter.org/) (run cells, debug cells...).

<br>

## Running notebooks

In the `notebooks` folder there are 8 notebooks representing each step of building the agent.
These notebooks are completed, meaning that you don't have to write any code, but it is warmly encouraged to tweak,
play and debug the code presented to better understand the steps you are following.

You have 2 options for environment setup and using the Notebooks. Please choose the one which suits you best:

1. [**Dev Container & Docker-compose**](./docs/environment-setup-devcontainer.md) (recommended option)

2. [**Poetry & python**](./docs/environment-setup-local-virtualenv) - for developers comfortable with the command line, pyenv and poetry. If you're on Windows, you must have & use WSL.

<br>

## Start the lab

  Please read [this guide](docs/understanding-the-use-case.md) to better understand the goal of this lab, how it organized and how to get the best out of it.

### The lab steps  

1. [Introduction](notebooks/01_intro.ipynb): Provides an introduction to the lab.
2. [Schedule](notebooks/02_get_schedule.ipynb): First implementation of the `opening schedule` feature.  
3. [The schedule tool](notebooks/03_get_schedule_tool.ipynb): Implementation of the `opening schedule` feature using a tool.
4. [The menu tool](notebooks/04_get_menu_tool.ipynb): Implementation of the `daily menu` tool.
5. [The current date tool](notebooks/05_get_current_date_tool.ipynb): Implementation of the `get current datetime` tool.
6. [LangChain refactor](notebooks/06_use_langchain.ipynb): Refactor of the code with LangChain.
7. [The order tool](notebooks/07_order_tool.ipynb): Implementation of the `order`tool.
8. [Final](notebooks/08_final.ipynb): Implementation of the `get_orders`and `cancel_orders` tools.
9. [Rice Up! agent](./notebooks/09_riceup_agent.ipynb): Exercise to implement a new agent for the *Rice Up!* restaurant.
10. [Utility helper](notebooks/99-db_utility.ipynb): Contains database helper functionalities.
