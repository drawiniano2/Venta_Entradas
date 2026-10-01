# 🎟️ Venta de Entradas para Eventos y Conciertos

Proyecto Backend desarrollado con **Django** y **Django REST Framework** para la gestión y venta de entradas para eventos y conciertos.

## 👨‍💻 Autor

**Christian Andrés Cisterna Trigo**

Proyecto académico desarrollado para INACAP.

## 🚀 Tecnologías utilizadas

- Python
- Django
- Django REST Framework
- PostgreSQL
- JWT (JSON Web Token)
- django-filter
- Swagger / OpenAPI
- HTML y CSS
- Git y GitHub

## 👥 Roles de usuario

### ESPECTADOR

Puede registrarse, iniciar sesión, consultar eventos, agregar entradas al carrito, realizar compras, consultar sus compras y visualizar sus entradas con código QR.

### ORGANIZADOR

Puede administrar eventos y tipos de entrada desde su panel, además de validar entradas correspondientes a sus propios eventos.

## 🛒 Carrito de compra

El sistema utiliza un carrito persistente asociado al usuario.

Agregar entradas al carrito **no descuenta inmediatamente el stock**. El stock se actualiza al confirmar correctamente la compra.

## 💳 Compras y stock

Durante la confirmación de una compra:

1. Se verifica la disponibilidad de stock.
2. Se descuenta la cantidad correspondiente.
3. Se actualiza el estado de la compra.
4. Se generan las entradas individuales.

## 🎫 Entradas y códigos QR

Cada entrada emitida posee un identificador UUID individual y código QR.

El organizador puede validar las entradas de sus eventos. Una entrada válida pasa a estado **UTILIZADA** después de su validación y no puede utilizarse nuevamente.

## 🔐 Autenticación

La API utiliza autenticación mediante **JWT**, incluyendo tokens Access y Refresh.

El sistema aplica permisos según el rol del usuario.

## 🔎 API REST

El proyecto implementa una API REST mediante Django REST Framework para administrar los principales recursos del sistema.

También incorpora filtros mediante **django-filter**.

## 📚 Swagger / OpenAPI

Con el servidor ejecutándose localmente, la documentación interactiva se encuentra en:

http://127.0.0.1:8000/api/docs/

## 🗄️ Base de datos

El proyecto utiliza **PostgreSQL** como sistema gestor de base de datos.

## 📁 Estructura principal

Venta_Entradas/
- accounts/
- carrito/
- compras/
- config/
- entradas/
- eventos/
- templates/
- manage.py
- requirements.txt
- .gitignore
- README.md

## ⚙️ Instalación

Clonar el repositorio:

    git clone https://github.com/drawiniano2/Venta_Entradas.git

Entrar al proyecto:

    cd Venta_Entradas

Crear el entorno virtual:

    python -m venv venv

Activarlo en Windows PowerShell:

    .\venv\Scripts\Activate.ps1

Instalar las dependencias:

    pip install -r requirements.txt

## 🗃️ Migraciones

    python manage.py migrate

## ▶️ Ejecutar el proyecto

    python manage.py runserver

Abrir en el navegador:

http://127.0.0.1:8000/

## 🧪 Funcionalidades implementadas

- Registro e inicio de sesión
- Roles ESPECTADOR y ORGANIZADOR
- Autenticación JWT
- Gestión de eventos
- Gestión de recintos
- Gestión de tipos de entrada
- Filtros
- Carrito persistente
- Confirmación de compras
- Control de stock
- Generación de entradas
- UUID individual
- Código QR
- Consulta de compras
- Consulta de entradas
- Validación de entradas
- Prevención de reutilización
- API REST
- Swagger / OpenAPI
- Página 404 personalizada

## 🔒 Seguridad del repositorio

Los archivos sensibles y elementos locales que no deben publicarse están excluidos mediante `.gitignore`, incluyendo el entorno virtual, archivos `.env`, cachés y otros archivos temporales.

## 📌 Estado del proyecto

**Proyecto funcional y preparado para entrega académica.**

Se verificó el flujo principal de eventos, carrito, compra, emisión y validación de entradas.

## 📄 Uso

Proyecto desarrollado con fines académicos y educativos.
