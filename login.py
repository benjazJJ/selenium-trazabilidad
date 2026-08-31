from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import platform
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# CONFIGURACIÓN GOOGLE SHEETS

DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
# El archivo credenciales.json debe estar junto a login.py
RUTA_CREDS = os.path.join(DIR_ACTUAL, "credenciales.json")
# Nombre EXACTO del documento de Google Sheets
NOMBRE_DOCUMENTO_SHEETS = "Trazabilidad Selenium"

# Información del computador
NOMBRE_EQUIPO = platform.node()
SISTEMA_OPERATIVO = platform.system()


# Permisos correctos para Google Sheets + Google Drive

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# CONECTAR CON GOOGLE SHEETS


def conectar_sheets():

    print("[SHEETS] Intentando conectar con Google Sheets...")

    # Comprobar que existe credenciales.json

    if not os.path.exists(RUTA_CREDS):

        raise FileNotFoundError(
            f"No se encontró el archivo de credenciales:\n{RUTA_CREDS}"
        )

    # Cargar credenciales de la cuenta de servicio

    creds = Credentials.from_service_account_file(RUTA_CREDS, scopes=SCOPES)

    # Autorizar gspread

    cliente = gspread.authorize(creds)

    # Abrir documento por nombre

    documento = cliente.open(NOMBRE_DOCUMENTO_SHEETS)

    # Tomar primera hoja

    hoja = documento.sheet1

    print("[SHEETS] Conexión exitosa.")

    return hoja


# INICIALIZAR HOJA


def inicializar_hoja(hoja):
    """

    Si Google Sheets está vacío,

    crea automáticamente los encabezados.

    """

    cabeceras = [
        "Fecha/Hora",
        "PC",
        "SO",
        "Accion/Paso",
        "Resultado/Estado",
        "Duracion (seg)",
        "Hora Termino",
    ]

    valores = hoja.get_all_values()

    if not valores:

        hoja.append_row(cabeceras)

        print("[SHEETS] Cabecera creada.")

    elif valores[0] != cabeceras:

        hoja.insert_row(cabeceras, 1)

        print("[SHEETS] Cabecera agregada en la fila 1.")

    else:

        print("[SHEETS] La hoja ya tiene cabeceras.")


# COMPROBAR SI PC YA APARECE


def pc_ya_registrado(hoja):

    valores = hoja.get_all_values()

    if len(valores) <= 1:

        return False

    pcs_registrados = []

    for fila in valores[1:]:

        if len(fila) > 1:

            pcs_registrados.append(fila[1])

    return NOMBRE_EQUIPO in pcs_registrados


# REGISTRAR ACCIÓN
def registrar_accion_sheets(hoja, accion, resultado, tiempo_inicio):

    try:

        tiempo_fin = time.time()

        duracion = round(tiempo_fin - tiempo_inicio, 2)

        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        hora_termino = datetime.now().strftime("%H:%M:%S")

        hoja.append_row(
            [
                fecha_hora,
                NOMBRE_EQUIPO,
                SISTEMA_OPERATIVO,
                accion,
                resultado,
                duracion,
                hora_termino,
            ]
        )

        print(f"[LOG] {accion} -> {resultado}")

    except Exception as e:

        print(f"[ERROR SHEETS] No se pudo registrar la acción: {e}")


# CONEXIÓN GOOGLE SHEETS
hoja_logs = None

try:

    hoja_logs = conectar_sheets()

    inicializar_hoja(hoja_logs)

    if pc_ya_registrado(hoja_logs):

        print(f"[AVISO] El equipo {NOMBRE_EQUIPO} ya tiene " f"registros anteriores.")

        print("[AVISO] Se agregará una nueva ejecución.")

    else:

        print(f"[INFO] Primera ejecución detectada " f"para el PC {NOMBRE_EQUIPO}.")


except Exception as e:

    print("")

    print("========================================")

    print("ERROR AL CONECTAR CON GOOGLE SHEETS")

    print("========================================")

    print(e)

    print("")

    print("Comprueba que:")

    print("1. Existe credenciales.json")

    print("2. Google Sheets API está habilitada")

    print("3. Google Drive API está habilitada")

    print("4. Compartiste la hoja con el correo " "de la cuenta de servicio")

    print("5. El documento se llama exactamente:")

    print(NOMBRE_DOCUMENTO_SHEETS)

    raise


# CONFIGURACIÓN FIREFOX
RUTA_PERFIL = os.path.join(DIR_ACTUAL, "perfil_firefox_persistente")

os.makedirs(RUTA_PERFIL, exist_ok=True)


options = Options()

options.add_argument("-profile")

options.add_argument(RUTA_PERFIL)


RUTA_GECKODRIVER = r"C:\Program Files\geckodriver.exe"

if not os.path.exists(RUTA_GECKODRIVER):

    print(f"[ERROR] No se encontró GeckoDriver en:")

    print(RUTA_GECKODRIVER)

    raise FileNotFoundError(RUTA_GECKODRIVER)


service = Service(RUTA_GECKODRIVER)


driver = webdriver.Firefox(service=service, options=options)


url_login = "https://fundacion-instituto-profesional-duoc-uc.github.io/ATY1102-MantenedorUsuarios/index.html"


