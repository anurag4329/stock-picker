from crewai import Agent, Crew, Process, Task
from crewai.memory import ShortTermMemory, LongTermMemory, EntityMemory
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage
from crewai.memory.storage.rag_storage import RAGStorage
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

from crewai_tools.tools.serper_dev_tool.serper_dev_tool import SerperDevTool
from pydantic import BaseModel, Field

from .tools.push_notification import PushNotificationTool


class TrendingCompany(BaseModel):
    """A company that is trending in the news and attracting attention"""
    name: str = Field(description="The name of the company")
    ticker: str = Field(description="The ticker symbol of the company")
    reason: str = Field(description="Reason this company is trending in the news")


class TrendingCompanyList(BaseModel):
    """A list of multiple trending companies that are in the news"""
    companies: List[TrendingCompany] = Field(description="A list of trending companies")


class TrendingCompanyResearch(BaseModel):
    """A research report on a trending company"""
    name: str = Field(description="The name of the company")
    market_position: str = Field(description="Current market position and competetive analysis")
    future_outlook: str = Field(description="Future outlook and growth potential")
    investment_potential: str = Field(description="Investment potential and suitability for investment")
    # news_articles: List[str] = Field(description="A list of news articles about the company")


class TrendingCompanyResearchList(BaseModel):
    """A list of detailed research reports on trending companies"""
    reports: List[TrendingCompanyResearch] = Field(
        description="A list of comprehensive research reports on all trending companies")


@CrewBase
class StockPicker():
    """StockPicker crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def trending_company_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['trending_company_finder'], tools=[SerperDevTool()], memory=True,
            verbose=True
        )

    @agent
    def financial_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['financial_researcher'], tools=[SerperDevTool()],
            verbose=True
        )

    @agent
    def stock_picker(self) -> Agent:
        return Agent(
            config=self.agents_config['stock_picker'], tools=[PushNotificationTool()], memory=True,
            verbose=True
        )

    @task
    def find_trending_companies(self) -> Task:
        return Task(
            config=self.tasks_config['find_trending_companies'],
            output_pydantic=TrendingCompanyList,
            description="Find the most trending companies in the news"
        )

    @task
    def research_trending_companies(self) -> Task:
        return Task(
            config=self.tasks_config['research_trending_companies'],
            output_pydantic=TrendingCompanyResearchList,
            description="Research the most trending companies in the news"
        )

    @task
    def pick_best_company(self) -> Task:
        return Task(
            config=self.tasks_config['pick_best_company'],
            # output_pydantic=List[str],
            description="Pick the best stocks from the trending companies"
        )

    @crew
    def crew(self) -> Crew:
        """Creates the StockPicker crew"""

        manager = Agent(
            config=self.agents_config['manager'],
            allow_delegation=True,
            verbose=True
        )

        short_term_memory = ShortTermMemory(
            storage=RAGStorage(
                embedder_config={
                    "provider": "openai",
                    "config": {
                        "model": "text-embedding-3-small",
                    }
                },
                type="short_term",
                path="./memory",
            ),
        )

        long_term_memory = LongTermMemory(
            storage=LTMSQLiteStorage(
                db_path="./memory/long_term_memory_storage.db"
            )
        )

        entity_memory = EntityMemory(
            storage=RAGStorage(
                embedder_config={
                    "provider": "openai",
                    "config": {
                        "model": "text-embedding-3-small",
                    }
                },
                type="short_term",
                path="./memory",
            ),
        )

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            verbose=True,
            manager_agent=manager,
            memory=True,
            long_term_memory=long_term_memory,
            short_term_memory=short_term_memory,
            entity_memory=entity_memory

        )
