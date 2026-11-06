# Declaración transparente del uso de IA

- **Herramienta / modelo:** ChatGPT de OpenAI, GPT-6, en sesiones de noviembre de 2026.
- **Tareas asistidas:** interpretación de errores de SPI por GPIO, propuesta de protocolo con CRC, diseño del firmware STM32Cube en PlatformIO, programa C del maestro SPI para Milk-V, servidor web, scripts de instalación UART, dashboard HTML, plantillas de documentación y pruebas.
- **Verificaciones automáticas disponibles:** unit tests de decodificación CRC/encabezados y sintaxis Python/C según registros guardados en el repositorio.
- **Verificación física pendiente:** compilar con el entorno real PlatformIO, confirmar temporización TIM2+ADC+DMA, verificar SPI sobre las placas, medir voltajes reales y confirmar acceso HTTP con Nginx. No declarar «funciona» hasta obtener evidencia.
- **Chats/interacciones:** exportar o adjuntar los enlaces/contenidos autorizados de las conversaciones ChatGPT en carpeta `docs/interacciones_ia/` antes de entregar; describir prompts que originaron módulos o correcciones.
- **Responsabilidad:** los miembros del equipo revisaron/ajustaron el código y son responsables de validar experimentalmente los resultados, no de confiar solo en las salidas de IA.
