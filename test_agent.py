import asyncio
import json

# Simular el MCP client
class FakeMCP:
    async def call_tool(self, name, args):
        print(f"MCP llamado: {name}({args})")
        return json.dumps([
            {"mes": "2024-01", "total": 150000},
            {"mes": "2024-02", "total": 230000},
            {"mes": "2024-03", "total": 180000},
        ])

async def main():
    from backend.agent import Agent
    agent = Agent(FakeMCP())
    
    result = await agent.process_message("Dame el total de ventas por mes")
    print("\n=== RESULTADO FINAL ===")
    print(f"answer: {result['answer']}")
    print(f"sql: {result['sql']}")
    print(f"data: {result['data']}")

asyncio.run(main())