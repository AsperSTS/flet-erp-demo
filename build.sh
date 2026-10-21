#!/bin/bash

# Activar el entorno conda si es necesario (el usuario puede correrlo en su terminal)
# eval "$(conda shell.bash hook)"
# conda activate zyra_312_dev

echo "Compilando Zyra ERP con Nuitka..."

python -m nuitka --standalone \
    --plugin-enable=pylint-warnings \
    --output-dir=build \
    main.py

echo "Compilación completada. Revisa la carpeta build/"
