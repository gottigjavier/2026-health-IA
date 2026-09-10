# Health-IA — Sistema de Gestión de Llamadas y Tareas para Internación

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5-092E20?style=flat-square&logo=django&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952B3?style=flat-square&logo=bootstrap&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white)
![MQTT](https://img.shields.io/badge/MQTT-Mosquitto_2-660066?style=flat-square&logo=mqtt&logoColor=white)
![Podman](https://img.shields.io/badge/Podman-6-892CA0?style=flat-square&logo=podman&logoColor=white)

Sistema de administración de llamadas y tareas programadas para el sector de internación de hospitales o clínicas. La aplicación permite gestionar camas, tareas y llamadas desde cualquier punto de la red mediante una interfaz web.

## Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Arquitectura](#arquitectura)
- [Tecnologías](#tecnologías)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Configuración con Podman](#configuración-con-podman)
- [Secretos y Variables de Entorno Obligatorias](#secretos-y-variables-de-entorno-obligatorias)
- [Desarrollo Local](#desarrollo-local)
- [WebSockets (canales en tiempo real)](#websockets-canales-en-tiempo-real)
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
| ------ | ------------- |
| Cableado | Señal completa por cable |
| Mixto | Cable hasta el nodo de habitación, Wi-Fi hasta el servidor |
| Inalámbrico | Placa Wi-Fi integrada en cada pulsador con batería interna |

---

## Arquitectura

### Diagrama interactivo

[**health-architecture.html**](./health-architecture.html) — diagrama SVG autocontenido de la arquitectura completa (componentes, flujos de datos y rutas de tiempo real / MQTT). Abrelo descargando el archivo y abriéndolo en el navegador (GitHub muestra el HTML como código, no lo renderiza como página).

### Vista previa (dark)

![Arquitectura Health-IA — dark](./health-architecture.visual-check.1440x900.dark.png)

Vista previa renderizada de `health-architecture.html` en tema oscuro (1440×900). La versión clara y otras resoluciones están disponibles junto al archivo HTML en el repositorio.

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
| ------ | ------------ |
| Frontend | React 18, Bootstrap, WebSockets |
| Backend | Django 5, Django Ninja (API REST) |
| WebSockets | Django Channels |
| Base de Datos | PostgreSQL 16 |
| Broker Mensajería | Redis, Mosquitto (MQTT over TLS/mTLS) |
| Contenedores | Podman |

> [!WARNING]
> **No subir `redis-py` a la rama 8.x.** El channel layer (`channels_redis
> 4.x`) está escrito y testeado contra `redis-py` 5.x. Con `redis-py` 8.x, el
> `receive()` de los consumers hace `BRPOP` con timeout de 5s y `redis-py` 8
> convierte la respuesta `nil` al expirar en `TimeoutError` (en vez de `None`),
> matando la conexión WebSocket cada ~5s. La restricción `redis>=5.0,<6` está
> fijada en `health/requirements.txt`. Si alguna build la rompe, se reintroduce
> el síntoma de "timeouts de Redis cada 5s".

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
| --------- | ------------- |
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
| ---------- | ------------- | ------------- |
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
- Mosquitto MQTT (puerto 8883, TLS/mTLS)

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
# runserver tiene autoreload, ideal para desarrollo local
python manage.py runserver 0.0.0.0:8000
```

> [!NOTE]
> En el entorno de Podman el servidor corre con **daphne** (ver
> `health/entrypoint.sh`), que **no tiene autoreload**. Para que los cambios
> en código Python (`consumer.py`, vistas, etc.) surtan efecto en el pod hay
> que reiniciarlo:
> `podman restart health-pod-app`. Los templates y estáticos
> (`collectstatic --clear`) se recopilan en el arranque.

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

Para pruebas sin hardware, abre en el navegador:

```
http://localhost:8000/nursing/rooms
```

> [!IMPORTANT]
> El simulador se conecta al WebSocket de llamadas (`/ws/callData/`), que
> **requiere autenticación por JWT**. El token se toma del `access_token`
> guardado en `localStorage` (si ya iniciaste sesión en el board React en el
> mismo navegador) o, si hay una sesión Django autenticada, de un `meta tag`
> generado por el backend. Si no hay token, la conexión se rechaza con el
> código de cierre `4401` y la llamada no llega. Asegurate de haber iniciado
> sesión antes de usar el simulador.

---

## WebSockets (canales en tiempo real)

El backend expone tres canales WebSocket que consumen los componentes React y
el simulador de pulsadores. **Todos requieren un JWT válido** pasado como
parámetro de query string: `ws://host/ws/<canal>/?token=<access_token>`.

| Canal | Ruta | Uso |
| ------- | ------ | ----- |
| App board | `/ws/appData/` | Estado completo de camas, llamadas y tareas |
| Llamadas | `/ws/callData/` | Llamadas de pulsadores (simulador + hardware) |
| Tareas | `/ws/taskData/` | Programación y estado de tareas |

**Autenticación**: el `consumer.py` extrae el token de `?token=` y lo valida
contra la firma JWT del backend (ver `nursing/ws_auth.py`). Si falta o es
inválido, cierra con código `4401`/`4402` respectivamente. El frontend React
maneja esto automáticamente: lee el `access_token` de `localStorage` (el que
guarda `/api/auth/login`) y lo agrega a la URL del socket, con reconexión
automática y refresco de token vía `/api/auth/refresh`.

---

## API REST

La API REST está disponible en `/api/`.

### Autenticación

| Endpoint | Método | Autenticación | Descripción |
| ---------- | -------- | --------------- | ------------- |
| `/api/auth/login` | POST | pública | Iniciar sesión (retorna tokens JWT `access` + `refresh`) |
| `/api/auth/refresh` | POST | pública | Refrescar el token de acceso con el de refresco |
| `/api/auth/register` | POST | JWT | Registrar usuario |
| `/api/auth/logout` | POST | JWT | Cerrar sesión |
| `/api/users/me` | GET | JWT | Datos del usuario autenticado |

### Recursos

| Endpoint | Método | Descripción |
| ---------- | -------- | ------------- |
| `/api/app/load` | GET | Carga inicial de la aplicación (beds, calls, tasks) |
| `/api/rooms` | GET | Obtener habitaciones |
| `/api/beds` | GET | Listar camas |
| `/api/beds` | POST | Crear cama |
| `/api/beds/{id}` | PUT | Actualizar cama |
| `/api/beds/{id}` | GET | Ver cama específica |
| `/api/beds/vacate` | POST | Liberar / desocupar una cama |
| `/api/patients` | GET | Listar pacientes |
| `/api/tasks` | GET | Listar tareas |
| `/api/tasks` | POST | Crear tarea |
| `/api/tasks/{id}` | PUT | Actualizar tarea |
| `/api/tasks/{id}` | GET | Ver tarea específica |
| `/api/tasks/{id}/complete` | POST | Marcar tarea como cumplida |
| `/api/tasks/{id}` | DELETE | Eliminar tarea |
| `/api/calls` | GET | Listar llamadas |
| `/api/calls/{id}/answer` | POST | Responder / cancelar llamada |
| `/api/calls/{id}/close` | POST | Cerrar llamada con motivo/respuesta |
| `/api/events` | GET | Listar eventos del sistema |
| `/api/events/{id}` | GET | Ver evento específico |

---

## Uso de la Aplicación

### Acceso

1. Navega a `http://localhost:8000`
2. Inicia sesión con tus credenciales
3. Serás redirigido a `http://localhost:8000/nursing/home`

### Colores de Estado

| Color | Significado |
| ------- | ------------- |
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

Hay dos formas de marcar una tarea como cumplida:

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
{"state": true, "bed": "12,3", "key": "<CALL_SECRET_KEY>"}
```

| Campo | Tipo | Descripción |
| ------- | ------ | ------------- |
| `state` | Boolean | true = llamada, false = cancelación |
| `bed` | String | "habitación,cama" (ej: "12,3"). Para cancelación: "12,0" |
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

### Cifrado TLS/mTLS para MQTT

> [!NOTE]
> El tráfico MQTT viaja **cifrado con TLS** y autenticado por **certificados
> mutuos (mTLS)**: el broker solo acepta clientes que presenten un certificado
> firmado por la CA del sistema. El listener inseguro (1883) está deshabilitado
> por defecto — el broker escucha únicamente en el puerto **8883** con TLS.

#### Generación de certificados

Las claves se generan ejecutando `health/mosquitto/certs/generate.sh`
(requiere `openssl` instalado):

```bash
cd health/mosquitto/certs
chmod +x generate.sh
./generate.sh
```

El script genera (y **reutiliza** los que ya existen y no expiran en menos de 30 días):

| Archivo | Rol | Vigencia | Detalle |
| --------- | ----- | ---------- | --------- |
| `ca.crt` / `ca.key` | Autoridad Certificadora (CA) | 10 años | Firma todos los certificados del sistema |
| `server.crt` / `server.key` | Certificado del broker Mosquitto | 5 años | RSA 2048, con SAN para `mosquitto`, `localhost`, `127.0.0.1` |
| `client-esp-room1.crt` / `.key` | Certificado de cliente del pulsador ESP8266 | 5 años | **EC P-256** (ver nota abajo) |
| `client-django.crt` / `.key` | Certificado de cliente del backend Django | 5 años | RSA |

> [!IMPORTANT]
> El certificado del ESP8266 usa **EC P-256** y no RSA a propósito: el stack
> secundario de BearSSL (~6 KB) se desborda durante el handshake mTLS al firmar
> con RSA-2048. ECDSA usa mucho menos stack y entra. La CA y el server siguen
> siendo RSA — un cliente EC firmado por una CA RSA es perfectamente válido.

#### Copiado de claves al firmware

Editá `health/mosquitto/HealthMQTTClient/defines.h` y pegá el contenido de los
certificados generados en las variables correspondientes:

| Variable en `defines.h` | Origen |
| -------------------------- | -------- |
| `caCert` | `health/mosquitto/certs/ca.crt` |
| `clientCert` | `health/mosquitto/certs/client-esp-room1.crt` |
| `clientKey` | `health/mosquitto/certs/client-esp-room1.key` |

Cada variable espera el contenido entre `-----BEGIN CERTIFICATE-----` /
`-----END CERTIFICATE-----` (o `-----BEGIN EC PRIVATE KEY-----` /
`-----END EC PRIVATE KEY-----` para `clientKey`), dentro del raw string
`R"EOF( ... )EOF"`. Los placeholders actuales del archivo (`REEMPLAZAR con el
contenido de...`) indican exactamente de dónde sale cada valor.

> [!CAUTION]
> Los archivos `*.key` y `*.crt` de `certs/` ya están en `.gitignore`, pero
> **`defines.h` NO lo está**: una vez que pegás las claves reales, el archivo
> pasa a contener secretos PKI. **Nunca lo commitees con valores reales.** Si
> `clientKey` se filtra, cualquiera puede hacerse pasar por el pulsador de la
> habitación.

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
