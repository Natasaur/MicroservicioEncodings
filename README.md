# Proyecto Django

Este es un proyecto desarrollado con **Django**.  
A continuación se detallan los pasos para instalarlo y ejecutarlo en tu máquina local.

---

## 📋 Requisitos previos

Antes de comenzar, asegúrate de tener instalado:

- [Python 3.10+](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/)
- [virtualenv](https://pypi.org/project/virtualenv/) *(opcional pero recomendado)*
- [Git](https://git-scm.com/)

---

## 🚀 Instalación y ejecución

### 1. Clonar el repositorio
```bash
git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git
cd TU_REPOSITORIO

### 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar migraciones
python manage.py migrate

# 5. Iniciar servidor
python manage.py runserver