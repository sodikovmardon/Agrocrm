import json
from typing import Any, Dict, List, Optional

from app.core.config import settings


SYSTEM_PROMPT_BASE = """You are AgroSmart AI, an intelligent farm management assistant.
You help farmers manage their livestock, production, inventory, and finances.
Always respond in a structured format when requested.
Keep responses concise, accurate, and helpful.
Use Uzbek (O'zbek tili) language when communicating with farmers."""


async def llm_structured_output(
    system_prompt: str,
    user_prompt: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> str:
    if settings.OPENAI_API_KEY is None:
        return json.dumps({
            "operations": [],
            "warnings": ["AI sozlamalari to'liq emas. OpenAI API kaliti o'rnatilmagan."],
        })

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens or settings.OPENAI_MAX_TOKENS,
            temperature=temperature or settings.OPENAI_TEMPERATURE,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if content is None:
            return json.dumps({"operations": [], "warnings": ["AI dan bo'sh javob olindi."]})
        return content

    except ImportError:
        return json.dumps({
            "operations": [],
            "warnings": ["OpenAI kutubxonasi o'rnatilmagan. 'pip install openai' ni bajaring."],
        })
    except Exception as e:
        return json.dumps({
            "operations": [],
            "warnings": [f"AI bilan bog'lanishda xatolik: {str(e)}"],
        })


async def llm_text_response(
    system_prompt: str,
    user_prompt: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> str:
    if settings.OPENAI_API_KEY is None:
        return "AI sozlamalari to'liq emas. Iltimos, OpenAI API kalitini o'rnating."

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": f"{SYSTEM_PROMPT_BASE}\n\n{system_prompt}"},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens or settings.OPENAI_MAX_TOKENS,
            temperature=temperature or settings.OPENAI_TEMPERATURE,
        )

        content = response.choices[0].message.content
        if content is None:
            return "Kechirasiz, hozir javob bera olmayman. Iltimos, keyinroq urinib ko'ring."
        return content

    except ImportError:
        return "OpenAI kutubxonasi o'rnatilmagan. Iltimos, 'pip install openai' ni bajaring."
    except Exception as e:
        return f"AI bilan bog'lanishda xatolik yuz berdi: {str(e)}"


async def llm_classify_intent(
    question: str,
    intents: List[str],
) -> str:
    system_prompt = f"""You are an intent classifier. Classify the user's question into one of these intents:
{chr(10).join(f'- {i}' for i in intents)}

Respond with only the intent name, nothing else."""
    return await llm_text_response(system_prompt=system_prompt, user_prompt=question, temperature=0.1)
