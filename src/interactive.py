import asyncio
from agent import WorkflowAgent

async def interactive_workflow():
    API_KEY = "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"
    agent = WorkflowAgent(api_key=API_KEY)
    
    while True:
        print("\n=== Tavily Research Workflow System ===")
        print("1. Add new research task")
        print("2. Process all tasks")
        print("3. Exit")
        
        choice = input("\nChoose an option (1-3): ")
        
        if choice == "1":
            query = input("Enter your research query: ")
            category = input("Enter category (press Enter for 'general'): ") or "general"
            try:
                importance = int(input("Enter importance (1-5, default 1): ") or "1")
            except ValueError:
                importance = 1
            
            agent.add_task(query, category, importance)
            print(f"Task added successfully! Queue size: {len(agent.task_queue)}")
            
        elif choice == "2":
            if not agent.task_queue:
                print("No tasks in queue!")
                continue
                
            print("\nProcessing tasks...")
            results = await agent.run_workflow()
            
            for i, result in enumerate(results, 1):
                print(f"\n--- Result {i} ---")
                print(f"Query: {result['query']}")
                print(f"Category: {result['category']}")
                if 'error' in result['result']:
                    print(f"Error: {result['result']['error']}")
                else:
                    print("Answer:", result['result'].get('answer', 'No direct answer available'))
                    print("\nTop Sources:")
                    for source in result['result'].get('results', [])[:3]:
                        print(f"- {source.get('title', 'N/A')}: {source.get('url', 'N/A')}")
                
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    asyncio.run(interactive_workflow())