try:

    print("")

    print("==============================")

    print("PRUEBA LOGIN INCORRECTO")

    print("==============================")

    t_inicio = time.time()

    driver.get(url_login)

    time.sleep(2)

    user_box = driver.find_element(By.ID, "username")

    pass_box = driver.find_element(By.ID, "password")

    user_box.clear()

    user_box.send_keys("test123")

    pass_box.clear()

    pass_box.send_keys("clave123")

    time.sleep(1)

    pass_box.submit()

    time.sleep(3)

    if driver.find_elements(By.ID, "username"):

        print("[OK] Credenciales incorrectas rechazadas.")

        registrar_accion_sheets(
            hoja_logs,
            "Login Fallido Intencional",
            "Credenciales rechazadas correctamente",
            t_inicio,
        )

    else:

        print("[ERROR] Las credenciales incorrectas " "parecen haber sido aceptadas.")

        registrar_accion_sheets(
            hoja_logs,
            "Login Fallido Intencional",
            "ERROR - Credenciales incorrectas aceptadas",
            t_inicio,
        )

    print("")

    print("==============================")

    print("PRUEBA LOGIN CORRECTO")

    print("==============================")

    t_inicio = time.time()

    driver.get(url_login)

    time.sleep(2)

    user_box = driver.find_element(By.ID, "username")

    pass_box = driver.find_element(By.ID, "password")

    user_box.clear()

    user_box.send_keys("duoc")

    pass_box.clear()

    pass_box.send_keys("duoc123")

    time.sleep(1)

    pass_box.submit()

    # Esperar máximo 10 segundos

    wait = WebDriverWait(driver, 10)

    elemento_derecha = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Datos Registrados')]")
        )
    )

    assert elemento_derecha.is_displayed()

    print("[OK] Inicio de sesión exitoso verificado.")

    registrar_accion_sheets(hoja_logs, "Login Correcto", "Exitoso", t_inicio)

    # USUARIOS QUE SE AGREGARÁN

    usuarios_nuevos = [
        {"nombre": "Carlos Perez", "email": "ca.perez@duocuc.cl", "ciudad": "Santiago"},
        {"nombre": "Ana Gomez", "email": "an.gomez@duocuc.cl", "ciudad": "Valparaiso"},
        {"nombre": "Luis Rojas", "email": "lu.rojas@duocuc.cl", "ciudad": "Concepcion"},
    ]

    # REGISTRAR USUARIOS

    for usuario in usuarios_nuevos:

        print("")

        print(f"Procesando usuario: {usuario['nombre']}")

        t_inicio = time.time()

        # COMPROBAR SI YA EXISTE
        if usuario["nombre"] in driver.page_source:

            print(f"[SKIP] {usuario['nombre']} ya existe.")

            registrar_accion_sheets(
                hoja_logs,
                f"Crear usuario: {usuario['nombre']}",
                "SALTADO - Usuario ya existente",
                t_inicio,
            )

            continue

        # BUSCAR INPUT NOMBRE

        if driver.find_elements(By.ID, "nombre"):

            input_nombre = driver.find_element(By.ID, "nombre")

        else:

            input_nombre = driver.find_element(
                By.XPATH, "//input[@placeholder='Nombre']"
            )

        # BUSCAR INPUT EMAIL

        if driver.find_elements(By.ID, "email"):

            input_email = driver.find_element(By.ID, "email")

        else:

            input_email = driver.find_element(By.XPATH, "//input[@type='email']")

        # BUSCAR INPUT CIUDAD

        if driver.find_elements(By.ID, "ciudad"):

            input_ciudad = driver.find_element(By.ID, "ciudad")

        else:

            input_ciudad = driver.find_element(
                By.XPATH, "//input[contains(@placeholder, 'Ciudad')]"
            )

        # BOTÓN GUARDAR

        btn_guardar = driver.find_element(
            By.XPATH, "//button[contains(text(), 'Guardar Datos')]"
        )

        # RELLENAR FORMULARIO

        #

        input_nombre.clear()

        input_nombre.send_keys(usuario["nombre"])

        input_email.clear()

        input_email.send_keys(usuario["email"])

        input_ciudad.clear()

        input_ciudad.send_keys(usuario["ciudad"])

        time.sleep(0.5)

        btn_guardar.click()

        time.sleep(1)

        # COMPROBAR RESULTADO

        if usuario["nombre"] in driver.page_source:

            print(f"[OK] {usuario['nombre']} " f"se registró correctamente.")

            registrar_accion_sheets(
                hoja_logs, f"Crear usuario: {usuario['nombre']}", "Exitoso", t_inicio
            )

        else:

            print(f"[ERROR] {usuario['nombre']} " f"no aparece registrado.")

            registrar_accion_sheets(
                hoja_logs, f"Crear usuario: {usuario['nombre']}", "FALLIDO", t_inicio
            )

    # LEER TABLA FINAL

    t_inicio = time.time()

    print("")

    print("==============================")

    print("LISTA DE USUARIOS")

    print("==============================")

    filas = driver.find_elements(By.XPATH, "//table//tr")

    if not filas:

        filas = driver.find_elements(By.XPATH, "//*[contains(@class, 'table')]//tr")

    usuarios_encontrados = 0

    for fila in filas:

        celdas = fila.find_elements(By.TAG_NAME, "td")

        if celdas:

            datos_fila = [celda.text.strip() for celda in celdas if celda.text.strip()]

            if datos_fila:

                usuarios_encontrados += 1

                print(" | ".join(datos_fila))

    registrar_accion_sheets(
        hoja_logs,
        "Lectura de Tabla Final",
        f"Exitoso ({usuarios_encontrados} usuarios)",
        t_inicio,
    )

    print("")

    print("Automatización terminada correctamente.")

    input("Presione ENTER para cerrar el navegador...")


# ERROR GENERAL
except Exception as e:

    print("")
    print("==============================")
    print("ERROR EN SELENIUM")
    print("==============================")
    print(str(e))

    if hoja_logs is not None:

        registrar_accion_sheets(
            hoja_logs, "Error Critico", f"Excepcion: {str(e)[:100]}", time.time()
        )

    raise


finally:

    driver.quit()

    print("[FIN] Navegador cerrado.")
