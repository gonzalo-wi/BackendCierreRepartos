#!/usr/bin/env python3
"""
Script de limpieza y mantenimiento de logs
Permite comprimir, archivar y limpiar logs antiguos
"""

import os
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import json

class LogCleaner:
    def __init__(self, base_dir="/home/gonzalo/Documentos/BackendCierreRepartos"):
        self.logs_dir = Path(base_dir) / "logs"
        self.archive_dir = self.logs_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)

    def compress_file(self, source_path, target_path):
        """Comprime un archivo usando gzip"""
        try:
            with open(source_path, 'rb') as f_in:
                with gzip.open(target_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return True
        except Exception as e:
            print(f"❌ Error comprimiendo {source_path}: {e}")
            return False

    def get_file_age_days(self, file_path):
        """Obtiene la antigüedad de un archivo en días"""
        try:
            mtime = os.path.getmtime(file_path)
            file_date = datetime.fromtimestamp(mtime)
            age = datetime.now() - file_date
            return age.days
        except Exception as e:
            print(f"❌ Error obteniendo edad del archivo {file_path}: {e}")
            return 0

    def get_file_size_mb(self, file_path):
        """Obtiene el tamaño de un archivo en MB"""
        try:
            size_bytes = os.path.getsize(file_path)
            return size_bytes / (1024 * 1024)
        except Exception as e:
            print(f"❌ Error obteniendo tamaño del archivo {file_path}: {e}")
            return 0

    def archive_old_logs(self, days_old=7):
        """Archiva logs más antiguos que X días"""
        print(f"📦 Archivando logs más antiguos de {days_old} días...")
        
        archived_count = 0
        total_saved_mb = 0
        
        for log_file in self.logs_dir.glob("*.log*"):
            if log_file.is_file() and not log_file.name.startswith('archive'):
                age = self.get_file_age_days(log_file)
                size_mb = self.get_file_size_mb(log_file)
                
                if age > days_old:
                    # Crear nombre del archivo archivado
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    archived_name = f"{log_file.stem}_{timestamp}.log.gz"
                    archived_path = self.archive_dir / archived_name
                    
                    print(f"  📦 Archivando {log_file.name} ({size_mb:.2f} MB, {age} días)")
                    
                    if self.compress_file(log_file, archived_path):
                        os.remove(log_file)
                        archived_count += 1
                        total_saved_mb += size_mb
                        print(f"    ✅ Archivado como {archived_name}")
                    else:
                        print(f"    ❌ Error archivando {log_file.name}")
        
        print(f"✅ {archived_count} archivos archivados, {total_saved_mb:.2f} MB liberados")

    def clean_old_archives(self, days_old=30):
        """Elimina archivos archivados más antiguos que X días"""
        print(f"🗑️  Limpiando archivos archivados más antiguos de {days_old} días...")
        
        deleted_count = 0
        total_freed_mb = 0
        
        for archive_file in self.archive_dir.glob("*.gz"):
            if archive_file.is_file():
                age = self.get_file_age_days(archive_file)
                size_mb = self.get_file_size_mb(archive_file)
                
                if age > days_old:
                    print(f"  🗑️  Eliminando {archive_file.name} ({size_mb:.2f} MB, {age} días)")
                    try:
                        os.remove(archive_file)
                        deleted_count += 1
                        total_freed_mb += size_mb
                        print(f"    ✅ Eliminado")
                    except Exception as e:
                        print(f"    ❌ Error eliminando: {e}")
        
        print(f"✅ {deleted_count} archivos eliminados, {total_freed_mb:.2f} MB liberados")

    def truncate_large_logs(self, max_size_mb=50):
        """Trunca logs que superen un tamaño específico"""
        print(f"✂️  Truncando logs mayores a {max_size_mb} MB...")
        
        truncated_count = 0
        
        for log_file in self.logs_dir.glob("*.log"):
            if log_file.is_file():
                size_mb = self.get_file_size_mb(log_file)
                
                if size_mb > max_size_mb:
                    print(f"  ✂️  Truncando {log_file.name} ({size_mb:.2f} MB)")
                    
                    try:
                        # Backup del archivo antes de truncar
                        backup_name = f"{log_file.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log.gz"
                        backup_path = self.archive_dir / backup_name
                        
                        if self.compress_file(log_file, backup_path):
                            # Mantener solo las últimas 1000 líneas
                            lines_to_keep = 1000
                            temp_file = log_file.with_suffix('.tmp')
                            
                            # Leer las últimas N líneas
                            with open(log_file, 'r', encoding='utf-8') as f:
                                all_lines = f.readlines()
                                
                            with open(temp_file, 'w', encoding='utf-8') as f:
                                # Escribir header indicando que fue truncado
                                f.write(f"# Log truncado el {datetime.now().isoformat()}\n")
                                f.write(f"# Archivo original respaldado como {backup_name}\n")
                                f.write(f"# Manteniendo últimas {lines_to_keep} líneas\n\n")
                                
                                # Escribir últimas líneas
                                last_lines = all_lines[-lines_to_keep:]
                                f.writelines(last_lines)
                            
                            # Reemplazar archivo original
                            shutil.move(temp_file, log_file)
                            truncated_count += 1
                            
                            new_size_mb = self.get_file_size_mb(log_file)
                            print(f"    ✅ Truncado: {size_mb:.2f} MB → {new_size_mb:.2f} MB")
                            
                    except Exception as e:
                        print(f"    ❌ Error truncando: {e}")
        
        print(f"✅ {truncated_count} archivos truncados")

    def show_cleanup_report(self):
        """Muestra reporte del estado actual de los logs"""
        print("📊 Reporte de logs:")
        print("=" * 50)
        
        # Logs activos
        total_logs_size = 0
        active_logs = 0
        
        print("📄 Logs activos:")
        for log_file in sorted(self.logs_dir.glob("*.log")):
            if log_file.is_file():
                size_mb = self.get_file_size_mb(log_file)
                age_days = self.get_file_age_days(log_file)
                total_logs_size += size_mb
                active_logs += 1
                
                status = ""
                if size_mb > 50:
                    status += "⚠️ GRANDE "
                if age_days > 7:
                    status += "📅 ANTIGUO "
                
                print(f"  {log_file.name}: {size_mb:.2f} MB ({age_days} días) {status}")
        
        print(f"\n📋 Total logs activos: {active_logs} archivos, {total_logs_size:.2f} MB")
        
        # Archives
        total_archives_size = 0
        archives_count = 0
        
        if self.archive_dir.exists():
            print(f"\n📦 Archivos archivados:")
            for archive_file in sorted(self.archive_dir.glob("*.gz")):
                if archive_file.is_file():
                    size_mb = self.get_file_size_mb(archive_file)
                    age_days = self.get_file_age_days(archive_file)
                    total_archives_size += size_mb
                    archives_count += 1
                    
                    status = ""
                    if age_days > 30:
                        status += "🗑️ CANDIDATO A ELIMINAR "
                    
                    print(f"  {archive_file.name}: {size_mb:.2f} MB ({age_days} días) {status}")
            
            print(f"\n📦 Total archivos: {archives_count} archivos, {total_archives_size:.2f} MB")
        
        # Resumen total
        total_size = total_logs_size + total_archives_size
        print(f"\n📈 Espacio total usado por logs: {total_size:.2f} MB")
        
        # Recomendaciones
        print(f"\n💡 Recomendaciones:")
        if total_logs_size > 100:
            print(f"  • Considerar archivar logs (más de 100 MB activos)")
        if total_archives_size > 500:
            print(f"  • Considerar limpiar archivos antiguos (más de 500 MB archivados)")
        if any(self.get_file_size_mb(f) > 50 for f in self.logs_dir.glob("*.log")):
            print(f"  • Hay logs individuales mayores a 50 MB que deberían truncarse")

    def full_maintenance(self, archive_days=7, delete_days=30, max_log_size_mb=50):
        """Ejecuta mantenimiento completo"""
        print("🧹 Ejecutando mantenimiento completo de logs...")
        print("=" * 50)
        
        self.show_cleanup_report()
        print("\n" + "=" * 50)
        
        self.archive_old_logs(archive_days)
        print()
        
        self.clean_old_archives(delete_days)
        print()
        
        self.truncate_large_logs(max_log_size_mb)
        print()
        
        print("🎉 Mantenimiento completado!")
        print("=" * 50)
        self.show_cleanup_report()

def main():
    parser = argparse.ArgumentParser(description='Herramienta de limpieza de logs')
    parser.add_argument('--action', 
                       choices=['report', 'archive', 'clean', 'truncate', 'full'], 
                       default='report',
                       help='Acción a realizar')
    parser.add_argument('--archive-days', type=int, default=7,
                       help='Días para archivar logs antiguos')
    parser.add_argument('--delete-days', type=int, default=30,
                       help='Días para eliminar archivos archivados')
    parser.add_argument('--max-size-mb', type=int, default=50,
                       help='Tamaño máximo de logs en MB antes de truncar')
    
    args = parser.parse_args()
    
    cleaner = LogCleaner()
    
    if args.action == 'report':
        cleaner.show_cleanup_report()
    elif args.action == 'archive':
        cleaner.archive_old_logs(args.archive_days)
    elif args.action == 'clean':
        cleaner.clean_old_archives(args.delete_days)
    elif args.action == 'truncate':
        cleaner.truncate_large_logs(args.max_size_mb)
    elif args.action == 'full':
        cleaner.full_maintenance(args.archive_days, args.delete_days, args.max_size_mb)

if __name__ == "__main__":
    main()
