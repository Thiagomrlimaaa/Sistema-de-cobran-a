import csv
import time
from pathlib import Path
from typing import Iterable, List, Tuple
from urllib.parse import quote

from django.core.management.base import BaseCommand, CommandError

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from selenium.common.exceptions import TimeoutException


def load_numbers(file_path: Path) -> List[str]:
    if not file_path.exists():
        raise CommandError(f"Arquivo não encontrado: {file_path}")

    numbers: List[str] = []
    with file_path.open("r", encoding="utf-8") as fp:
        reader = csv.reader(fp)
        for row in reader:
            if not row:
                continue
            raw = row[0].strip()
            digits = "".join(filter(str.isdigit, raw))
            if digits:
                numbers.append(digits)
    if not numbers:
        raise CommandError("Nenhum número válido encontrado no arquivo informado.")
    return numbers


def init_driver(profile_dir: Path | None = None) -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--profile-directory=Default")
    if profile_dir:
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")

    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def wait_for_login(driver: webdriver.Chrome, timeout: int = 300) -> None:
    wait = WebDriverWait(driver, timeout)
    wait.until(EC.presence_of_element_located((By.ID, "app")))
    wait.until(
        EC.any_of(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='chat-list']")),
            EC.presence_of_element_located((By.CSS_SELECTOR, "header[data-testid='conversation-header']")),
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='conversation-panel-body']")),
        )
    )


def _find_clickable(driver: webdriver.Chrome, selectors: Iterable[Tuple[str, str]], timeout: int) -> webdriver.remote.webelement.WebElement:
    last_exc: Exception | None = None
    for by, value in selectors:
        try:
            return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            continue
    if last_exc:
        raise last_exc
    raise TimeoutException("Elemento não encontrado.")


def _find_present(driver: webdriver.Chrome, selectors: Iterable[Tuple[str, str]], timeout: int) -> webdriver.remote.webelement.WebElement:
    last_exc: Exception | None = None
    for by, value in selectors:
        try:
            return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            continue
    if last_exc:
        raise last_exc
    raise TimeoutException("Elemento não encontrado.")


def _open_chat_via_search(driver: webdriver.Chrome, queries: List[str], timeout: int) -> bool:
    search_selectors = [
        (By.CSS_SELECTOR, "div[contenteditable='true'][data-testid='chat-list-search']"),
        (By.CSS_SELECTOR, "div[contenteditable='true'][data-testid='chat-list-input']"),
        (By.CSS_SELECTOR, "div[contenteditable='true'][data-testid='chatlist-search']"),
        (By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='2']"),
        (
            By.XPATH,
            "//div[@contenteditable='true' and contains(@aria-label, 'Pesquisar')]",
        ),
    ]
    try:
        search_box = _find_clickable(driver, search_selectors, timeout=20)
    except Exception:
        return False

    result_selectors = [
        (By.CSS_SELECTOR, "div[data-testid='cell-frame-container'][role='row']"),
        (By.CSS_SELECTOR, "div[role='option']"),
        (By.XPATH, "//div[@data-testid='cell-frame-container']//span"),
        (By.XPATH, "//div[@role='presentation']//span"),
    ]

    for query in queries:
        search_box.click()
        search_box.send_keys(Keys.CONTROL, "a")
        search_box.send_keys(Keys.DELETE)
        search_box.send_keys(query)
        time.sleep(1)

        try:
            result_items = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-testid='cell-frame-container']"))
            )
            for item in result_items:
                try:
                    item.click()
                    return True
                except Exception:
                    continue
        except Exception:
            continue

    # Fallback: iniciar nova conversa digitando o número completo
    numeric_query = "".join(filter(str.isdigit, queries[0])) if queries else ""
    if not numeric_query:
        return False

    try:
        search_box.send_keys(Keys.ESCAPE)
        time.sleep(0.5)
        try:
            new_chat_btn = _find_clickable(
                driver,
                selectors=[
                    (By.CSS_SELECTOR, "span[data-testid='new-chat-button']"),
                    (By.CSS_SELECTOR, "div[data-testid='mi-new-chat']"),
                    (By.XPATH, "//div[@role='button' and @data-testid='new-chat-button']"),
                ],
                timeout=5,
            )
            new_chat_btn.click()
        except Exception:
            pass

        try:
            phone_box = _find_clickable(
                driver,
                selectors=[
                    (By.CSS_SELECTOR, "input[aria-label='Número de telefone']"),
                    (By.CSS_SELECTOR, "input[data-testid='contact-search-input']"),
                    (By.XPATH, "//input[@type='tel']"),
                    (By.XPATH, "//input[@inputmode='tel']"),
                ],
                timeout=5,
            )
            phone_box.clear()
            phone_box.send_keys(numeric_query)
            phone_box.send_keys(Keys.ENTER)
            time.sleep(2)
            return True
        except Exception:
            return False
    except Exception:
        return False


