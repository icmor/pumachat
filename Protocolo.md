Protocolo para el chat
======================

Mensajes que reciben el servidor y el cliente
---------------------------------------------

# `ERROR`, `WARNING` e `INFO`

Mensajes de error, advertencia e información

```
{ "type": "ERROR",
  "message": "Mensaje de error" }
```

```
{ "type": "WARNING",
  "message": "Mensaje de advertencia" }
```

```
{ "type": "INFO",
  "message": "Mensaje de información" }
```

Los tres mensajes *pueden* (no es obligatorio) tener una llave `"operation"` con
un mensaje y dependiendo de la operación puede haber más llaves extras; por
ejemplo, si el servidor recibe un mensaje tipo `IDENTIFY`, pero el nombre de
usuario ya está siendo utilizado, entonces el servidor responderá:

```
{ "type": "WARNING",
  "message": "El usuario 'Kimberly' ya existe",
  "operation": "IDENTIFY",
  "username": "Kimberly" }
```

En este ejemplo la llave extra es `"username"`.

Mensajes que recibe el servidor
-------------------------------

# `IDENTIFY`

Identifica a un usuario en el servidor:

```
{ "type": "IDENTIFY",
  "username": "Kimberly" }
```

En caso de éxito el servidor responde:

```
{ "type": "INFO",
  "message": "success",
  "operation": "IDENTIFY" }
```

y además manda el mensaje `NEW_USER` a los demás clientes conectados:

```
{ "type": "NEW_USER",
  "username": "Kimberly" }
```

Si el nombre de usuario ya está siendo usado el servidor responde:

```
{ "type": "WARNING",
  "message": "El usuario 'Kimberly' ya existe",
  "operation": "IDENTIFY",
  "username": "Kimberly" }
```

# `STATUS`

Cambia el estado de un usuario:

```
{ "type": "STATUS",
  "status": "AWAY" }
```

Si el estado cambia exitosamente, el servidor responde:

```
{ "type": "INFO",
  "message": "success",
  "operation": "STATUS" }
```

y además manda el mensaje `NEW_STATUS` a los demás clientes conectados:

```
{ "type": "NEW_STATUS",
  "username": "Kimberly",
  "status": "AWAY" }
```

Si el estado especificado es el que tiene el usuario, el servidor responde:

```
{ "type": "WARNING",
  "message": "El estado ya es 'AWAY'",
  "operation": "STATUS",
  "status": "AWAY" }
```

# `USERS`

Regresa la lista de usuarios en el chat:

```
{ "type": "USERS" }
```

El servidor responde:

```
{ "type": "USER_LIST",
  "usernames": [ "Kimberly", "Luis", "Fernando", "Antonio" ] }
```

# `MESSAGE`

Manda un mensaje privado a un usuario:

```
{ "type": "MESSAGE",
  "username": "Luis",
  "message": "Hola Luis, ¿cómo estás?" }
```

Si el usuario destinatario existe el servidor no responde nada y envía el
mensaje al usuario:

```
{ "type": "MESSAGE_FROM",
  "username": "Kimberly",
  "message": "Hola Luis, ¿cómo estás?" }
```

Si el usuario destinatario no existe, el servidor responde:

```
{ "type": "WARNING",
  "message": "El usuario 'Luis' no existe",
  "operation": "MESSAGE",
  "username": "Luis" }
```

# `PUBLIC_MESSAGE`

Manda un mensaje público a todos los usuarios conectados:

```
{ "type": "PUBLIC_MESSAGE",
  "message": "¡Hola a todos!" }
```

El servidor no responde nada y se envía el mensaje a los demás usuarios en el
chat:

```
{ "type": "PUBLIC_MESSAGE_FROM",
  "username": "Kimberly",
  "message": "¡Hola todos!" }
```

# `NEW_ROOM`

Crea un cuarto en el chat:

```
{ "type": "NEW_ROOM",
  "roomname": "Sala 1" }
```

Si el cuarto se crea exitosamente el servidor responde:

```
{ "type": "INFO",
  "message": "success",
  "operation": "NEW_ROOM",
  "roomname": "Sala 1"}
```

Además, el usuario que crea el cuarto es el primero y único en el mismo
inmediatamente después.

Si el nombre del cuarto ya existe, el servidor responde:

```
{ "type": "WARNING",
  "message": "El cuarto 'Sala 1' ya existe",
  "operation": "NEW_ROOM",
  "roomname": "Sala 1" }
```

# `INVITE`

Invita a uno o múltiples usuarios a un cuarto; únicamente usuarios en un cuarto
pueden invitar a otros usuarios a ese cuarto:

