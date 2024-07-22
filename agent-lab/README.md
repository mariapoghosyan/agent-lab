# Agents Lab

This lab will provide you with a gentle introduction to AI Agents.

If you're totally new to Agents and Generative AI applications in general, you might start with this brief [introduction](docs/agent-introduction.md).

In order to complete the lab, it is helpful to have:

- Basic knowledge of [Python](https://python.org), you don't need to be a python ninja, but it is encouraged to play with the examples provided.
- Elementary knowledge of how to use [Jupiter notebooks](https://jupyter.org/) (run cells, debug cells...)

<br>

## Running notebooks

In the `notebooks` folders there are 8 notebooks representing each step.
These notebooks are completed, meaning that you don't have to write any code, but it is warmly encouraged to tweak,
play and debug the code presented to better understand the steps you are following.

Depending on your environment setup, you can run the notebooks:
- [using Codespaces](../docs/environment-setup-codespaces.md) or 
- [using VSCode using a devcontainer](../docs/environment-setup-devcontainer.md)  or 
- [using Jupyter lab with a local virtualenv](../docs/environment-setup-local-virtualenv.md).

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

Utility
9. [Helper](notebooks/99-db_utility.ipynb): Contains database helper functionalities.
