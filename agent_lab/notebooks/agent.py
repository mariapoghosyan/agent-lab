#region This cell contains most of the code you saw in the preceeding notebook. You can just run this cell and skip to the next one.

import os
import asyncio
import pytz
import json
from dotenv import load_dotenv

# Imports
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langchain.pydantic_v1 import BaseModel, Field
from langchain.memory import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from datetime import datetime
from services.data_provider import DataProvider
from services.data_types import Order, OrderResponse
from termcolor import cprint
from langchain.agents import AgentExecutor, create_openai_functions_agent
from typing import Optional

# Environment setup
load_dotenv()

api_key=os.environ['AZURE_OPENAI_API_KEY']
endpoint=os.environ['AZURE_OPENAI_ENDPOINT']
deployment=os.environ['AZURE_OPENAI_DEPLOYMENT']
api_version=os.environ['AZURE_OPENAI_API_VERSION']
local_timezone = os.environ['TIMEZONE']

llm=AzureChatOpenAI(api_key=api_key, 
                    azure_endpoint=endpoint,
                    azure_deployment=deployment,
                    api_version=api_version, 
                    temperature=0.3)

# This the data access layer
db:DataProvider=DataProvider()


# Define the input schema for the schedule-tool
class ScheduleToolInputSchema(BaseModel):
    date: str = Field(description="The date for which you want to know the schedule in format 'DD/MM/YYYY HH:MM' (e.g. '31/12/2023 15:00').")
    user_id: Optional[str] = Field(description="The optional user id in form '#<4-digits-number>'.")
    
# Define the input schema for daily menu tool
class DailyMenuInputSchema(BaseModel):
    date: str = Field(description="The date for which you want to know the available menu in format 'DD/MM/YYYY HH:MM' (e.g. '29/05/2024 17:00').")  
    
# Define the input schema for the order tool
class OrderToolInputSchema(BaseModel):
    date: str = Field(description="The date and time for which you want the order to be delivered in format 'DD/MM/YYYY HH:MM' (e.g. '18/05/2024 11:23')")
    user_id: str = Field(description="The user id in form '#<4-digits-number>'.")    
    credit_card_digits: str = Field(description="The last 4 digits of the credit card number in form '####'.")
    order_detail: str = Field(description="""The order information using the following JSON format:
                            [                                
                                {
                                    "kind": "<kind of food>", # example: "pasta,pizza,drink",
                                    "name": "<name of the food>", # example: "lasagna","coke"
                                    "quantity": <number of dishes> #  example: 2    
                                    "extras": ["<extra1>", "<extra2>", ...] # example: ["double cheese", "well cooked", "no ice"])
                                },
                                <next food>
                            ]
                            """)
    order_id: Optional[str] = Field(description="The id of the open order in form '<4-digits-number>'")
   
# Returns the operative schedule for the provided date and the optional user id
@tool("schedule-tool", args_schema=ScheduleToolInputSchema)
def operative_schedule(date:str, user_id:str=None):
    """Useful when you need to know the operative schedule on a specific date and time."""
    weekday= datetime.strptime(date, "%d/%m/%Y %H:%M").strftime("%A")    
    
    # Check if the user is a special client
    is_special = db.is_special_client(user_id)
    # Get the operative schedule from the database
    schedule=db.get_rice_up_schedule(day=weekday, is_special=is_special) 
    # Check if the requested date/time comes within the working schedule       
    if schedule.status == "open":        
        time= datetime.strptime(date, "%d/%m/%Y %H:%M").time()
        opening = datetime.strptime(schedule.start, "%H:%M").time()
        closing = datetime.strptime(schedule.end, "%H:%M").time()        
        if time < opening or time > closing:
            schedule.status = "closed"            
        
    return schedule

# Returns the menu for the provided date
@tool("daily-menu-tool", args_schema=DailyMenuInputSchema)
def get_rice_up_menu(date:str):
    """Useful when you need to know the menu for a specific date."""
    target_date= datetime.strptime(date, "%d/%m/%Y %H:%M") 
    weekday= target_date.strftime("%A")
    
    # Get the menu from the database
    return db.get_rice_up_menu(day=weekday)

# Function to get the current date and time in the format dd/mm/yyyy hh:mm
@tool("current-datetime-tool")
def get_current_datetime():
    """Useful when you need to know the current date and time for date and time based operations."""        
    local_tz = pytz.timezone(local_timezone)
    return {
        "current_datetime": datetime.now(local_tz).strftime("%A, %d/%m/%Y %H:%M")
    }