```
{ "type": "INVITE",
  "roomname": "Sala 1",
  "usernames": [ "Luis", "Antonio", "Fernando" ] }
```

El cuarto y todos los usuarios deben existir, en cuyo caso el servidor responde:

```
{ "type": "INFO",
  "message": "success",
  "operation": "INVITE",
  "roomname": "Sala 1" }
```

Además de enviar un mensaje de invitación a cada usuario en la lista:

```
{ "type": "INVITATION",
  "message": "Kimberly te invita al cuarto 'Sala 1'",
  "username" "Kimberly",
  "roomname": "Sala 1" }
```

Si el cuarto no existe, el servidor responde:

```
{ "type": "WARNING",
  "message": "El cuarto 'Sala 1' no existe",
  "operation": "INVITE",
  "roomname": "Sala 1" }
```

Si alguno de los usuarios no existe, el servidor responde:

```
{ "type": "WARNING",
  "message": "El usuario 'Fernando' no existe",
  "operation": "INVITE",
  "username": "Fernando" }
```

# `JOIN_ROOM`

Se une a un cuarto; el usuario debió previamente ser invitado al mismo para
poder unirse:

```
{ "type": "JOIN_ROOM",
  "roomname": "Sala 1" }
```

Si el cuarto existe y el usuario fue invitado previamente al mismo, el servidor
responde:

```
{ "type": "INFO",
  "message": "success",
  "operation": "JOIN_ROOM",
  "roomname": "Sala 1" }
```

Además el usuario se une al cuarto y el servidor envía el siguiente mensaje a
todos los usuarios en el cuarto:

```
{ "type": "JOINED_ROOM",
  "roomname": "Sala 1",
  "username": "Fernando" }
```

Si el cuarto no existe el servidor responde:

```
{ "type": "WARNING",
  "message": "El cuarto 'Sala 1' no existe",
  "operation": "JOIN_ROOM",
  "roomname": "Sala 1" }
```

Si el usuario no fue invitado previamente al cuarto, el servidor responde:

```
{ "type": "WARNING",
  "message": "El usuario no ha sido invitado al cuarto 'Sala 1'",
  "operation": "JOIN_ROOM",
  "roomname": "Sala 1" }
```

Si el usuario ya se unió al cuarto el servidor responde:

```
{ "type": "WARNING",
  "message": "El usuario ya se unió al cuarto 'Sala 1'",
  "operation": "JOIN_ROOM",
  "roomname": "Sala 1" }
```

# `ROOM_USERS`

```
{ "type": "ROOM_USERS",
  "roomname": "Sala 1" }
```

Si el cuarto existe y el usuario se ha unido al mismo, el servidor responde:

```
{ "type": "ROOM_USER_LIST",
  "usernames": [ "Kimberly", "Luis", "Antonio", "Fernando" ] }
```

Si el cuarto no existe el servidor responde:

```
{ "type": "WARNING",
  "message": "El cuarto 'Sala 1' no existe",
  "operation": "ROOM_USERS",
  "roomname": "Sala 1" }
```

Si el cuarto existe pero el usuario no ha sido invitado, o ha sido invitado pero
no se ha unido, el servidor responde:

```
{ "type": "WARNING",
  "message": "El usuario no se ha unido al cuarto 'Sala 1'",
  "operation": "ROOM_USERS",
  "roomname": "Sala 1" }
```

# `ROOM_MESSAGE`

Manda un mensaje a un cuarto.

```
{ "type": "ROOM_MESSAGE",
  "roomname": "Sala 1",
  "message": "¡Hola sala 1!" }
```

Si el cuarto existe y el usuario se ha unido al mismo, el servidor no responde
nada y envía el mensaje a todos los demás usuarios en el cuarto:

```
{ "type": "ROOM_MESSAGE_FROM",
  "roomname": "Sala 1",
  "username": "Kimberly",
  "message": "¡Hola sala 1!" }
```

Si el cuarto no existe el servidor responde:

```
{ "type": "WARNING",
  "message": "El cuarto 'Sala 1' no existe",
  "operation": "ROOM_MESSAGE",
  "roomname": "Sala 1" }
```

Si el cuarto existe pero el usuario no ha sido invitado, o ha sido invitado pero
no se ha unido, el servidor responde:

```
{ "type": "WARNING",
  "message": "El usuario no se ha unido al cuarto 'Sala 1'",
  "operation": "ROOM_MESSAGE",
  "roomname": "Sala 1" }
```

# `LEAVE_ROOM`

El usuario abandona un cuarto:

```
{ "type": "LEAVE_ROOM",
  "roomname": "Sala 1" }
```

Si el cuarto existe y el usuario se ha unido al mismo, el servidor responde:

