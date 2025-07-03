Simple Business Data Agent
this is a little AI agent built with LangGraph that looks at some basic business numbers (sales, costs) and gives you a quick report

what it does
it takes todays and yesterdays business data and figures out :

if you made a profit or loss (basically pnl)

how much your sales and costs changed.

if your Customer Acquisition Cost (CAC) jumped up too high.

then it gives you some simple advice based on those numbers.

how to run it

install the stuff it needs :

pip install langgraph langchain-core

just run the script:

python business_agent.py

this will run with the sample data inside the file and print a report

run the tests (to make sure it's not broken) :

python -m unittest business_agent.py

u should see an "OK" at the end.

that's that