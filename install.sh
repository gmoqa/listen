#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/usr/local/bin"
VENV_DIR="$SCRIPT_DIR/venv"

echo "🔧 Instalando comando 'listen'..."

if [ ! -d "$VENV_DIR" ]; then
    echo "⚠️  No se encontró el entorno virtual. Creándolo..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install -r "$SCRIPT_DIR/requirements.txt"
else
    source "$VENV_DIR/bin/activate"
fi

echo "Creando wrapper script en $INSTALL_DIR/listen..."
cat > "$INSTALL_DIR/listen" << EOF
#!/bin/bash
source "$VENV_DIR/bin/activate"
exec python "$SCRIPT_DIR/listen.py" "\$@"
EOF

chmod +x "$INSTALL_DIR/listen"
chmod +x "$SCRIPT_DIR/listen.py"

echo "✅ Comando 'listen' instalado correctamente en $INSTALL_DIR"
echo ""
echo "Ahora puedes usar 'listen' desde cualquier directorio"
echo ""
echo "Uso:"
echo "  listen              # Grabar y transcribir en español"
echo "  listen -l en        # Grabar y transcribir en inglés"
echo "  listen -m medium    # Usar modelo más preciso"
echo ""
echo "Presiona ESPACIO para detener la grabación"
