# PROMPTS.md

This file contains all prompts used in the development of this stock market prediction tool. Each prompt should be appended to this file as the project evolves.

## Initial Project Setup Prompt

**Date**: 2025-07-05  
**Context**: Project initialization and architecture planning

**Prompt**:
We're creating a stock market prediction tool. Create an assets directory to hold permanent data that we will want to keep track of. Otherwise create services in this project using docker-compose. Create a postgres docker with pgvector installed, which will support RAG in the future. When creating services, to the maximum extend possible, use the Python Mode Context Protocol in mind. We will use uv as the package manager for this project. Python should be executed using the "uv run" command. To start, we require data on every company in the S&P 500. Research the web on these companies and create basic company information for each in a .json file in assets. We are particularly interested on financial data for the companies, information published by the companies before earnings reports, analysts views of the companies and target prices, and the historical performance of these analysts. We are interested in some very specific data on each company, such as dates for earnings reports, ex-dividend dates, dividends paid out, insider trading on the companies, performance of the company relative to their sector, and any historical predictors on how the company's stock performs the very next day after reporting earnings. We will do our own sentiment analysis on published data and reports and look to use this analysis to predict stock performance the day after earning reports are issued. Think deeply about how to implement this project. Enter research-mode. Update CLAUDE.md here. We will need services that pull data from external services, so include in your analysis tools (such as Tavily search with mcp-tavily) and token limits (using free tiers) to do this. Give high preference to existing mcp-tools that can be integrated for and tool or service that this project might need. Do not write any code until you have completed this plan. Save this prompt to a PROMPTS.md file. Write in CLAUDE.md that we should append every prompt written here to the PROMPTS.md file. I'm counting on you.

---

## Web Application and Ollama Integration Update

**Date**: 2025-07-05  
**Context**: Adding web application interface and local AI agent capabilities

**Prompt**:
Update this plan to include a locally hosted web application to help the user view the results, display upcoming earning reports dates, historical performance of the stock after these dates, and whether to stock hit or missed expected earnings targets. We also need to be running ollama locally (or dockerized) in order to have agents which will support further workflows.

---

*Note: All subsequent prompts should be appended below this section with date and context.*