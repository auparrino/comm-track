"""
Pisubí — Cliente LLM con rotación y fallback
Proveedor principal: Groq → Cerebras → Mistral

Usa la interfaz compatible con OpenAI (todos los proveedores la soportan).
"""
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.config import LLM_PROVIDERS, LLM_PROVIDER_ORDER

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class LLMClient:
    """
    Cliente unificado para múltiples proveedores LLM.
    Intenta cada proveedor en orden; si uno falla, pasa al siguiente.
    """

    def __init__(self, provider_order: Optional[list[str]] = None):
        self.provider_order = provider_order or LLM_PROVIDER_ORDER

    def _get_client(self, provider: str):
        if OpenAI is None:
            raise ImportError("Instalar openai: pip install openai")
        import os
        cfg = LLM_PROVIDERS[provider]
        api_key = os.getenv(cfg["api_key_env"], "")
        if not api_key:
            raise ValueError(f"API key no configurada: {cfg['api_key_env']}")
        return OpenAI(api_key=api_key, base_url=cfg["base_url"]), cfg["model"]

    def complete(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.1,
        max_tokens: int = 512,
    ) -> tuple[str, str]:
        """
        Genera una respuesta usando el primer proveedor disponible.

        Returns:
            (response_text, provider_used)
        """
        last_error = None
        for provider in self.provider_order:
            try:
                client, model = self._get_client(provider)
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})

                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                text = resp.choices[0].message.content.strip()
                return text, provider

            except Exception as exc:
                last_error = exc
                print(f"[LLM] {provider} falló: {exc}. Probando siguiente...")
                continue

        raise RuntimeError(
            f"Todos los proveedores LLM fallaron. Último error: {last_error}"
        )

    def classify_news(self, title: str, snippet: str) -> dict:
        """
        Clasifica una noticia y retorna dict con campos estándar.
        Retorna también el proveedor utilizado.
        """
        import json

        prompt = f"""Clasificá esta noticia sobre commodities:
Título: {title}
Snippet: {snippet[:500] if snippet else '(sin snippet)'}

Respondé ÚNICAMENTE con un JSON válido, sin texto adicional:
{{
  "commodities": ["lithium", "gold", "soy", "other"],
  "sentiment": "positive|negative|neutral",
  "signal_type": "regulatory|geopolitical|supply|demand|climate|technology|price|other",
  "relevance_score": 0.0,
  "impact_direction": "bullish|bearish|neutral",
  "summary_es": "Resumen en 1-2 oraciones en español."
}}"""

        system = ("Sos un analista experto en mercados de commodities. "
                  "Respondés siempre con JSON válido.")

        text, provider = self.complete(prompt, system=system, temperature=0.0, max_tokens=256)

        # Parsear JSON — limpiar posibles backticks
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(text)
        result["llm_provider"] = provider
        return result

    def generate_weekly_summary(
        self,
        commodity_name: str,
        news_items: list[dict],
        variables: list[dict],
        trade_summary: dict | None = None,
    ) -> dict:
        """
        Genera un resumen semanal de un commodity basado en noticias y variables.
        Retorna dict con: summary_text, key_signals, llm_provider.
        """
        import json

        # Armar contexto de noticias
        news_text = ""
        for i, n in enumerate(news_items[:10], 1):
            sentiment = n.get("sentiment", "?")
            direction = n.get("impact_direction", "?")
            news_text += f"{i}. [{sentiment}/{direction}] {n.get('title', '')} — {n.get('summary_es') or n.get('snippet', '')[:150]}\n"

        # Armar contexto de variables
        vars_text = ""
        for v in variables:
            val = v.get("value_text") or str(v.get("value", ""))
            vars_text += f"- {v.get('variable_name')}: {val} ({v.get('unit', '')})\n"

        # Armar contexto de comercio exterior
        trade_text = ""
        if trade_summary:
            trade_text = (
                f"Exportaciones AR (últimos 12 meses): "
                f"USD {trade_summary.get('total_export_usd', 0)/1e9:.2f} bn\n"
            )

        prompt = f"""Generá un resumen semanal conciso del mercado de {commodity_name} para un analista argentino.

NOTICIAS RECIENTES:
{news_text or '(sin noticias)'}

VARIABLES MACROECONÓMICAS:
{vars_text or '(sin datos)'}

{trade_text}

Respondé ÚNICAMENTE con JSON válido:
{{
  "summary_text": "Párrafo de 3-4 oraciones en español describiendo el estado actual del mercado, principales drivers y perspectiva de corto plazo.",
  "key_signals": ["señal 1 corta", "señal 2 corta", "señal 3 corta"]
}}"""

        system = (
            "Sos un analista senior de commodities con foco en impacto para Argentina. "
            "Respondés siempre con JSON válido, sin markdown ni texto adicional."
        )

        text, provider = self.complete(
            prompt, system=system, temperature=0.2, max_tokens=512
        )
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(text)
        result["llm_provider"] = provider
        return result

    def generate_alerts(
        self,
        commodity_name: str,
        high_impact_news: list[dict],
        variables: list[dict],
    ) -> list[dict]:
        """
        Genera alertas de señales de alto impacto para un commodity.
        Retorna lista de dicts con: title, description, severity, signal_type.
        """
        import json

        if not high_impact_news and not variables:
            return []

        news_text = ""
        for n in high_impact_news[:5]:
            news_text += (
                f"- [{n.get('impact_direction','?')}] {n.get('title','')} "
                f"(relevancia: {n.get('relevance_score',0):.1f})\n"
            )

        prompt = f"""Dado el siguiente contexto del mercado de {commodity_name}, identificá alertas de señales de alto impacto.

NOTICIAS DE ALTO IMPACTO:
{news_text or '(ninguna)'}

Generá SOLO las alertas más relevantes (máximo 3). Respondé con JSON:
[
  {{
    "title": "Título corto de la alerta",
    "description": "1-2 oraciones explicando el impacto esperado.",
    "severity": "high|medium",
    "signal_type": "regulatory|geopolitical|supply|demand|climate|price|technology"
  }}
]"""

        system = (
            "Sos un analista de riesgo de commodities. "
            "Respondés con JSON válido solamente."
        )

        text, provider = self.complete(
            prompt, system=system, temperature=0.1, max_tokens=512
        )
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        alerts = json.loads(text)
        for a in alerts:
            a["llm_provider"] = provider
        return alerts


# Instancia global reutilizable
llm = LLMClient()
