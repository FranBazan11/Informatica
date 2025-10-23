#!/bin/bash
# =============================================================
# Script de instalación para el Sistema de Monitoreo
# Autor: Juan Francisco Bazan Carrizo
# =============================================================

echo "=========================================="
echo " Instalación del Sistema de Monitoreo"
echo " de Temperatura - Versión Unificada"
echo "=========================================="
echo ""

# Detectar sistema operativo
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux (probablemente Raspberry Pi)
    echo "✓ Sistema Linux detectado"
    
    # Verificar si es Raspberry Pi
    if [ -f /proc/device-tree/model ]; then
        MODEL=$(cat /proc/device-tree/model)
        if [[ $MODEL == *"Raspberry Pi"* ]]; then
            echo "✓ Raspberry Pi detectada: $MODEL"
            PLATFORM="raspberry"
        else
            echo "✓ Sistema Linux (no Raspberry Pi)"
            PLATFORM="linux"
        fi
    else
        echo "✓ Sistema Linux genérico"
        PLATFORM="linux"
    fi
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "✓ macOS detectado"
    PLATFORM="macos"
    
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "✓ Windows detectado"
    PLATFORM="windows"
else
    echo "⚠ Sistema operativo no reconocido: $OSTYPE"
    PLATFORM="unknown"
fi

echo ""
echo "=========================================="
echo " Instalando dependencias Python"
echo "=========================================="
echo ""

# Función para instalar paquetes Python
install_python_package() {
    PACKAGE=$1
    echo "Instalando $PACKAGE..."
    
    if [[ $PLATFORM == "raspberry" ]]; then
        sudo pip3 install $PACKAGE
    else
        pip3 install $PACKAGE
    fi
    
    if [ $? -eq 0 ]; then
        echo "✓ $PACKAGE instalado correctamente"
    else
        echo "✗ Error al instalar $PACKAGE"
        return 1
    fi
}

# Instalación específica según plataforma
if [[ $PLATFORM == "raspberry" ]]; then
    echo "Instalando para Raspberry Pi..."
    echo ""
    
    # Actualizar sistema
    echo "Actualizando sistema..."
    sudo apt-get update
    
    # Instalar Python y pip si no están
    sudo apt-get install -y python3 python3-pip
    
    # Instalar librerías específicas de Raspberry Pi
    install_python_package "RPi.GPIO"
    install_python_package "spidev"
    
    # Instalar también pyfirmata por si usan Arduino conectado a la Raspberry
    install_python_package "pyfirmata"
    install_python_package "pyserial"
    
    echo ""
    echo "=========================================="
    echo " Configuración de SPI"
    echo "=========================================="
    echo ""
    echo "Para usar el MCP3008, debes habilitar SPI:"
    echo "1. Ejecuta: sudo raspi-config"
    echo "2. Ve a: Interface Options → SPI"
    echo "3. Selecciona: Yes"
    echo "4. Reinicia: sudo reboot"
    echo ""
    echo "Después del reinicio, verifica con: ls /dev/spi*"
    echo ""
    
else
    echo "Instalando para PC (control de Arduino)..."
    echo ""
    
    # Instalar pyfirmata para controlar Arduino
    install_python_package "pyfirmata"
    install_python_package "pyserial"
    
    echo ""
    echo "=========================================="
    echo " Configuración de Arduino"
    echo "=========================================="
    echo ""
    echo "Para usar Arduino con Python:"
    echo "1. Abre Arduino IDE"
    echo "2. Ve a: File → Examples → Firmata → StandardFirmata"
    echo "3. Sube el código a tu Arduino"
    echo "4. Conecta el Arduino via USB"
    echo ""
    
fi

echo ""
echo "=========================================="
echo " Instalación Completa"
echo "=========================================="
echo ""
echo "Para ejecutar el programa:"
echo ""

if [[ $PLATFORM == "raspberry" ]]; then
    echo "  sudo python3 monitoreo_temperatura_unificado.py"
else
    echo "  python3 monitoreo_temperatura_unificado.py"
fi

echo ""
echo "El programa detectará automáticamente el hardware disponible."
echo ""
echo "Consulta GUIA_UNIFICADA.md para más detalles."
echo ""
