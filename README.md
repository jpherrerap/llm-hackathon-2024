# Aplicación de Soporte al Cliente con IA

Esta es una aplicación de soporte al cliente con agentes de IA y RAG. Utiliza un backend en Python con FastAPI y un frontend en Vue.js para proporcionar una interfaz de chat interactiva que puede responder a las consultas de los clientes.

## Características

- Chat en tiempo real con IA
- Interfaz de usuario intuitiva
- Backend robusto con FastAPI
- Almacenamiento de mensajes en MongoDB

## Requisitos

- Docker y Docker Compose (recomendado), Node.js 14+
- Alternativamente: Python 3.11+, Node.js 14+, MongoDB

## Configuración y Ejecución

### Backend usando Docker Compose (Recomendado)

1. Clona este repositorio:
   ```
   git clone <url-del-repositorio>
   cd <nombre-del-directorio>
   ```

2. Crea un archivo `.env` en la raíz del proyecto y añade tu clave API de OpenAI:
   ```
   OPENAI_API_KEY=tu_clave_api_aqui
   ```

3. Ejecuta el backend con Docker Compose:
   ```
   docker compose up --build
   ```

4. Accede a la aplicación en `http://localhost:8000`

### Opción 2: Backend Manual

1. Instala las dependencias de Python:
   ```
   pip install -r requirements.txt
   ```

2. Instala y ejecuta MongoDB

3. Crea un archivo `.env` en la raíz del proyecto y añade tu clave API de OpenAI:
   ```
   OPENAI_API_KEY=tu_clave_api_aqui
   MONGO_URI=mongodb://localhost:27017
   ```

4. Ejecuta el servidor FastAPI:
   ```
   python main.py
   ```

### Frontend

1. Navega al directorio de la aplicación:
   ```
   cd app
   ```

2. Instala las dependencias de Node.js:
   ```
   npm install
   ```

3. Ejecuta el servidor de desarrollo:
   ```
   npm run dev
   ```

4. Accede a la aplicación en la URL proporcionada por Vite (generalmente `http://localhost:5173`)

## Uso

Una vez que la aplicación esté en funcionamiento, puedes interactuar con el chatbot de IA a través de la interfaz web. Escribe tus preguntas o comentarios en el campo de entrada y recibirás respuestas generadas por la IA.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue para discutir cambios mayores antes de crear un pull request.

## Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.