@tool("order-tool", args_schema=OrderToolInputSchema)
def order(date:str, user_id:str, order_detail: str, credit_card_digits:int,order_id:str=None,):
    """Useful when you need to place or update and order for a specific date and time"""
    
    weekday=datetime.strptime(date, "%d/%m/%Y %H:%M").strftime("%A")
    total_price=0 
    
       
    response=OrderResponse()    
    
    # Check if the user id is valid, if not, return the info to the LLM
    user=db.get_rice_up_customer(user_id)
    if user is None:
        response.messages.append(f"Sorry, I could not find any user with the user id: {user_id}. Please provide the id of a registered user.")
        response.status="failed"
        return response
    
    # Check if the provided card digits match the ones registered for the user
    if user.card_digits != credit_card_digits:
        response.messages.append(f"Sorry, the last 4 digits of the card provided do not match the ones registered for user {user_id}. Please provide the correct digits.")
        response.status="failed"
        return response  
        
    # Get available dishes for the selected date  
    available_dishes=db.get_rice_up_dishes(day=weekday)
    
    # Check if ordered dishes are present in the menu for the desired date
    detail=json.loads(order_detail)
    for detail in detail:
        dish_name=detail["name"]
        dish=available_dishes.get(dish_name.lower())
        if dish is None:
            response.messages.append(f"Sorry, {detail['name']} is not available in our menu for desired date.")
            response.status="failed"
        else:
            # Dish is fine, add price to the total price of the order 
            total_price+=dish.price*detail["quantity"]
    
    # If dish validation failed, return the response to the LLM        
    if response.status=="failed":
            return response
        
    # Validation passed, saves/updates the order into database.    
    order=Order(user_id=user_id, date=date, total=total_price, detail=order_detail, status="pending")
    order_id=db.upsert_order(order_id=order_id, order=order)
    
    # Return the order status for further processing by the LLM
    response.order_id=order_id
    response.user_name=user.first_name
    response.total_price=total_price
    response.card_digits=user.card_digits
        
    return response
    
# We create an array containing the tools that will be used by the agent
tools=[operative_schedule, get_rice_up_menu, get_current_datetime, order]

# Short term memory for the agent
session_id="0000"
memory = ChatMessageHistory(session_id=session_id)
#endregion

# Check that provided user id and card digits match the ones registered in the database
def check_autorization(user_id:str, card_digits:int)-> OrderResponse:
    response=OrderResponse()    
    
    # Check if the user id is valid, if not, return the info to the LLM
    user=db.get_rice_up_customer(user_id)
    if user is None:
        response.messages.append(f"Sorry, I could not find any user with the user id: {user_id}. Please provide the id of a registered user.")
        response.status="failed"
        return response
    
    # Check if the provided card digits match the ones registered for the user
    if user.card_digits != card_digits:
        response.messages.append(f"Sorry, the last 4 digits of the card provided do not match the ones registered for user {user_id}. Please provide the correct digits.")        
    
    return response

# Updated system message, notice the presence of new constraints and the new tasks

system_message = f'''
Role: An assistant with expertise in handling questions about operative schedule, available menu and order management of a food delivery service.
 
Instructions:
- Provide information about the available menu, opening schedule and placing, cancelling and equiry about orders.
- Kindly deny any request not regarding opening schedule, menu or food order management.
- Always assume the date and time returned by the get_current_datetime tool as the reference date for all date calculations.
- If a date is not indicated use the reference date.
- If a time is not indicated assume it is 12 PM.
- Assume the following format: 'DD/MM/YYYY HH:MM' as the standard format for dates.

Steps:
  - Opening Schedule:
      1. Always use the calculated date based on reference date to check and return the opening schedule.
      2. Always indicate the desired data and time including weekday in the response.
      
  - Available menu:
      1. When the user asks for the a menu you should respond using the following template enclosed in triple quotes:

      ```
      Menu for <day-name> <requested date>
      
      Soup
      
      1. <name> - <price> - <ingredients> - <label>
      2. <name> - <price> - <ingredients> - <label>
   
      Bowl
      
      1. <name> - <price> - <ingredients> - <label>
      2. <name> - <price> - <ingredients> - <label>
      ```  
      
      2. If the request is about specific menu entries (e.g. 'do you have pasta', 'do you offer vegetarian food' or 'are there any specials?' ), together with the menu kindle answer the question.     
      3. If no specials are available for the day, do not include that section into menu.
      4. If no menu is available, kindly reply that there you can serve any food for that day..
      5. If the request relates to an item that is not available in the menu, kindly reply that it cannot be ordered.      
  
  - Order Placement:    
      1. The user id is mandatory for placing an order. If the user id is available, kindly ask the user to provide it.
      2. The user must indicate when it wants to place the order. If the user does not provide a date and time, kindly ask the user to provide it.
      3. The ordering date must fall within the opening schedule. If the user tries to place an order outside the opening schedule, kindly inform the user that the service is closed at that time.
      4. The user must provide its the last 4 digits of registered credit card. If the user does not provide it, kindly ask the user to provide it, otherwise the order cannot be placed.
      5. When order is successfully placed, respond with the following message enclosed in triple quotes:
      
      ```
      Thank you for your order <first-name> <user_id>. 
            
      Your order <order-id> will be delivered on <date> at <time>.
      We will charge your credit card ending in <last-4-digits> for the amount of <total-amount>.      
      
      Your order details:
      <quantity>x <name> - <price>
      
      <thank the user depending if it is a new order or an update> <firstname> <lastname> <user_id>.
      ```
      
  - Order retrieval:
      1. If the user asks for the status of an order, kindly provide the status of the order in the following format:      
      ```
      <order-id> - <date> - <time> - <total-amount>
      <order details>
      ...
      <other orders>
      ```
      
      2. If the user asks for the status of a specific order id that does not exist, kindly inform the user that the order does not exist.
      3. Return the order details in the same format as the order placement.
      
  - Order cancellation:
      1. The request of canceling an order must include the order id. If the order id is not provided, kindly ask the user to provide it.
      2. If cancel request succeeds, kindly inform the user that the order has been canceled.
      3. If cancel request fails because an order does not exist, kindly inform the user that the order does not exist.
  
Expectation:
  - Provide a seamless experience to the user, by providing the requested information in a kind and timely manner, including all the necessary details and guiding the user to a possible follow up step.

Narrowing:  
  1. The user can only order food that is available in the menu. Any other request should be kindly denied.
  2. Deny all the requests referring to a date antecedent the reference date.
'''

