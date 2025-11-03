from oarepo_checks.llm_client import BaseLLMClient


class DummyClient(BaseLLMClient):
    """Client for chat.ai.e-infra.cz API."""

    def chat_completion(
        self,
        prompt: str,
        **kwargs,
    ) -> str:
        return """{
    "metadata.title": {
        "section_empty": false,
        "errors": [
            {
                "error_short": "Název je příliš obecný a neodráží obsah obrázku/fotografie",
                "error_long": "Název 'Updated Title' je nedostatečně popisný pro typ záznamu 'image-photo'. Doporučujeme upravit název tak, aby specifikoval obsah obrázku (např. 'Fotografie krajiny X z roku 2020').",
                "manual_check_needed": false
            }
        ]
    },
    "license": {
        "section_empty": false,
        "errors": [
            {
                "error_short": "Chybí licence pro veřejný záznam",
                "error_long": "Záznam má nastaveno 'access.record: public', ale chybí specifikace licence. Doporučujeme doplnit licenci (např. Creative Commons CC-BY 4.0) pro jasné určení podmínek užití.",
                "manual_check_needed": false
            }
        ]
    }
}"""
