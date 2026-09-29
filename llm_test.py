from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field

load_dotenv()
client = genai.Client()


class SEOSuggestion(BaseModel):
    suggested_title: str = Field(description="An improved page title, 60 characters or fewer.")
    suggested_meta_description: str = Field(
        description="An improved meta description, 160 characters or fewer."
    )
    reasoning: str = Field(description="One or two sentences explaining the changes.")


# Pretend audit data (from example.com), so we can test without the API server
page = {
    "title": "Example Domain",
    "meta_description": None,
    "h1": ["Example Domain"],
    "issues": ["Meta description is missing."],
}

prompt = f"""You are an SEO assistant. Improve this page's title and meta description.

Current title: {page["title"]}
Current meta description: {page["meta_description"]}
H1 headings: {page["h1"]}
Issues found: {page["issues"]}

Keep the title to 60 characters or fewer and the meta description to 160 or fewer.
Base your suggestions only on the information given."""

interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input=prompt,
    response_format={
        "type": "text",
        "mime_type": "application/json",
        "schema": SEOSuggestion.model_json_schema(),
    },
)

print("Raw reply:", interaction.output_text)

suggestion = SEOSuggestion.model_validate_json(interaction.output_text)
print("Title:", suggestion.suggested_title, f"({len(suggestion.suggested_title)} chars)")
print("Meta:", suggestion.suggested_meta_description, f"({len(suggestion.suggested_meta_description)} chars)")
print("Why:", suggestion.reasoning)