# Define the input schema for the order retrieval tool
class OrderRetrievalToolInputSchema(BaseModel):    
    user_id: str = Field(description="The user id in form '#<4-digits-number>'")    
    credit_card_digits: str = Field(description="The last 4 digits of the credit card number in form '####'.")
    order_id: Optional[str] = Field(description="The id of the open order to cancel in form '####'")
    
class OrderCancellationToolInputSchema(BaseModel):    
    user_id: str = Field(description="The user id in form '#<4-digits-number>'.")    
    credit_card_digits: str = Field(description="The last 4 digits of the credit card number in form '####'")
    order_id: str = Field(description="The id of the open order to cancel in form '####'")
    
@tool("order-retrieval-tool", args_schema=OrderRetrievalToolInputSchema)
def order_retrieval(user_id:str, credit_card_digits:int, order_id:str=None):
    """Useful when you need to retrieve the list of pending orders or a specific order of a user."""
    
    # Check if the user id is authorized to retrieve the orders   
    response=check_autorization(user_id, credit_card_digits)
    if response.status=="failed":
        return response
    if order_id is None:
        return db.get_orders(user_id=user_id, status="pending")
    else:  
        return db.get_order(user_id=user_id, order_id=order_id, status="pending")   

@tool("order-cancellation-tool", args_schema=OrderCancellationToolInputSchema)
def order_cancellation(user_id:str, credit_card_digits:int, order_id:str):
    """Useful when you need to cancel a specific pending order."""
    
    # Check if the user id is authorized to cancel the order     
    response=check_autorization(user_id, credit_card_digits)
    if response.status=="failed":
        return response
        
    # Delete the specified order by marking it as deleted in the database
    return db.cancel_order(user_id=user_id, order_id=order_id)

# We add the new tools to the list of tools available to the agent
tools.append(order_retrieval)
tools.append(order_cancellation)

def run_agent(user_request:str):
    prompt = ChatPromptTemplate.from_messages(
    [
        ("system",system_message),  
        MessagesPlaceholder(variable_name="chat_history"),      # This is the chat history
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),  # This holds the agent interation messages
    ])

    # Create the agent
    agent = create_openai_functions_agent(llm, tools, prompt)
    # Create the runtime in charge of executing the agent (then one in charge of calling the tools, adding the returned data into message hsitory, call the llm again, etc.)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    agent_with_chat_history = RunnableWithMessageHistory(
        agent_executor,
        lambda session_id: memory,
        input_messages_key="input",
        history_messages_key="chat_history")
    
    # Execute the agent
    response= agent_with_chat_history.invoke({"input": user_request},config={"configurable": {"session_id": session_id}})
    return response["output"]

whatever = ...

async def function(param) -> asyncio.coroutines:
    # Chat with the agent until the user types an empty message
    while True:
        user_message = input("Enter your message: ",)
        if user_message == '':
            break
        cprint(f"User: {user_message}","blue")
        try:
            result = run_agent(user_message)
            cprint(f"Agent: {result}", "yellow")
            await asyncio.sleep(0.5)
        except Exception as e:
            cprint(f"An error occurred: {str(e)}", "red")

asyncio.run(function(whatever))