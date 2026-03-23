# Sistema de Gestión de Inventario y Recursos Escolares (Logística TBA)

Un completo e integral sistema ERP diseñado a medida para satisfacer las necesidades de gestión de inventario, activos, compras y solicitudes de establecimientos educativos. Construido con tecnología robusta utilizando **Django** y **Bootstrap 5**, y pensado para una administración escalable, segura y sencilla.

---

## Características y Módulos Principales

El sistema está compuesto por múltiples módulos interconectados, asegurando que cada aspecto operativo quede cubierto:

- **Bodega**:
  - Catálogo detallado de artículos y categorías.
  - Gestión de stock en tiempo real (con alertas de stock crítico).
  - Registro auditable de movimientos (entradas, salidas y ajustes manuales de stock).
  - Control de ubicaciones físicas y bodegas secundarias.

- **Activos Fijos**:
  - Registro unificado para seguir la vida útil de cada activo de alto valor del colegio.
  - Asignaciones formales del equipo a personal docente o dependencias específicas.
  - Control de historial y estado operativo (en uso, reparación, de baja).

- **Módulo de Compras (Procurement)**:
  - Generación, aprobación y seguimiento en tiempo real de Órdenes de Compra (OC).
  - Directorio consolidado integrado con proveedores externos.
  - Flujo logístico para la inserción automática de la mercadería recibida a la Bodega o Activos Fijos.

- **Sistema de Solicitudes**:
  - Portal de usuario tipo "autoservicio" para docentes y administrativos.
  - Solicitudes de materiales de consumo y activos fijos bajo un sistema claro de aprobación jerárquica (Pendiente, Aprobado, Entregado, Rechazado).
  - Alertas y notificaciones.

- **Auditoría Continua**:
  - Trazabilidad total mediante middlewares de seguimiento en segundo plano. Se registra quién inserta, edita o elimina registros. 
  - Gestión centralizada de auditoría para lograr alta integridad y cumplimiento.

- **Fotocopiadora**:
  - Centro de costos que controla cuotas y solicitudes de fotocopias o impresiones.

- **Bajas de Inventario**:
  - Proceso de descarte con controles para justificar formalmente cuándo y por qué un equipo u objeto sale de inventario (daños severos, obsolescencia, etc).

- **Reportes y Dashboards**:
  - Vistas ejecutivas, gráficos avanzados (basados en ApexCharts/ECharts) orientados a facilitar la toma de decisiones.

## Stack Tecnológico

**Backend (Lógica de Negocio):**
- [Python 3.13+](https://www.python.org/)
- [Django 5.2.7](https://www.djangoproject.com/)
- [PostgreSQL](https://www.postgresql.org/) (Motor recomendado para el entorno de Producción) o SQLite (Entorno de desarrollo local)
- Gestión de dependencias mediante [`uv`](https://github.com/astral-sh/uv).

**Frontend (Interfaz de Usuario):**
- [Bootstrap 5.3](https://getbootstrap.com/) puro sin librerías invasivas.
- SCSS transpilado y optimizado utilizando el flujo de tareas de [Gulp 4](https://gulpjs.com/).
- Componentes especializados: *SweetAlert2, DataTables, Grid.js, Flatpickr*.

## Arquitectura del Proyecto

```text
tba/
├── apps/                    # Aplicaciones encapsuladas y modulares
│   ├── accounts/           # Autenticación, Roles y Perfiles de Usuarios
│   ├── activos/            # Control Patrimonial Fijo
│   ├── auditoria/          # Middlewares y tablas para la traza de cambios
│   ├── bajas_inventario/   # Justificaciones de pérdidas y descartes
│   ├── bodega/             # Inventario fungible constante
│   ├── compras/            # Proveedores y Órdenes de Compra
│   ├── fotocopiadora/      # Solicitudes de reprografía e impresión
│   ├── notificaciones/     # Bandeja de entrada y alertas al usuario
│   ├── pages/              # Portal, Vistas globales y Dashboards Base
│   ├── reportes/           # Constructor de vistas para impresión
│   └── solicitudes/        # Gestión de flujos de peticiones del colegio
├── core/                   # Configuraciones base de Django (settings.py, urls.py)
├── templates/              # Interfaz gráfica (Vistas HTML de Django)
├── static/                 # Archivos estáticos (CSS/JS)
├── src/                    # Archivos en bruto (JS/SCSS) listos para compilar en Node
├── uv.lock / pyproject.toml# Configuración de dependencias de Backend
├── package.json            # Gestor de librerías y assets de Frontend (Node.js)
└── manage.py              # CLI principal para el control de Django
```

## Requisitos Previos

- **Python 3.13** o superior.
- **Node.js** (v18+) y NPM.
- Gestor de paquetes **uv** (`pip install uv`).
- **PostgreSQL 12** o superior.

## Guía de Instalación Rápida

### 1. Clonar el repositorio

```bash
git clone https://github.com/MrRegom/tba.git
cd tba
```

### 2. Entorno Virtual y Dependencias (Python Backend)

```bash
# Crear un entorno virtual
uv venv

# Activarlo (Windows):
.venv\Scripts\activate

# Activarlo (Mac/Linux):
source .venv/bin/activate

# Instalar dependencias
uv sync
```

### 3. Dependencias de Frontend (Compilación SCSS/JS)

```bash
# Instalar dependencias visuales de Node
npm install

# Iniciar la tarea de preprocesamiento de estilos y scripts
npx gulp
```

### 4. Entorno de Datos (`.env`)

Copiar el archivo de configuración de ejemplo:

```bash
cp .env.example .env
```
_Edite el archivo `.env` configurando los accesos a la base de datos de PostgreSQL y las claves de seguridad requeridas._

### 5. Configurar la Base de Datos y Semillas

```bash
# Ejecutar migraciones de base de datos
python manage.py migrate

# (Opcional) Cargar datos iniciales de prueba:
python manage.py populate_colegio_data
```

### 6. Administrador Nativo y Servidor

```bash
# Crear la cuenta principal
python manage.py createsuperuser

# Ejecutar el servidor de desarrollo local
python manage.py runserver
```
El sistema estará disponible en la URL: `http://127.0.0.1:8000/`.

---

## Pruebas y Calidad (QA)

La plataforma cuenta con una suite de pruebas enfocada en la integridad transaccional (utilizando pytest y factory-boy). 

```bash
# Ejecutar las pruebas unitarias e integración
pytest --cov=apps apps/
```

## Seguridad e Instrucciones para Servidor de Producción

En `core/settings.py` el comportamiento difiere dependiendo del entorno de ejecución:
- En producción es requerido el uso de un proxy reverso con soporte SSL (ej. Nginx).
- La variable `DJANGO_DEBUG` en el archivo `.env` debe configurarse en `False`.
- Configurar `ALLOWED_HOSTS` aprobando únicamente los dominios de la institución (`*.logisticatba.cloud`).
- Ejecutar mediante servidor WSGI o ASGI adaptado para producción (ej. `Gunicorn`).

## Licencia

**Logística TBA - Propiedad Intelectual.**
Proyecto **Privado**. El código fuente no puede ser comercializado o reproducido públicamente sin el consentimiento explícito de sus autores.
