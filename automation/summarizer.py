"""
Memo summarizer — turn Juan's voice memo into the Blueprint §8 debrief fields
and a §9 seller classification, using the Claude API.

Returns a dict:
  entered, disposition, asking_price, offer_range, repairs, motivation,
  decision_maker, objection, next_action, follow_up_date, classification
"""

import os
import json
import anthropic

_CLASSES = [
    "Ready Now", "Wants More Money", "Family Decision", "Shopping Offers",
    "Title / Legal Issue", "Tenant / Access", "Long-Term Nurture", "Pass",
]

_SYSTEM = (
    "You extract a structured real-estate acquisition debrief from a short voice "
    "memo recorded by an investor after visiting a property. Return ONLY JSON with "
    "keys: entered (bool), disposition ('Pursuing'|'Nurturing'|'Passing'), "
    "asking_price (str|null), offer_range (str|null), repairs (str|null), "
    "motivation (str|null), decision_maker (str|null), objection (str|null), "
    "next_action (str|null), follow_up_date (YYYY-MM-DD|null), classification "
    f"(one of {_CLASSES}). If a field isn't stated, use null. Do not invent facts."
)


class Summarizer:
    def __init__(self, api_key=None, model=None):
        self.client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")

    def summarize(self, transcript):
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            system=_SYSTEM,
            messages=[{"role": "user", "content": f"Voice memo:\n{transcript}"}],
        )
        text = "".join(b.text for b in msg.content if b.type == "text").strip()
        text = text[text.find("{"): text.rfind("}") + 1]
        data = json.loads(text)
        if data.get("classification") not in _CLASSES:
            data["classification"] = ""  # let the pipeline escalate for a human
        return data
