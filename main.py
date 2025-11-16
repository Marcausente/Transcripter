import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import os
import sys
import subprocess
import glob

try:
    import whisper
except ImportError:
    messagebox.showerror("Error", "Por favor instala whisper: pip install openai-whisper")
    sys.exit(1)

def find_ffmpeg():
    """Busca ffmpeg en ubicaciones comunes de Windows"""
    # Primero intentar con el PATH normal
    try:
        subprocess.run(["ffmpeg", "-version"], 
                     capture_output=True, 
                     check=True,
                     creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Buscar en ubicaciones comunes de Windows
    if sys.platform == "win32":
        search_paths = [
            os.path.expanduser("~\\AppData\\Local\\Microsoft\\WinGet\\Packages"),
            os.path.expanduser("~\\AppData\\Local\\Programs"),
            "C:\\Program Files",
            "C:\\Program Files (x86)",
        ]
        
        for base_path in search_paths:
            if os.path.exists(base_path):
                # Buscar recursivamente ffmpeg.exe
                pattern = os.path.join(base_path, "**", "ffmpeg.exe")
                matches = glob.glob(pattern, recursive=True)
                if matches:
                    ffmpeg_path = os.path.dirname(matches[0])
                    # Agregar al PATH temporalmente
                    os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ.get("PATH", "")
                    try:
                        subprocess.run(["ffmpeg", "-version"], 
                                     capture_output=True, 
                                     check=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                        return True
                    except:
                        pass
    
    return False

class TranscripterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Transcripter - Transcribir Audio a Texto")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Variables
        self.audio_file = None
        self.model = None
        self.transcribing = False
        
        # Verificar ffmpeg
        self.check_ffmpeg()
        
        # Crear interfaz
        self.create_widgets()
        
    def check_ffmpeg(self):
        """Verifica si ffmpeg está disponible y lo busca si no está en PATH"""
        if find_ffmpeg():
            return  # FFmpeg encontrado, todo bien
        
        # Si no se encontró, mostrar advertencia pero permitir continuar
        # (puede que funcione de todas formas si Whisper tiene su propia forma de procesar)
        messagebox.showwarning(
            "FFmpeg no encontrado",
            "FFmpeg no está en el PATH del sistema.\n\n"
            "La aplicación intentará buscar FFmpeg automáticamente.\n"
            "Si aún así hay problemas, puedes:\n\n"
            "1. Reiniciar la aplicación (para recargar el PATH)\n"
            "2. O instalar FFmpeg manualmente:\n"
            "   - winget install ffmpeg\n"
            "   - O descarga desde: https://ffmpeg.org/download.html\n\n"
            "Puedes continuar, pero es posible que la transcripción falle."
        )
        
    def create_widgets(self):
        # Frame superior para controles
        control_frame = tk.Frame(self.root, padx=10, pady=10)
        control_frame.pack(fill=tk.X)
        
        # Botón para seleccionar archivo
        self.select_btn = tk.Button(
            control_frame,
            text="Seleccionar archivo MP3",
            command=self.select_file,
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=5
        )
        self.select_btn.pack(side=tk.LEFT, padx=5)
        
        # Botón para transcribir
        self.transcribe_btn = tk.Button(
            control_frame,
            text="Transcribir",
            command=self.start_transcription,
            font=("Arial", 12),
            bg="#2196F3",
            fg="white",
            padx=20,
            pady=5,
            state=tk.DISABLED
        )
        self.transcribe_btn.pack(side=tk.LEFT, padx=5)
        
        # Botón para copiar
        self.copy_btn = tk.Button(
            control_frame,
            text="Copiar al portapapeles",
            command=self.copy_to_clipboard,
            font=("Arial", 12),
            bg="#FF9800",
            fg="white",
            padx=20,
            pady=5,
            state=tk.DISABLED
        )
        self.copy_btn.pack(side=tk.LEFT, padx=5)
        
        # Label para mostrar archivo seleccionado
        self.file_label = tk.Label(
            control_frame,
            text="No hay archivo seleccionado",
            font=("Arial", 10),
            fg="gray"
        )
        self.file_label.pack(side=tk.LEFT, padx=10)
        
        # Separador
        separator = tk.Frame(self.root, height=2, bg="gray")
        separator.pack(fill=tk.X, padx=10, pady=5)
        
        # Área de texto para mostrar transcripción
        text_frame = tk.Frame(self.root, padx=10, pady=10)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_area = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=("Arial", 11),
            bg="white",
            fg="black",
            padx=10,
            pady=10
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        # Barra de estado
        self.status_label = tk.Label(
            self.root,
            text="Listo",
            font=("Arial", 9),
            fg="gray",
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, padx=10, pady=5)
        
    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de audio",
            filetypes=[
                ("Archivos de audio", "*.mp3 *.wav *.m4a *.flac"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if file_path:
            self.audio_file = file_path
            filename = os.path.basename(file_path)
            self.file_label.config(text=f"Archivo: {filename}", fg="black")
            self.transcribe_btn.config(state=tk.NORMAL)
            self.status_label.config(text="Archivo seleccionado. Presiona 'Transcribir' para comenzar.")
            
    def start_transcription(self):
        if not self.audio_file or self.transcribing:
            return
            
        self.transcribing = True
        self.transcribe_btn.config(state=tk.DISABLED)
        self.select_btn.config(state=tk.DISABLED)
        self.text_area.delete(1.0, tk.END)
        self.status_label.config(text="Cargando modelo Whisper... Esto puede tardar unos segundos.")
        
        # Ejecutar transcripción en un hilo separado para no bloquear la UI
        thread = threading.Thread(target=self.transcribe_audio)
        thread.daemon = True
        thread.start()
        
    def transcribe_audio(self):
        try:
            # Buscar FFmpeg antes de comenzar (por si no se encontró al inicio)
            find_ffmpeg()
            
            # Verificar que el archivo existe
            if not os.path.exists(self.audio_file):
                error_msg = f"El archivo no existe: {self.audio_file}"
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
                return
            
            # Cargar modelo (base es un buen balance entre velocidad y precisión)
            if self.model is None:
                self.root.after(0, lambda: self.status_label.config(
                    text="Descargando modelo Whisper 'base' (primera vez)..."
                ))
                self.model = whisper.load_model("base")
            
            self.root.after(0, lambda: self.status_label.config(
                text="Transcribiendo audio... Esto puede tardar varios minutos dependiendo de la duración."
            ))
            
            # Transcribir - usar fp16=False para mejor compatibilidad
            result = self.model.transcribe(
                self.audio_file, 
                language="es",
                fp16=False,
                verbose=False
            )
            text = result["text"].strip()
            
            if not text:
                self.root.after(0, lambda: messagebox.showwarning(
                    "Advertencia", 
                    "No se pudo transcribir el audio. El archivo puede estar corrupto o no contener audio."
                ))
                return
            
            # Actualizar UI en el hilo principal
            self.root.after(0, lambda: self.update_text(text))
            
        except FileNotFoundError as e:
            error_msg = (
                f"Error: No se encontró el archivo o FFmpeg no está instalado.\n\n"
                f"Detalles: {str(e)}\n\n"
                f"Por favor instala FFmpeg:\n"
                f"- winget install ffmpeg\n"
                f"- O descarga desde: https://ffmpeg.org/download.html"
            )
            self.root.after(0, lambda: messagebox.showerror("Error - FFmpeg requerido", error_msg))
            self.root.after(0, lambda: self.status_label.config(text="Error: FFmpeg no encontrado"))
        except Exception as e:
            error_msg = f"Error durante la transcripción:\n\n{str(e)}\n\n"
            if "ffmpeg" in str(e).lower() or "WinError 2" in str(e):
                error_msg += "Solución: Instala FFmpeg con: winget install ffmpeg"
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            self.root.after(0, lambda: self.status_label.config(text="Error durante la transcripción"))
        finally:
            self.transcribing = False
            self.root.after(0, lambda: self.transcribe_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.select_btn.config(state=tk.NORMAL))
            
    def update_text(self, text):
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(1.0, text)
        self.copy_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Transcripción completada. Puedes copiar el texto.")
        
    def copy_to_clipboard(self):
        text = self.text_area.get(1.0, tk.END).strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status_label.config(text="Texto copiado al portapapeles!")
            messagebox.showinfo("Éxito", "Texto copiado al portapapeles")
        else:
            messagebox.showwarning("Advertencia", "No hay texto para copiar")

def main():
    root = tk.Tk()
    app = TranscripterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