def send_message(
    driver: webdriver.Chrome,
    full_number: str,
    message: str,
    wait_time: Tuple[int, int],
) -> bool:
    driver.get("https://web.whatsapp.com/")

    try:
        wait_for_login(driver, timeout=wait_time[0])
    except Exception:
        return False

    try:
        digits = "".join(filter(str.isdigit, full_number))
        queries = []
        if digits:
            if digits.startswith("55") and len(digits) > 2:
                queries.append(digits[2:])
            if len(digits) > 9:
                queries.append(digits[-9:])
            queries.append(digits)
        queries.append(full_number)
        if not full_number.startswith("+") and digits:
            queries.append(f"+{digits}")
        if not _open_chat_via_search(driver, queries=queries, timeout=15):
            return False

        message_box = _find_clickable(
            driver,
            selectors=[
                (By.CSS_SELECTOR, "div[contenteditable='true'][data-testid='conversation-compose-box-input']"),
                (By.CSS_SELECTOR, "div[contenteditable='true'][data-testid='conversation-compose-text-input']"),
                (By.XPATH, "//div[@contenteditable='true' and @role='textbox']"),
                (By.CSS_SELECTOR, "div[contenteditable='true'] p.selectable-text.copyable-text"),
                (By.XPATH, "//div[@contenteditable='true']//p[contains(@class,'selectable-text')]"),
            ],
            timeout=wait_time[0],
        )
        message_box.click()
        message_box.send_keys(Keys.CONTROL, "a")
        message_box.send_keys(Keys.DELETE)

        lines = message.split("\n")
        for index, line in enumerate(lines):
            if line:
                message_box.send_keys(line)
            if index != len(lines) - 1:
                message_box.send_keys(Keys.SHIFT, Keys.ENTER)

        send_button = _find_clickable(
            driver,
            selectors=[
                (By.CSS_SELECTOR, "button[data-testid='compose-btn-send']"),
                (By.CSS_SELECTOR, "span[data-icon='send']"),
                (By.XPATH, "//button[@aria-label='Enviar' or @aria-label='Send']"),
            ],
            timeout=10,
        )
        send_button.click()
        time.sleep(wait_time[1])
        return True
    except Exception:
        return False


class Command(BaseCommand):
    help = (
        "Envia mensagens pelo WhatsApp Web automatizando o navegador. "
        "É necessário estar logado no WhatsApp Web e manter o navegador aberto durante o envio."
    )

    def add_arguments(self, parser):
        parser.add_argument("numbers_file", type=str, help="Caminho do arquivo CSV contendo os números (um por linha).")
        parser.add_argument("message", type=str, help="Mensagem que será enviada para cada número.")
        parser.add_argument(
            "--country-code",
            type=str,
            default="55",
            help="Código do país a ser prefixado (padrão: 55).",
        )
        parser.add_argument(
            "--profile-dir",
            type=str,
            default="",
            help="Diretório de perfil do Chrome para reutilizar sessão já autenticada.",
        )
        parser.add_argument(
            "--load-wait",
            type=int,
            default=40,
            help="Tempo máximo (em segundos) para aguardar carregamento da conversa.",
        )
        parser.add_argument(
            "--post-wait",
            type=int,
            default=3,
            help="Tempo (em segundos) para aguardar após o envio antes de seguir para o próximo número.",
        )

    def handle(self, *args, **options):
        numbers_file = Path(options["numbers_file"]).resolve()
        message = options["message"]
        country_code = options["country_code"].strip()
        profile_dir = Path(options["profile_dir"]).resolve() if options["profile_dir"] else None
        load_wait = options["load_wait"]
        post_wait = options["post_wait"]

        self.stdout.write(self.style.WARNING("Aviso: automatizar o WhatsApp Web pode violar os Termos de Serviço."))
        self.stdout.write(self.style.WARNING("Use por sua conta e risco e apenas com números autorizados."))

        numbers = load_numbers(numbers_file)
        self.stdout.write(self.style.SUCCESS(f"{len(numbers)} números carregados para envio."))

        driver = init_driver(profile_dir)
        driver.get("https://web.whatsapp.com")

        try:
            self.stdout.write(f"Aguardando carregamento do WhatsApp Web (timeout {load_wait}s)...")
            wait_for_login(driver, timeout=load_wait)
        except TimeoutException as exc:
            driver.quit()
            raise CommandError(
                "Tempo esgotado aguardando carregamento do WhatsApp Web. "
                "Verifique se o login foi concluído ou aumente --load-wait."
            ) from exc
        except Exception as exc:  # noqa: BLE001
            driver.quit()
            raise CommandError(f"Não foi possível confirmar o login no WhatsApp Web: {exc}") from exc

        success_count = 0
        failure: List[str] = []

        for number in numbers:
            full_number = f"{country_code}{number}" if not number.startswith(country_code) else number
            self.stdout.write(f"Enviando para {full_number}...")
            ok = send_message(
                driver,
                full_number=full_number,
                message=message,
                wait_time=(load_wait, post_wait),
            )
            if ok:
                success_count += 1
                self.stdout.write(self.style.SUCCESS(f"Mensagem enviada para {full_number}."))
            else:
                failure.append(full_number)
                self.stdout.write(self.style.ERROR(f"Falha ao enviar para {full_number}."))

        driver.quit()

        self.stdout.write(self.style.SUCCESS(f"Envios concluídos. Sucesso: {success_count}"))
        if failure:
            self.stdout.write(self.style.ERROR(f"Números com falha ({len(failure)}):"))
            for number in failure:
                self.stdout.write(f" - {number}")

