# Health-IA — Sistema de Gestión de Llamadas y Tareas para Internación

Sistema de administración de llamadas y tareas programadas para el sector de internación de hospitales o clínicas. La aplicación permite gestionar camas, tareas y llamadas desde cualquier punto de la red mediante una interfaz web.

## Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Arquitectura](#arquitectura)
- [Tecnologías](#tecnologías)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Configuración con Podman](#configuración-con-podman)
- [Secretos y Variables de Entorno Obligatorias](#secretos-y-variables-de-entorno-obligatorias)
- [Desarrollo Local](#desarrollo-local)
- [API REST](#api-rest)
- [Uso de la Aplicación](#uso-de-la-aplicación)
- [Configuración de Hardware](#configuración-de-hardware)

---

## Descripción General

La aplicación recibe y administra:
- **Llamadas**: Provenientes de botones pulsadores en cada cama y botones de cancelación por habitación
- **Tareas**: Programadas para el personal de salud (médicos, enfermeros, administrativos)

El acceso es decentralizado: cualquier usuario con credenciales puede acceder desde cualquier punto de la red hospitalaria mediante un navegador web.

### Modos de Comunicación con Pulsadores

El sistema soporta tres configuraciones para la señal de los pulsadores:

| Modo | Descripción |
|------|-------------|
| Cableado | Señal completa por cable |
| Mixto | Cable hasta el nodo de habitación, Wi-Fi hasta el servidor |
| Inalámbrico | Placa Wi-Fi integrada en cada pulsador con batería interna |

---

## Arquitectura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend API   │────▶│   PostgreSQL    │
│   (React)       │◀────│    (Django)     │     │    Database     │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   WebSocket     │
                        │   (Channels)    │
                        └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌─────────────┐
              │  Redis   │ │ Mosquitto│ │    MQTT     │
              │ (Broker) │ │ (Broker) │ │ Dispositivo │
              └──────────┘ └──────────┘ └─────────────┘
```

---

## Tecnologías

| Capa | Tecnología |
|------|------------|
| Frontend | React 18, Bootstrap, WebSockets |
| Backend | Django 5, Django Ninja (API REST) |
| WebSockets | Django Channels |
| Base de Datos | PostgreSQL 16 |
| Broker Mensajería | Redis, Mosquitto (MQTT) |
| Contenedores | Podman |

---

## Estructura del Proyecto

```
health/
├── healthproject/          # Configuración del proyecto Django
├── nursing/                # Aplicación principal de Django
│   ├── api.py             # Endpoints de Django Ninja
│   ├── consumer.py        # Consumidores WebSocket
│   ├── models.py          # Modelos de base de datos
│   └── modular_views/     # Vistas modulares
├── nursing_react/         # Frontend React
│   ├── src/
│   │   ├── components/   # Componentes React
│   │   ├── context/      # Estado global
│   │   └── services/     # API y WebSocket clients
│   └── build/            # Build de producción
├── mosquitto/             # Configuración del broker MQTT
├── data/                  # Datos persistentes (volúmenes)
│   └── db/               # Base de datos PostgreSQL
├── entrypoint.sh          # Script de inicio del contenedor
└── requirements.txt       # Dependencias Python
```

---

## Configuración con Podman

### Requisitos

- Podman instalado
- Permisos para ejecutar contenedores rootless

### Archivos de Configuración

| Archivo | Descripción |
|---------|-------------|
| `pod.yaml` | Definición del Pod Kubernetes |
| `Dockerfile` | Imagen de la aplicación |
| `.env` | Variables de entorno |

### Variables de Entorno

```bash
DB=db
DB_NAME=db
DB_USER=postgres
DB_PASSWORD=postgres
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Levantar la Aplicación

Si se realizaron cambios en el frontend y/o el backend, es posible que previamente desees realizar builds.

Puedes utilizar alguno de los tres scripts:

>
>- Build del backend: `podmanbuildbackend.sh`
>- Build del frontend: `podmanbuildfrontend.sh`
>- Build de frontend y backend: `podmanbuildall.sh`

Luego, puedes obviar el paso 1 a continuación ya que está incluído en los scripts:

```bash
# 1. Buildear la imagen de la aplicación
podman build -t health-app:latest .

# 2. Crear y levantar el pod
podman kube play pod.yaml

# 1 y 2 En un sólo paso
bash podmanbuildall.sh && podman kube play pod.yaml

# 3. Verificar estado
podman pod ps
podman ps
```

### Ver Logs

```bash
podman logs health-pod-app
podman logs health-pod-db
```

### Detener la Aplicación

```bash
podman kube down pod.yaml

# O manualmente
podman pod stop health-pod
podman pod rm health-pod
```

### Permisos de Archivos

Si hay problemas de permisos con los volúmenes:

```bash
sudo chmod -R 777 ./health/ 
```

> [!CAUTION]
> El ejemplo muestra el máximo de permisos que se pueden otorgar en un sistema Unix y en forma recursiva a las todas las subcarpetas y archivos. Esto puede resultar en un riesgo de seguridad.

---

## Secretos y Variables de Entorno Obligatorias

> [!IMPORTANT]
> Los archivos `.env` **nunca** se commitean. Ya están ignorados por `.gitignore`
> (`**/.env`) y **sacados del índice de git**. Si modificás o creás un `.env`,
> asegurate de que quede fuera del control de versiones.

La aplicación exige ciertas variables de entorno para arrancar de forma segura.
Si faltan, **el arranque falla con un mensaje claro** en lugar de usar valores
por defecto inseguros que estarían hardcodeados en el código versionado.

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `SECRET_KEY` | Sí | Clave de firma de Django (firma sesiones, JWTs, tokens CSRF). Debe ser única y secreta por entorno. |
| `CALL_SECRET_KEY` | No (default inseguro) | Secreto compartido que autentica los mensajes de los pulsadores (WebSocket `callData` y MQTT `mqtt/call/`). Debe coincidir con el valor configurado en el firmware de los pulsadores. **En producción es OBLIGATORIO definirlo** con un valor sólido y único. |
| `DJANGO_SUPERUSER_USERNAME` | Solo primer arranque | Username del superusuario inicial. |
| `DJANGO_SUPERUSER_PASSWORD` | Solo primer arranque | Contraseña del superusuario inicial. |
| `DJANGO_SUPERUSER_EMAIL` | Solo primer arranque | Email del superusuario inicial. |

Estas credenciales **solo** se necesitan la primera vez que se levanta la app
(para crear el superusuario inicial). Si ya existe un superusuario, el arranque
no las exige.

> [!WARNING]
> `SECRET_KEY` y las contraseñas expuestas alguna vez en git (o en un README,
> PR, o chat) deben considerarse **comprometidas** y **rotarse** inmediatamente.
> Nunca las compartas fuera del entorno seguro donde corre la aplicación.
> `CALL_SECRET_KEY` usa un default inseguro (`CHANGE-ME-IN-PRODUCTION`) — en
> producción DEBE definirse por entorno. Si la clave vieja hardcodeada
> (`this&is$a$key&to?prevent?hacking`) llegó a estar en git o en el firmware,
> rótala y actualizá pulsador + backend al mismo valor nuevo.

---

## Desarrollo Local

### Servicios Externos Requeridos

Necesitas tener corriendo:
- PostgreSQL (puerto 5432)
- Redis (puerto 6379)
- Mosquitto MQTT (puerto 1883)

```bash
# PostgreSQL
sudo systemctl start postgresql

# Mosquitto
sudo systemctl start mosquitto

# Redis
redis-server --daemonize yes
```

### Backend Django

```bash
cd health
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Frontend React

```bash
cd health/nursing_react
npm install
npm run dev
```

### Configuración de settings.py

Para desarrollo local:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'healthdb',
        'USER': 'postgres',
        'PASSWORD': 'your-password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('localhost', 6379)],
        },
    }
}
```

### Simulación de Llamadas

Para pruebas sin hardware, accede a:
```
http://localhost:8000/nursing/rooms
```

---

## API REST

La API REST está disponible en `/api/`.

### Autenticación

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/auth/login` | POST | Iniciar sesión (retorna tokens JWT) |
| `/api/auth/register` | POST | Registrar usuario |
| `/api/auth/logout` | POST | Cerrar sesión |
| `/api/auth/refresh` | POST | Refrescar token |

### Recursos

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/rooms` | GET | Obtener habitaciones |
| `/api/app/load` | GET | Carga inicial de la aplicación |
| `/api/events` | GET | Listar todos los eventos |
| `/api/events/{id}` | GET | Ver evento específico |

---

## Uso de la Aplicación

### Acceso

1. Navega a `http://localhost:8000`
2. Inicia sesión con tus credenciales
3. Serás redirigido a `http://localhost:8000/nursing/home`

### Colores de Estado

| Color | Significado |
|-------|-------------|
| Gris | Cama Desocupada |
| Verde | Ocupada, sin llamadas ni tareas pendientes |
| Azul | Tarea pendiente con tiempo cumplido |
| Rojo | Llamada pendiente |
| Violeta | Tarea pendiente + Llamada pendiente |

### Tareas

- **Programación**: Por defecto, 30 minutos desde el momento actual
- **Repetición**: Configurable con frecuencia y fecha de fin
- **Edición**: Click en la tarea para editar. En tareas repetitivas, la edición no afecta otras ocurrencias

#### Marcar Tarea como Cumplida

有两种方式:
1. **Manual**: Ingresa una fecha/hora pasada en "Efectivización de la Tarea" y presiona "Guardar Edición"
2. **Rápido**: Botón "Recién Cumplida" (marca con hora actual)

### Llamadas

- Las llamadas pendientes aparecen en rojo
- Al responder (botón de cancelación), cambian a gris
- Click en la llamada para agregar: motivo, respuesta y responsable
- Botón de cancelación por habitación responde todas las llamadas de esa habitación

### Interfaz

- **Dark Mode** por defecto
- Notificaciones sonoras para llamadas y tareas pendientes
- Registro automático de todas las acciones en la tabla "event"

### Eventos del Sistema

>El sistema registra cada acción realizada ya sea por interfaz de usuario como por el dispositivo de llamada o por el backend al cumplirse el momento de una tarea. El registro consta del estado previo a la acción y el estado resultante de dicha acción.

Para acceder a los eventos del sistema:

1. Navega a `http://localhost:8000/events`
2. Solo usuarios con permisos de superusuario pueden acceder

#### Características

- **Lista de eventos**: Muestra los últimos 100 eventos ordenados por fecha (más reciente primero)
- **Ordenamiento**: Click en las columnas Fecha/Hora, Usuario o Acción para ordenar
- **Búsqueda**: Campo de texto para filtrar eventos por cualquier campo
- **Vista de detalle**: Click en un evento para ver los datos completos
- **Exportación**: Botón "Exportar CSV" para descargar los eventos filtrados
- **Datos Before/After**: Los campos "Antes" y "Después" se muestran separados por punto y coma (;)

#### Formato de Exportación

El archivo CSV exportado contiene las columnas:
- Fecha/Hora
- Usuario
- Acción
- Antes
- Después

>Para el uso en un Centro de Enfermería con una sola computadora, la App permite diferenciar al usuario que inica sesión (Jefe de Enfermería) del que ingresa acciones como *ocupar cama* o *nueva tarea*, etc. 


---

## Configuración de Hardware

### Formato de Datos MQTT

La aplicación espera mensajes en formato JSON:

```json
{"state": true, "id": "12,3", "key": "<CALL_SECRET_KEY>"}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `state` | Boolean | true = llamada, false = cancelación |
| `id` | String | "habitación,cama" (ej: "12,3"). Para cancelación: "12,0" |
| `key` | String | Secreto compartido. **Debe ser idéntico** a `CALL_SECRET_KEY` configurado en el backend. No es un campo de contenido: el backend lo valida contra `settings.CALL_SECRET_KEY` y **rechaza (aborta) cualquier mensaje que no lo tenga**. |

> [!IMPORTANT]
> El valor de `key` es el **mismo** que `CALL_SECRET_KEY` definido en el entorno
> del backend. Configuralo en el firmware del pulsador (p. ej. en `defines.h`)
> con el **mismo valor** y, si se rota, actualizá ambos lados en simultáneo.

### Configuración ESP8266 (NodeMCU)

Edita el archivo `defines.h` para configurar:
- SSID de la red WiFi
- Contraseña WiFi
- IP del servidor

---

## Administración

- **Panel Admin Django**: `http://localhost:8000/admin`
- **Crear Superusuario**:
  ```bash
  cd health
  python manage.py createsuperuser
  ```

---

## Mantenimiento

### Limpieza de Podman

```bash
# Ver uso de espacio
podman system df

# Limpiar contenedores detenidos
podman container prune

# Limpiar imágenes sin usar
podman image prune -a

# Limpiar volúmenes
podman volume prune

# Limpieza completa
podman system prune -a --volumes
```

### Migrar desde Docker

```bash
# Exportar imagen Docker
docker save myimage > myimage.tar

# Importar a Podman
podman load < myimage.tar
```
