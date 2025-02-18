from typing import Dict, List, Optional
from dataclasses import dataclass
from tavily import TavilyClient
import asyncio
from datetime import datetime
import json
import aiohttp
import time
from functools import wraps
from dotenv import load_dotenv
import os

def rate_limit(calls: int, period: float):
    """Rate limiting decorator"""
    def decorator(func):
        last_reset = time.time()
        calls_made = 0

        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal last_reset, calls_made
            
            current = time.time()
            if current - last_reset >= period:
                calls_made = 0
                last_reset = current
            
            if calls_made >= calls:
                wait_time = period - (current - last_reset)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    last_reset = time.time()
                    calls_made = 0
            
            calls_made += 1
            return await func(*args, **kwargs)
        return wrapper
    return decorator

class ResearchError(Exception):
    """Custom exception for research-related errors"""
    pass

class ReasoningError(Exception):
    """Custom exception for reasoning-related errors"""
    pass

@dataclass
class ResearchTask:
    query: str
    category: str
    importance: int
    created_at: datetime
    status: str = "pending"
    error: Optional[str] = None
    research_results: Optional[dict] = None
    reasoning_analysis: Optional[str] = None

class WorkflowAgent:
    def __init__(self, api_key: str, max_retries: int = 3):
        self.client = TavilyClient(api_key=api_key)
        self.task_queue: List[ResearchTask] = []
        self.results_cache: Dict[str, dict] = {}
        self.max_retries = max_retries
        
    def add_task(self, query: str, category: str, importance: int) -> None:
        """Add a new task to the queue"""
        task = ResearchTask(
            query=query,
            category=category,
            importance=importance,
            created_at=datetime.now()
        )
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda x: (-x.importance, x.created_at))

    def get_queue_status(self) -> List[dict]:
        """Get the current status of all tasks in the queue"""
        return [{
            'query': task.query,
            'category': task.category,
            'importance': task.importance,
            'created_at': task.created_at.isoformat(),
            'status': task.status,
            'error': task.error,
            'research_results': task.research_results,
            'reasoning_analysis': task.reasoning_analysis
        } for task in self.task_queue]

    @rate_limit(calls=5, period=60)
    async def _research_query(self, query: str) -> dict:
        """Perform research on a query using Tavily API"""
        try:
            # TavilyClient.search is not async, so run it in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.client.search(
                    query=query,
                    search_depth="advanced",
                    include_answer=True,
                    max_results=5
                )
            )
            
            if not response or not isinstance(response, dict):
                raise ResearchError("Invalid response from Tavily API")
                
            if 'error' in response:
                raise ResearchError(f"Tavily API error: {response['error']}")
                
            return response
            
        except Exception as e:
            raise ResearchError(f"Research failed: {str(e)}")

    def _get_category_insights(self, category: str, research_results: dict) -> str:
        """Generate category-specific insights from research results"""
        if not research_results or not research_results.get('results'):
            return ""
            
        insights = ""
        answer = research_results.get('answer', '')
        results = research_results.get('results', [])
        all_content = answer + ' ' + ' '.join(r.get('content', '') for r in results)
        
        if category.lower() == 'technology':
            # Look for emerging trends, technical details, and future implications
            if any(word in all_content.lower() for word in ['future', 'emerging', 'trend', 'advancement', 'innovation']):
                insights += "• Future Trends: This topic shows significant potential for future developments\n"
            if any(word in all_content.lower() for word in ['challenge', 'limitation', 'problem', 'issue']):
                insights += "• Technical Challenges: There are notable technical challenges to consider\n"
            if any(word in all_content.lower() for word in ['impact', 'effect', 'influence', 'change']):
                insights += "• Societal Impact: This technology may have significant societal implications\n"
                
        elif category.lower() == 'science':
            # Focus on methodology, evidence, and scientific implications
            if any(word in all_content.lower() for word in ['experiment', 'study', 'research', 'evidence']):
                insights += "• Research Focus: Strong experimental/research foundation\n"
            if any(word in all_content.lower() for word in ['theory', 'hypothesis', 'model']):
                insights += "• Theoretical Framework: Well-established theoretical background\n"
            if any(word in all_content.lower() for word in ['discovery', 'breakthrough', 'finding']):
                insights += "• Scientific Impact: Notable scientific achievements identified\n"
                
        elif category.lower() == 'business':
            # Analyze market trends, strategies, and business implications
            if any(word in all_content.lower() for word in ['market', 'industry', 'sector']):
                insights += "• Market Analysis: Significant market/industry factors identified\n"
            if any(word in all_content.lower() for word in ['strategy', 'plan', 'approach']):
                insights += "• Strategic Insights: Clear strategic implications present\n"
            if any(word in all_content.lower() for word in ['opportunity', 'growth', 'potential']):
                insights += "• Growth Potential: Business opportunities highlighted\n"
                
        elif category.lower() == 'health':
            # Focus on medical implications, research, and health impacts
            if any(word in all_content.lower() for word in ['study', 'research', 'trial']):
                insights += "• Medical Research: Based on clinical/medical studies\n"
            if any(word in all_content.lower() for word in ['treatment', 'therapy', 'intervention']):
                insights += "• Treatment Options: Therapeutic approaches discussed\n"
            if any(word in all_content.lower() for word in ['prevention', 'risk', 'safety']):
                insights += "• Health Implications: Important health considerations noted\n"
        
        return insights

    def _calculate_source_credibility(self, url: str) -> float:
        """Calculate credibility score for a source"""
        credibility_score = 1.0
        
        # Academic and educational domains get higher scores
        if any(domain in url.lower() for domain in ['.edu', 'academic', 'research', 'science']):
            credibility_score *= 1.3
        
        # Established reference sites
        if any(domain in url.lower() for domain in ['wikipedia.org', 'britannica.com', 'nature.com', 'science.org']):
            credibility_score *= 1.2
            
        # Government sources
        if '.gov' in url.lower():
            credibility_score *= 1.25
            
        # Recent or archived content
        if 'archive.org' in url.lower():
            credibility_score *= 0.9  # Slightly lower score for archived content
            
        return min(credibility_score, 2.0)  # Cap at 2.0

    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        # Simple keyword extraction based on frequency and importance
        words = text.lower().split()
        # Remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if word not in common_words and len(word) > 3]
        
        # Count frequency
        from collections import Counter
        keyword_freq = Counter(keywords)
        
        # Return top concepts
        return [word for word, _ in keyword_freq.most_common(5)]

    async def _analyze_results(self, research_results: dict) -> str:
        """Analyze research results and generate insights"""
        try:
            if not research_results:
                return "No results available"
                
            answer = research_results.get('answer', 'No direct answer available')
            results = research_results.get('results', [])
            
            # Extract key concepts
            all_text = answer + ' ' + ' '.join(r.get('content', '') for r in results)
            key_concepts = self._extract_key_concepts(all_text)
            
            # Calculate source credibility
            credible_sources = []
            for result in results:
                url = result.get('url', '')
                credibility = self._calculate_source_credibility(url)
                if credibility > 1.0:
                    credible_sources.append({
                        'title': result.get('title', ''),
                        'url': url,
                        'credibility': credibility
                    })
            
            # Generate potential follow-up questions
            follow_ups = [
                f"How does {concept} relate to other concepts in this field?"
                for concept in key_concepts[:2]
            ]
            follow_ups.extend([
                "What are the practical applications of this knowledge?",
                "What are the latest developments in this area?",
                "What are the main challenges or controversies in this field?"
            ])
            
            # Build enhanced analysis
            analysis = "Research Analysis:\n\n"
            analysis += f"Main Answer: {answer}\n\n"
            
            if key_concepts:
                analysis += "Key Concepts:\n"
                for concept in key_concepts:
                    analysis += f"• {concept}\n"
                analysis += "\n"
            
            if credible_sources:
                analysis += "Most Credible Sources:\n"
                for source in sorted(credible_sources, key=lambda x: x['credibility'], reverse=True)[:3]:
                    analysis += f"• {source['title']} (Credibility: {source['credibility']:.1f})\n"
                analysis += "\n"
            
            analysis += "Suggested Follow-up Questions:\n"
            for question in follow_ups:
                analysis += f"• {question}\n"
            
            return analysis
            
        except Exception as e:
            raise ReasoningError(f"Analysis failed: {str(e)}")

    async def process_task(self, task: ResearchTask) -> dict:
        """Process a single task"""
        task.status = "processing"
        print(f"Processing task: {task.query}")
        
        try:
            # Determine search depth based on importance
            search_depth = "advanced" if task.importance >= 3 else "basic"
            
            # Check cache first
            cache_key = f"{task.query}_{search_depth}"
            if cache_key in self.results_cache:
                print(f"Using cached results for: {task.query}")
                research_results = self.results_cache[cache_key]
            else:
                print(f"Fetching new results for: {task.query}")
                research_results = await self._research_query(task.query)
                self.results_cache[cache_key] = research_results
            
            # Enhance research results with category-specific analysis
            category_insights = self._get_category_insights(task.category, research_results)
            
            # Generate comprehensive analysis
            task.research_results = research_results
            task.reasoning_analysis = await self._analyze_results(research_results)
            
            # Add category-specific insights
            if category_insights:
                task.reasoning_analysis += f"\n\nCategory-Specific Insights ({task.category}):\n{category_insights}"
            
            task.status = "completed"
            
            print(f"Task completed: {task.query}")
            
            return {
                'query': task.query,
                'category': task.category,
                'result': {
                    'status': 'success',
                    'research_results': research_results,
                    'reasoning_analysis': task.reasoning_analysis,
                    'importance_level': task.importance,
                    'search_depth': search_depth
                }
            }
            
        except (ResearchError, ReasoningError) as e:
            print(f"Task failed: {task.query} - Error: {str(e)}")  # Debug log
            task.status = "failed"
            task.error = str(e)
            return {
                'query': task.query,
                'category': task.category,
                'result': {
                    'status': 'error',
                    'error': str(e)
                }
            }

    async def process_tasks(self) -> List[dict]:
        """Process all tasks in the queue"""
        if not self.task_queue:
            return []
            
        results = []
        tasks_to_remove = []
        
        for task in self.task_queue:
            result = await self.process_task(task)
            results.append(result)
            tasks_to_remove.append(task)
        
        # Remove processed tasks
        for task in tasks_to_remove:
            self.task_queue.remove(task)
            
        return results

# Example usage
if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment
    API_KEY = os.getenv("TAVILY_API_KEY")
    if not API_KEY:
        raise ValueError("TAVILY_API_KEY environment variable is not set")
    
    agent = WorkflowAgent(api_key=API_KEY)
    
    # Add some example tasks
    agent.add_task("What are the latest developments in AI?", "technology", 3)
    agent.add_task("Best practices for Python async programming", "programming", 2)
    
    # Run the workflow
    async def main():
        results = await agent.process_tasks()
        for result in results:
            print(f"\nQuery: {result['query']}")
            print(f"Category: {result['category']}")
            print("Results:", result['result'])
    
    asyncio.run(main())