```
{ "type": "INFO",
  "message": "success",
  "operation": "LEAVE_ROOM",
  "roomname": "Sala 1" }
```

Además el servidor envía el siguiente mensaje a los demás usuarios en el cuarto:

```
{ "type": "LEFT_ROOM",
  "roomname": "Sala 1",
  "username": "Fernando" }
```

Si el cuarto no existe el servidor responde:

```
{ "type": "WARNING",
  "message": "El cuarto 'Sala 1' no existe",
  "operation": "LEAVE_ROOM",
  "roomname": "Sala 1" }
```

Si el cuarto existe pero el usuario no ha sido invitado, o ha sido invitado pero
no se ha unido, el servidor responde:

```
{ "type": "WARNING",
  "message": "El usuario no se ha unido al cuarto 'Sala 1'",
  "operation": "LEAVE_ROOM",
  "roomname": "Sala 1" }
```

# `DISCONNECT`

Desconecta al usuario del chat, incluyendo abandonar todos los cuartos donde se
haya unido.

```
{ "type": "DISCONNECT" }
```

El servidor no responde nada y envía el siguiente mensaje a todos los usuarios
conectados:

```
{ "type": "DISCONNECTED",
  "username": "Luis" }
```

Además, si el usuario se había unido a cuartos, envía el siguiente mensaje a
cada cuarto:

```
{ "type": "LEFT_ROOM",
  "roomname": "Sala 1",
  "username": "Fernando" }
```

Mensajes que recibe el cliente
------------------------------

# `NEW_USER`

Un nuevo usario se conectó e identificó:

```
{ "type": "NEW_USER",
  "username": "Luis" }
```

# `NEW_STATUS`

Un usuario cambió su estado:

```
{ "type": "NEW_STATUS",
  "username": "Kimberly",
  "status": "AWAY" }
```

# `USER_LIST`

En respuesta a `USERS`

```
{ "type": "USER_LIST",
  "usernames": [ "Kimberly", "Luis", "Fernando", "Antonio" ] }
```

# `MESSAGE_FROM`

Recibe un mensaje privado:

```
{ "type": "MESSAGE_FROM",
  "username": "Luis",
  "message": "Hola Kim, bien ¿y tú?" }
```

# `PUBLIC_MESSAGE_FROM`

Recibe un mensaje público:

```
{ "type": "PUBLIC_MESSAGE_FROM",
  "username": "Kimberly",
  "message": "¡Hola todos!" }
```

# `JOINED_ROOM`

Un nuevo usuario se unió a un cuarto:

```
{ "type": "JOINED_ROOM",
  "roomname": "Sala 1",
  "username": "Fernando" }
```

# `ROOM_USER_LIST`

En respuesta a `ROOM_USERS`

```
{ "type": "ROOM_USER_LIST",
  "roomname": "Sala 1",
  "usernames": "Kimberly", "Fernando" }
```

# `ROOM_MESSAGE_FROM`

Recibe un mensaje en un cuarto:

```
{ "type": "ROOM_MESSAGE_FROM",
  "roomname": "Sala 1",
  "username": "Kimberly",
  "message": "¡Bienvenidos a mi sala!" }
```

# `INVITATION`

Recibe una invitación a un cuarto:
```
{ "type": "INVITATION",
  "message": "Kimberly te invita al cuarto 'Sala 1'",
  "username" "Kimberly",
  "roomname": "Sala 1" }
```

# `LEFT_ROOM`

Un usuario abandonó un cuarto:

```
{ "type": "LEFT_ROOM",
  "roomname": "Sala 1",
  "username": "Fernando" }
```

# `DISCONNECTED`

Un usuario se desconectó:

```
{ "type": "DISCONNECTED",
  "username": "Luis" }
```

Notas
-----

Los mensajes presentados son ejemplos; obviamente los nombres de usario, de
cuartos y mensajes particulares serán distintos.

Si un usuario no se ha identificado no puede hacer nada hasta que se
identifique; todo mensaje distinto de `IDENTIFY` se responderá con un error y se
desconectará al cliente.

Si un mensaje es incompleto (por ejemplo, un `MESSAGE` que le falte la llave
`"username"`) se responderá con un error y se desconectará al cliente. Lo mismo
con valores esperados: si un estado no es válido (distinto de `ACTIVE`, `AWAY` y
`BUSY`) se responderá con un error y se desconectará al cliente.

Cuando todos los usuarios de un cuarto lo hayan abandonado, el cuarto
desaparece.

Cualquier mensaje no reconocido (en particular si no es un diccionario JSON) se
responderá con un error y se desconectará al cliente.
