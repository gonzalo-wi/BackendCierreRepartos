#!/usr/bin/env python3
"""
Script de monitoreo de logs en tiempo real
Muestra logs de usuario y errores técnicos
"""

import json
import time
import argparse
from pathlib import Path
from datetime import datetime
import subprocess
import sys

class LogMonitor:
    def __init__(self, base_dir="/home/gonzalo/Documentos/BackendCierreRepartos"):
        self.logs_dir = Path(base_dir) / "logs"
        self.user_actions_log = self.logs_dir / "user_actions.log"
        self.technical_errors_log = self.logs_dir / "technical_errors.log"
        self.general_log = self.logs_dir / "application.log"

    def tail_file(self, filepath, lines=10):
        """Obtiene las últimas N líneas de un archivo"""
        try:
            result = subprocess.run(
                ['tail', '-n', str(lines), str(filepath)],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except Exception as e:
            print(f"Error leyendo {filepath}: {e}")
            return []

    def format_json_log(self, line):
        """Formatea una línea de log JSON para mostrar legible"""
        try:
            data = json.loads(line)
            timestamp = data.get('timestamp', 'N/A')
            level = data.get('level', 'INFO')
            action = data.get('action', 'N/A')
            message = data.get('message', 'N/A')
            user_id = data.get('user_id', 'N/A')
            resource = data.get('resource', 'N/A')
            ip = data.get('ip_address', 'N/A')
            
            # Colores para diferentes niveles
            colors = {
                'INFO': '\033[32m',    # Verde
                'WARNING': '\033[33m', # Amarillo
                'ERROR': '\033[31m',   # Rojo
                'DEBUG': '\033[36m',   # Cyan
            }
            reset = '\033[0m'
            color = colors.get(level, '')
            
            return f"{color}[{timestamp}] {level} - {action} - Usuario: {user_id} - Recurso: {resource} - IP: {ip}{reset}\n  📝 {message}"
            
        except json.JSONDecodeError:
            # Si no es JSON, devolver la línea tal como está
            return line
        except Exception as e:
            return f"Error formateando log: {e}"

    def format_simple_log(self, line):
        """Formatea logs simples (no JSON)"""
        return line

    def monitor_user_actions(self, lines=20):
        """Muestra las últimas acciones de usuario"""
        print(f"📊 Últimas {lines} acciones de usuario:")
        print("=" * 80)
        
        if not self.user_actions_log.exists():
            print("❌ Archivo de log de acciones de usuario no encontrado")
            return
            
        log_lines = self.tail_file(self.user_actions_log, lines)
        
        if not log_lines or (len(log_lines) == 1 and not log_lines[0]):
            print("📭 No hay acciones de usuario registradas")
            return
            
        for line in log_lines:
            if line.strip():
                print(self.format_json_log(line))
                print()

    def monitor_technical_errors(self, lines=10):
        """Muestra los últimos errores técnicos"""
        print(f"🚨 Últimos {lines} errores técnicos:")
        print("=" * 80)
        
        if not self.technical_errors_log.exists():
            print("❌ Archivo de log de errores técnicos no encontrado")
            return
            
        log_lines = self.tail_file(self.technical_errors_log, lines)
        
        if not log_lines or (len(log_lines) == 1 and not log_lines[0]):
            print("✅ No hay errores técnicos registrados")
            return
            
        for line in log_lines:
            if line.strip():
                print(self.format_json_log(line))
                print()

    def monitor_general_logs(self, lines=15):
        """Muestra logs generales de la aplicación"""
        print(f"📋 Últimos {lines} logs generales:")
        print("=" * 80)
        
        if not self.general_log.exists():
            print("❌ Archivo de log general no encontrado")
            return
            
        log_lines = self.tail_file(self.general_log, lines)
        
        if not log_lines or (len(log_lines) == 1 and not log_lines[0]):
            print("📭 No hay logs generales")
            return
            
        for line in log_lines:
            if line.strip():
                print(self.format_simple_log(line))

    def watch_logs(self, log_type="all"):
        """Monitoreo en tiempo real de logs"""
        print(f"👀 Monitoreando logs en tiempo real... (Ctrl+C para salir)")
        print("=" * 80)
        
        files_to_watch = []
        if log_type in ["all", "user"]:
            files_to_watch.append(str(self.user_actions_log))
        if log_type in ["all", "errors"]:
            files_to_watch.append(str(self.technical_errors_log))
        if log_type in ["all", "general"]:
            files_to_watch.append(str(self.general_log))
        
        if not files_to_watch:
            print("❌ No hay archivos para monitorear")
            return
            
        try:
            # Usar tail -f para seguimiento en tiempo real
            cmd = ['tail', '-f'] + files_to_watch
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True,
                bufsize=1
            )
            
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    # Determinar si es JSON o texto simple
                    if line.strip().startswith('{'):
                        print(self.format_json_log(line.strip()))
                    else:
                        print(self.format_simple_log(line.strip()))
                    print()
                    
        except KeyboardInterrupt:
            print("\n👋 Monitoreo detenido")
            process.terminate()
        except Exception as e:
            print(f"❌ Error en monitoreo: {e}")

    def show_log_stats(self):
        """Muestra estadísticas de los archivos de log"""
        print("📈 Estadísticas de logs:")
        print("=" * 50)
        
        logs = [
            ("Acciones de usuario", self.user_actions_log),
            ("Errores técnicos", self.technical_errors_log),
            ("Logs generales", self.general_log)
        ]
        
        for name, path in logs:
            if path.exists():
                try:
                    size = path.stat().st_size
                    size_mb = size / (1024 * 1024)
                    
                    # Contar líneas
                    result = subprocess.run(['wc', '-l', str(path)], capture_output=True, text=True)
                    lines = result.stdout.split()[0] if result.returncode == 0 else "N/A"
                    
                    # Última modificación
                    mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    
                    print(f"📄 {name}:")
                    print(f"   Tamaño: {size_mb:.2f} MB")
                    print(f"   Líneas: {lines}")
                    print(f"   Última modificación: {mtime}")
                    print()
                except Exception as e:
                    print(f"❌ Error obteniendo estadísticas de {name}: {e}")
            else:
                print(f"❌ {name}: Archivo no encontrado")
                print()

def main():
    parser = argparse.ArgumentParser(description='Monitor de logs de la aplicación')
    parser.add_argument('--action', choices=['user', 'errors', 'general', 'watch', 'stats'], 
                       default='stats', help='Acción a realizar')
    parser.add_argument('--lines', type=int, default=20, 
                       help='Número de líneas a mostrar')
    parser.add_argument('--watch-type', choices=['all', 'user', 'errors', 'general'], 
                       default='all', help='Tipo de logs a monitorear en tiempo real')
    
    args = parser.parse_args()
    
    monitor = LogMonitor()
    
    if args.action == 'user':
        monitor.monitor_user_actions(args.lines)
    elif args.action == 'errors':
        monitor.monitor_technical_errors(args.lines)
    elif args.action == 'general':
        monitor.monitor_general_logs(args.lines)
    elif args.action == 'watch':
        monitor.watch_logs(args.watch_type)
    elif args.action == 'stats':
        monitor.show_log_stats()
    
    print()

if __name__ == "__main__":
    main()
