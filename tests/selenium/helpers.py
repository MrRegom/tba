"""Helpers reutilizables para pruebas Selenium de formularios."""
from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select


def select_by_text_or_first(driver, name: str, text: str | None = None) -> str:
    element = driver.find_element(By.NAME, name)
    select = Select(element)
    if text:
        try:
            select.select_by_visible_text(text)
            return text
        except Exception:
            pass
    for option in select.options:
        value = option.get_attribute("value")
        if value:
            select.select_by_value(value)
            return option.text.strip()
    raise AssertionError(f"No hay opciones disponibles para el campo {name}")


def fill_input(driver, name: str, value: str) -> None:
    field = driver.find_element(By.NAME, name)
    field.clear()
    field.send_keys(value)


def set_input_value(driver, name: str, value: str) -> None:
    field = driver.find_element(By.NAME, name)
    driver.execute_script(
        "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true})); arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
        field,
        value,
    )


def replace_input_value(driver, name: str, value: str) -> None:
    field = driver.find_element(By.NAME, name)
    field.send_keys(Keys.CONTROL, "a")
    field.send_keys(str(value))


def submit_last_form(driver) -> None:
    buttons = driver.find_elements(By.XPATH, "//form//button[@type='submit'] | //form//input[@type='submit']")
    visible = [button for button in buttons if button.is_displayed()]
    target = visible[-1] if visible else (buttons[-1] if buttons else None)
    if target is None:
        raise AssertionError("No se encontro un boton submit visible")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
    try:
        target.click()
    except Exception:
        driver.execute_script("arguments[0].click();", target)


def force_select_value(driver, name: str, value: str, label: str) -> None:
    driver.execute_script(
        """
        const select = document.getElementsByName(arguments[0])[0];
        if (!select) { return; }
        let option = Array.from(select.options).find(opt => opt.value === arguments[1]);
        if (!option) {
            option = new Option(arguments[2], arguments[1], true, true);
            select.add(option);
        }
        select.value = arguments[1];
        select.dispatchEvent(new Event('change', {bubbles: true}));
        """,
        name,
        str(value),
        label,
    )


def page_has_text(driver, text: str) -> bool:
    return text.lower() in driver.page_source.lower()
