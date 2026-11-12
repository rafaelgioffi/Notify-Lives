from __future__ import annotations

import subprocess
import time
from pathlib import Path

from ..config import settings
from ..db import record_attempt, update_attempt
from .base import PublicationResult


class WhatsAppAssistedAdapter:
    """Keeps the existing desktop flow, but makes it observable and retryable."""

    channel_name = "whatsapp_desktop"

    def publish(
        self,
        *,
        destination: str,
        caption: str,
        media_path: str | None = None,
        campaign_id: str = "manual",
    ) -> PublicationResult:
        attempt_record = record_attempt(
            campaign_id=campaign_id,
            channel=self.channel_name,
            destination=destination,
            status="pending",
            attempts=0,
        )
        attempts_used = 0
        try:
            import pyautogui
            import pyperclip
        except ImportError as exc:
            update_attempt(attempt_record.id, status="failed", error_message=str(exc), attempts=attempts_used)
            return PublicationResult(False, error_message=f"Dependência do WhatsApp ausente: {exc}")

        for attempt in range(1, settings.whatsapp_max_retries + 2):
            attempts_used = attempt
            update_attempt(attempt_record.id, status="sending", attempts=attempts_used)
            delay = settings.whatsapp_initial_delay if attempt == 1 else settings.whatsapp_retry_delay
            if attempt > 1:
                print(f"Retry do WhatsApp para '{destination}' em {delay:g}s (tentativa {attempt})...")
                time.sleep(delay)

            try:
                self._send_once(pyautogui, pyperclip, destination, caption, media_path)
            except Exception as exc:  # desktop UI errors are expected and must be recoverable
                if attempt > settings.whatsapp_max_retries:
                    update_attempt(attempt_record.id, status="failed", error_message=str(exc), attempts=attempts_used)
                    return PublicationResult(False, error_message=str(exc))
                print(f"Falha técnica ao preparar o WhatsApp: {exc}")
                continue

            if not settings.whatsapp_manual_confirmation or self._confirm_first_message(destination):
                update_attempt(attempt_record.id, status="published", attempts=attempts_used)
                return PublicationResult(True)

            if attempt > settings.whatsapp_max_retries:
                update_attempt(
                    attempt_record.id,
                    status="failed",
                    error_message="Envio não confirmado pelo usuário",
                    attempts=attempts_used,
                )
                return PublicationResult(False, error_message="Envio não confirmado pelo usuário")

        update_attempt(
            attempt_record.id,
            status="failed",
            error_message="Número máximo de tentativas atingido",
            attempts=attempts_used,
        )
        return PublicationResult(False, error_message="Número máximo de tentativas atingido")

    @staticmethod
    def _send_once(pyautogui, pyperclip, destination: str, caption: str, media_path: str | None) -> None:
        subprocess.run(["powershell", "-NoProfile", "-Command", "Start-Process", "whatsapp://"], check=False)
        time.sleep(4)
        pyautogui.hotkey("ctrl", "f")
        time.sleep(1)
        pyautogui.write(destination, interval=0.08)
        time.sleep(3)
        pyautogui.press(["tab", "tab"])
        pyautogui.press("enter")
        time.sleep(2)

        if media_path and Path(media_path).exists():
            pyperclip.copy("")
            pyautogui.hotkey("ctrl", "v")
            time.sleep(3)
        pyperclip.copy(caption)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(2)
        pyautogui.press("enter")

    @staticmethod
    def _confirm_first_message(destination: str) -> bool:
        answer = input(
            f"A primeira mensagem para '{destination}' foi enviada? "
            "Responda S para confirmar ou N para tentar novamente: "
        ).strip().lower()
        return answer in {"s", "sim", "y", "yes"}

