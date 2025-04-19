import asyncio
from agent.business_agent import BusinessAgent

async def test_agent():
    agent = BusinessAgent()
    
    # Test business advice
    print("Testing business advice...")
    try:
        response = await agent.get_business_advice("What are the first steps to start a restaurant in Washington?")
        print("\nResponse:", response)
    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    asyncio.run(test_agent()) 