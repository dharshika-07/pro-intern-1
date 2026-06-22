from sqlalchemy.orm import Session

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from core.prompts import STORY_PROMPT
from models.story import Story, StoryNode
from core.models import StoryLLMResponse, StoryNodeLLM
from core.config import settings
from dotenv import load_dotenv

load_dotenv()

class StoryGenerator:

    @classmethod
    def _get_llm(cls):
        return ChatOpenAI(model="gpt-4o-mini")

    @classmethod
    def _generate_mock_story_data(cls, theme: str) -> StoryLLMResponse:
        from core.models import StoryNodeLLM, StoryOptionLLM
        
        theme_title = theme.capitalize() if theme else "Fantasy"
        title = f"The Quest of {theme_title}"
        
        win_node = StoryNodeLLM(
            content=f"Using all your wits in this {theme} quest, you successfully solve the final mystery! The legendary relic is yours, and peace is restored.",
            isEnding=True,
            isWinningEnding=True,
            options=[]
        )
        
        lose_node = StoryNodeLLM(
            content=f"You made a fatal miscalculation. The shadows of the {theme} world close in around you, and your journey comes to an end.",
            isEnding=True,
            isWinningEnding=False,
            options=[]
        )
        
        node_a = StoryNodeLLM(
            content=f"You head left into the dark woods. A glowing pathway appears, but you hear growls nearby. What is your move?",
            isEnding=False,
            isWinningEnding=False,
            options=[
                StoryOptionLLM(text="Follow the glowing pathway", nextNode=win_node.model_dump()),
                StoryOptionLLM(text="Investigate the growling sound", nextNode=lose_node.model_dump())
            ]
        )
        
        node_b = StoryNodeLLM(
            content=f"You step right towards the old ruins. An ancient puzzle door blocks the path, carved with runes of the {theme} era.",
            isEnding=False,
            isWinningEnding=False,
            options=[
                StoryOptionLLM(text="Attempt to solve the rune puzzle", nextNode=win_node.model_dump()),
                StoryOptionLLM(text="Force the door open", nextNode=lose_node.model_dump())
            ]
        )
        
        root_node = StoryNodeLLM(
            content=f"Your {theme} adventure begins! You stand before a split path in a strange, uncharted land. Which way will you choose?",
            isEnding=False,
            isWinningEnding=False,
            options=[
                StoryOptionLLM(text="Take the left path into the woods", nextNode=node_a.model_dump()),
                StoryOptionLLM(text="Take the right path to the ruins", nextNode=node_b.model_dump())
            ]
        )
        
        return StoryLLMResponse(title=title, rootNode=root_node)

    @classmethod
    def generate_story(cls, db: Session, session_id: str, theme: str = "fantasy")-> Story:
        api_key = settings.OPENAI_API_KEY
        is_mock = False
        if not api_key or "sk-" not in api_key or len(api_key.strip()) < 20:
            is_mock = True

        if is_mock:
            print("[TEMP LOG] OpenAI request start (MOCKED)", flush=True)
            story_structure = cls._generate_mock_story_data(theme)
            print("[TEMP LOG] OpenAI request end (MOCKED)", flush=True)
        else:
            try:
                llm = cls._get_llm()
                story_parser = PydanticOutputParser(pydantic_object=StoryLLMResponse)

                prompt = ChatPromptTemplate.from_messages([
                    (
                        "system",
                        STORY_PROMPT
                    ),
                    (
                        "human",
                        f"Create the story with this theme: {theme}"
                    )
                ]).partial(format_instructions=story_parser.get_format_instructions())

                print("[TEMP LOG] OpenAI request start", flush=True)
                raw_response = llm.invoke(prompt.invoke({}))
                print("[TEMP LOG] OpenAI request end", flush=True)

                response_text = raw_response
                if hasattr(raw_response, "content"):
                    response_text = raw_response.content

                story_structure = story_parser.parse(response_text)
            except Exception as e:
                print(f"[TEMP LOG] OpenAI generation failed, falling back to mock data: {e}", flush=True)
                print("[TEMP LOG] OpenAI request start (MOCKED FALLBACK)", flush=True)
                story_structure = cls._generate_mock_story_data(theme)
                print("[TEMP LOG] OpenAI request end (MOCKED FALLBACK)", flush=True)

        story_db = Story(title=story_structure.title, session_id=session_id)
        db.add(story_db)
        db.flush()

        root_node_data = story_structure.rootNode
        if isinstance(root_node_data, dict):
            root_node_data = StoryNodeLLM.model_validate(root_node_data)

        cls._process_story_node(db, story_db.id, root_node_data, is_root=True)

        db.commit()
        return story_db

    @classmethod
    def _process_story_node(cls, db: Session, story_id: int, node_data: StoryNodeLLM, is_root: bool = False) -> StoryNode:
        node = StoryNode(
            story_id=story_id,
            content=node_data.content if hasattr(node_data, "content") else node_data["content"],
            is_root=is_root,
            is_ending=node_data.isEnding if hasattr(node_data, "isEnding") else node_data["isEnding"],
            is_winning_ending=node_data.isWinningEnding if hasattr(node_data, "isWinningEnding") else node_data["isWinningEnding"],
            options=[]
        )
        db.add(node)
        db.flush()

        if not node.is_ending and (hasattr(node_data, "options") and node_data.options):
            options_list = []
            for option_data in node_data.options:
                next_node = option_data.nextNode

                if isinstance(next_node, dict):
                    next_node = StoryNodeLLM.model_validate(next_node)

                child_node = cls._process_story_node(db, story_id, next_node, False)

                options_list.append({
                    "text": option_data.text,
                    "node_id": child_node.id
                })

            node.options = options_list

        db.flush()
        return node