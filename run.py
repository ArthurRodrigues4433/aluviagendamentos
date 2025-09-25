#!/usr/bin/env python3
"""
Script para executar o servidor FastAPI.
Resolve problemas de imports relativos quando executado diretamente.
"""

import sys
import os

# Adicionar o diretório src ao path para imports absolutos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src"]
    )