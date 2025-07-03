import unittest
import json
from typing import TypedDict, Dict, Any

from langchain_core.messages import BaseMessage #unused idk
from langgraph.graph import StateGraph, END

#this is like the main memory for the graph, it holds all our data as it moves around.

class AgentState(TypedDict):
    input_data: Dict[str, Any] # the raw data we get
    metrics: Dict[str, float] # the numbers we calculate
    report: Dict[str, Any] #final report with advice


#(real workers here) each node is just a function. it gets the state, does a job, and returns what it changed.

def calclate_metrics_node(state: AgentState) -> Dict[str, Any]:
    """this one does the math i guess"""
    print("---EXECUTING NODE: calculate_metrics_node---")
    input_data = state['input_data']
    today = input_data['today']
    previous_day = input_data['previous_day']

    # ok lets do the math
    profit = today['sales'] - today['costs']

    # calc the % change, gotta watch out for dividing by zero lol
    revenue_change_pct = ((today['sales'] - previous_day['sales']) / previous_day['sales']) * 100 if previous_day['sales'] != 0 else 0
    cost_change_pct = ((today['costs'] - previous_day['costs']) / previous_day['costs']) * 100 if previous_day['costs'] != 0 else 0

    # now for CAC
    cac_today = today['costs'] / today['customers'] if today['customers'] != 0 else float('inf')
    cac_previous = previous_day['costs'] / previous_day['customers'] if previous_day['customers'] != 0 else float('inf')
    
    cac_increase_pct = 0
    if cac_previous != 0 and cac_previous != float('inf'):
        cac_increase_pct = ((cac_today - cac_previous) / cac_previous) * 100
    
    metrics = {
        "profit": profit,
        "revenue_change_pct": revenue_change_pct,
        "cost_change_pct": cost_change_pct,
        "cac_today": cac_today,
        "cac_increase_pct": cac_increase_pct
    }
    
    print(f"Calculated Metrics: {json.dumps(metrics, indent=2)}")
    
    # send back the metrics to update the state
    return {"metrics": metrics}


def generate_recommendations_node(state: AgentState) -> Dict[str, Any]:
    """this node gives the advice. the "recommendation" node"""
    print("---EXECUTING NODE: generate_recommendations_node---")
    metrics = state['metrics']
    
    recommendations = []
    alerts = []
    
    # heres the logic for the advice
    
    # is it making money?
    if metrics['profit'] < 0:
        profit_status = "Loss"
        recommendations.append("Reduce costs: The business is currently operating at a loss.")
    else:
        profit_status = "Profitable"

    #hows the CAC doing?
    if metrics['cac_increase_pct'] > 20:
        alert_message = f"High CAC Alert: Customer Acquisition Cost increased by {metrics['cac_increase_pct']:.2f}%."
        alerts.append(alert_message)
        recommendations.append("Review marketing campaigns: CAC has increased significantly. Analyze channel performance and ad spend efficiency.")

    #checkin on sales growth
    if metrics['revenue_change_pct'] > 5: # >5% is good growth i guess
        recommendations.append(f"Consider increasing advertising budget: Sales are growing ({metrics['revenue_change_pct']:.2f}% increase), capitalize on this momentum.")
    elif metrics['revenue_change_pct'] < -5:
        recommendations.append("Investigate sales drop: Revenue has decreased significantly. Analyze market factors and customer feedback.")

    # if nothing bad happened, just log that everything is aight
    if not recommendations:
        recommendations.append("Business metrics are stable. Continue monitoring performance.")

    report = {
        "profit_status": profit_status,
        "daily_profit": f"${metrics['profit']:.2f}",
        "alerts": alerts,
        "recommendations": recommendations,
        "key_metrics": {
            "revenue_change": f"{metrics['revenue_change_pct']:.2f}%",
            "cost_change": f"{metrics['cost_change_pct']:.2f}%",
            "cac_today": f"${metrics['cac_today']:.2f}",
            "cac_increase": f"{metrics['cac_increase_pct']:.2f}%"
        }
    }
    
    print(f"Generated Report: {json.dumps(report, indent=2)}")

    return {"report": report}

# make the graph and tell it to use our AgentState
workflow = StateGraph(AgentState)

# add our functions as nodes
workflow.add_node("calculator", calclate_metrics_node)
workflow.add_node("recommender", generate_recommendations_node)

#now connect the dots
#just a simple flow: calculator -> recommender
workflow.set_entry_point("calculator")
workflow.add_edge("calculator", "recommender")
workflow.add_edge("recommender", END) # and we're done

#compile it all into a runnable app
app = workflow.compile()


#some sample data to test with, this one should show a loss
sample_input_data = {
    "today": {
        "sales": 1500,
        "costs": 1800,
        "customers": 50
    },
    "previous_day": {
        "sales": 1600,
        "costs": 1200,
        "customers": 60
    }
}

#this part only runs when i gota'python business_agent.py'
if __name__ == "__main__":
    print("---STARTING AGENT RUN--")
    #gotta wrap the input data in a dictionary that matches the state
    initial_state = {"input_data": sample_input_data}
    final_state = app.invoke(initial_state)

    print("\n---AGENT RUN COMPLETE---")
    print("\nFinal Report:")
    print(json.dumps(final_state['report'], indent=4))


class TestBusinessAgent(unittest.TestCase):

    def test_high_cac_and_loss_scenario(self):
        print("\n---RUNNING UNIT TEST---")
        
        #test data
        test_data = {
            "today": {
                "sales": 2000,
                "costs": 2200,  # more costs = loss
                "customers": 40   # less customers = higher CAC
            },
            "previous_day": {
                "sales": 2100,
                "costs": 1500,
                "customers": 50
            }
        }
        
        #run the agent
        initial_test_state = {"input_data": test_data}
        result = app.invoke(initial_test_state)
        report = result['report']
        
        #check if the output is what i expect or na
        
        #check the p
        self.assertEqual(report['profit_status'], 'Loss')
        self.assertEqual(report['daily_profit'], '$-200.00')
        
        #check for the CAC alert
        self.assertEqual(len(report['alerts']), 1)
        self.assertIn("High CAC Alert", report['alerts'][0])
        self.assertIn("83.33%", report['alerts'][0])
        
        #check the advice it gives
        self.assertEqual(len(report['recommendations']), 2) 
        self.assertIn("Reduce costs: The business is currently operating at a loss.", report['recommendations'])
        self.assertIn("Review marketing campaigns: CAC has increased significantly. Analyze channel performance and ad spend efficiency.", report['recommendations'])
        print("---UNIT TEST PASSED---")
