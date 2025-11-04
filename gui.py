import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
from server import start_proxy_server
import threading
import base64
import json
from auth import load_users
from ttkthemes import ThemedTk
import os
from datetime import datetime

class ProxyGUI:
    def __init__(self):
        self.root = ThemedTk(theme="arc")
        self.root.title("Caching Proxy Server")
        self.root.geometry("1000x700")
        
        self.style = ttk.Style()
        self.style.configure('URL.TEntry', padding=(5, 5)) 
        
        self.style = ttk.Style()

        self.bg_color = "#f7fafc"  
        self.accent_color = "#2563eb"  
        self.card_color = "#ffffff"  
        self.text_color = "#0f1724" 
        self.root.configure(bg=self.bg_color)
        
        self.style.configure('Main.TFrame', background=self.bg_color)
        self.style.configure('Header.TLabel', 
                           font=('Helvetica', 16, 'bold'),
                           padding=10,
                           background=self.bg_color,
                           foreground=self.text_color)
        self.style.configure('Status.TLabel',
                           font=('Helvetica', 10),
                           padding=5,
                           background=self.bg_color,
                           foreground=self.text_color)
        self.style.configure('URL.TEntry', padding=5)
        
        self.server_running = False
        self.server_thread = None
        self.server = None
        self.proxy_port = 3001
        
        self.start_server()
        
        self.login_frame = ttk.Frame(self.root, style='Main.TFrame')
        self.setup_login_frame()
        self.login_frame.pack(fill='both', expand=True)
        
        self.main_frame = ttk.Frame(self.root, style='Main.TFrame')
        self.setup_main_frame()

        self.status_bar = ttk.Label(self.root,
                                  text="Server Status: Starting...",
                                  style='Status.TLabel',
                                  anchor='w')
        self.status_bar.pack(side='bottom', fill='x')
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.update_status()
        
    def toggle_password_visibility(self, entry_widget, button):
        """Toggle password visibility between show and hide"""
        if entry_widget.cget('show') == '':
            entry_widget.configure(show='•')
            button.configure(text='👁')
        else:
            entry_widget.configure(show='')
            button.configure(text='👁️‍🗨️')
    
    def create_password_frame(self, parent, password_var, width=30):
        """Create a password entry with show/hide toggle"""
        container_frame = ttk.Frame(parent, style='Main.TFrame')
        
        password_entry = ttk.Entry(container_frame,
                                 textvariable=password_var,
                                 show="•",
                                 width=width,
                                 style='URL.TEntry')
        password_entry.pack(side='left', expand=True, fill='x')
        
        toggle_btn = ttk.Button(container_frame,
                              text='👁',
                              width=3,
                              command=lambda: self.toggle_password_visibility(password_entry, toggle_btn))
        toggle_btn.pack(side='left', padx=(5, 0))
        
        return container_frame 
    
    def setup_login_frame(self):
        center_frame = ttk.Frame(self.login_frame, style='Main.TFrame')
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        ttk.Label(center_frame, 
                 text="Caching Proxy Server", 
                 style='Header.TLabel').pack(pady=20)
        
        form_frame = ttk.Frame(center_frame, style='Main.TFrame')
        form_frame.pack(padx=40, pady=20)
        
        username_frame = ttk.Frame(form_frame, style='Main.TFrame')
        username_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(username_frame, 
                 text="Username:", 
                 font=('Helvetica', 10)).pack(side='left', pady=5)
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(username_frame, 
                                 textvariable=self.username_var,
                                 width=30,
                                 style='URL.TEntry')
        username_entry.pack(side='right', padx=(10, 0), expand=True, fill='x')
        
        password_label_frame = ttk.Frame(form_frame, style='Main.TFrame')
        password_label_frame.pack(fill='x', pady=(0, 5))
        ttk.Label(password_label_frame, 
                 text="Password:", 
                 font=('Helvetica', 10)).pack(side='left')
                 
        self.password_var = tk.StringVar()
        password_frame = self.create_password_frame(form_frame, self.password_var)
        password_frame.pack(fill='x', pady=(0, 15))
        
        login_btn = ttk.Button(form_frame, 
                              text="Login",
                              command=self.login,
                              style='Accent.TButton')
        login_btn.pack(pady=10, ipadx=20, ipady=5)
        
        self.password_entry = password_frame.winfo_children()[0] 
        
        username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self.login())
        
    def setup_main_frame(self):
        
        self.style.configure('TNotebook', background=self.bg_color)
        self.style.configure('TNotebook.Tab', padding=[12, 4], font=('Helvetica', 10))
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        proxy_frame = ttk.Frame(self.notebook, style='Main.TFrame')
        self.notebook.add(proxy_frame, text='🌐 Proxy')

        ttk.Label(proxy_frame,
                 text="Proxy Server Control",
                 style='Header.TLabel').pack(pady=10)

        control_frame = ttk.Frame(proxy_frame, style='Main.TFrame')
        control_frame.pack(fill='x', padx=20, pady=10)

        left_controls = ttk.Frame(control_frame, style='Main.TFrame')
        left_controls.pack(side='left')

        self.server_btn = ttk.Button(left_controls,
                                   text="Start Server",
                                   command=self.toggle_server,
                                   style='Accent.TButton')
        self.server_btn.pack(side='left', padx=5, ipadx=10, ipady=2)

        self.server_status = ttk.Label(left_controls,
                                     text="●",
                                     foreground='gray',
                                     font=('Helvetica', 16),
                                     style='Status.TLabel')
        self.server_status.pack(side='left', padx=5)

        center_controls = ttk.Frame(control_frame, style='Main.TFrame')
        center_controls.pack(side='left', expand=True, fill='both')

        self.user_info = ttk.Label(center_controls,
                                text="Not Logged In",
                                font=('Helvetica', 12, 'bold'),
                                anchor='center',
                                style='Info.TLabel')
        self.user_info.pack(expand=True)

        right_controls = ttk.Frame(control_frame, style='Main.TFrame')
        right_controls.pack(side='right')

        self.logout_btn = ttk.Button(right_controls,
                                   text="Logout",
                                   command=self.logout,
                                   style='Accent.TButton')
        self.logout_btn.pack(side='right', padx=5, ipadx=10, ipady=2)

        main_content = ttk.Frame(proxy_frame, style='Main.TFrame')
        main_content.pack(fill='both', expand=True, padx=20, pady=10)

        left_column = ttk.Frame(main_content, style='Main.TFrame')
        left_column.pack(side='left', fill='both', expand=True)

        right_column = ttk.Frame(main_content, style='Main.TFrame')
        right_column.pack(side='right', fill='y')

        url_frame = ttk.Frame(left_column, style='Main.TFrame')
        url_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(url_frame,
                 text="URL:",
                 font=('Helvetica', 10)).pack(side='left', padx=5)
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(url_frame,
                            textvariable=self.url_var,
                            style='URL.TEntry')
        url_entry.pack(side='left', fill='x', expand=True, padx=5)

        send_btn = ttk.Button(url_frame,
                            text="Send Request",
                            command=self.send_request,
                            style='Accent.TButton')
        send_btn.pack(side='left', padx=5, ipadx=10, ipady=2)

        response_frame = ttk.Frame(left_column, style='Main.TFrame')
        response_frame.pack(fill='both', expand=True)

        ttk.Label(response_frame,
                 text="Response:",
                 font=('Helvetica', 10)).pack(anchor='w', pady=5)

        top_badge_frame = ttk.Frame(response_frame, style='Main.TFrame')
        top_badge_frame.pack(fill='x', pady=(0, 8))

        self.cache_status_var = tk.StringVar(value="Cache: -")
        self.cache_status_label = ttk.Label(top_badge_frame, textvariable=self.cache_status_var, font=('Helvetica', 10, 'bold'))
        self.cache_status_label.pack(side='left', padx=(0, 10))

        self.blocked_var = tk.StringVar(value="")
        self.blocked_label = ttk.Label(top_badge_frame, textvariable=self.blocked_var, font=('Helvetica', 10, 'bold'))
        self.blocked_label.pack(side='left')

        self.response_area = scrolledtext.ScrolledText(
            response_frame,
            height=20,
            font=('Consolas', 10),
            bg=self.card_color,
            fg=self.text_color,
            insertbackground=self.text_color,
            wrap=tk.WORD
        )
        self.response_area.pack(fill='both', expand=True)

        ttk.Label(right_column, text="Cache", font=('Helvetica', 12, 'bold'), background=self.bg_color, foreground=self.text_color).pack(anchor='w', pady=(0, 5))
        self.history_list = tk.Listbox(
            right_column,
            height=12,
            bg=self.card_color,
            fg=self.text_color,
            selectbackground=self.accent_color,
            selectforeground='white',
            highlightthickness=1,
            relief='solid'
        )
        self.history_list.pack(fill='both', padx=(0, 10), pady=(0, 10))
        self.history_list.bind('<Double-Button-1>', lambda e: self.load_selected_history())

        ttk.Label(right_column, text='Analytics', font=('Helvetica', 12, 'bold'), background=self.bg_color, foreground=self.text_color).pack(anchor='w')
        self.analytics_frame = ttk.Frame(right_column, style='Main.TFrame')
        self.analytics_frame.pack(fill='x', pady=(5, 10))

        self.requests_var = tk.StringVar(value='Requests: 0')
        self.hits_var = tk.StringVar(value='Cache Hits: 0')
        self.misses_var = tk.StringVar(value='Cache Misses: 0')

        ttk.Label(self.analytics_frame, textvariable=self.requests_var, background=self.bg_color, foreground=self.text_color).pack(anchor='w')
        ttk.Label(self.analytics_frame, textvariable=self.hits_var, background=self.bg_color, foreground=self.text_color).pack(anchor='w')
        ttk.Label(self.analytics_frame, textvariable=self.misses_var, background=self.bg_color, foreground=self.text_color).pack(anchor='w')

        self.clear_cache_btn = ttk.Button(right_column, text='Clear Cache', command=self.clear_cache, style='Accent.TButton')
        self.clear_cache_btn.pack(fill='x', pady=(10, 0), padx=(0, 10))
        self.clear_cache_btn.configure(state='disabled')

        self.admin_frame = ttk.Frame(self.notebook, style='Main.TFrame')
        self.setup_admin_frame()

        url_entry.bind('<Return>', lambda e: self.send_request())

    def add_to_history(self, url):
        username = getattr(self, 'current_username', None)
        if not hasattr(self, 'user_histories'):
            self.user_histories = {}
        if username not in self.user_histories:
            self.user_histories[username] = []
        history = self.user_histories[username]
        if url in history:
            history.remove(url)
        history.insert(0, url)
        self.user_histories[username] = history[:50]
        self.history_list.delete(0, tk.END)
        for u in self.user_histories[username]:
            self.history_list.insert(tk.END, u)

    def load_selected_history(self):
        sel = self.history_list.curselection()
        if not sel:
            return
        url = self.history_list.get(sel[0])
        self.url_var.set(url)
        self.send_request()

    def clear_cache(self):
        try:
            self.clear_cache_btn.configure(state='disabled')
            self.status_bar.configure(text="Clearing cache...")
            resp = requests.post(
                f"http://localhost:{self.proxy_port}/clear_cache",
                headers={"Authorization": self.auth_header},
                timeout=5
            )
            if resp.status_code == 200:
                try:
                    js = resp.json()
                    before = js.get('before')
                    after = js.get('after')
                    messagebox.showinfo("Success", f"Cache cleared successfully (before={before}, after={after})")
                except Exception:
                    messagebox.showinfo("Success", "Cache cleared successfully")
                self.refresh_analytics()
                self.cache_status_var.set("Cache: -")
                
                username = getattr(self, 'current_username', None)
                if hasattr(self, 'user_histories') and username in self.user_histories:
                    self.user_histories[username] = []
                    self.history_list.delete(0, tk.END)
            else:
                try:
                    body = resp.text
                except Exception:
                    body = ''
                messagebox.showerror("Error", f"Failed to clear cache: {resp.status_code} {body}")
        except requests.exceptions.Timeout:
            messagebox.showerror("Error", "Clear cache request timed out")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Error", "Failed to connect to proxy server")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {e}")
        finally:
            try:
                self.clear_cache_btn.configure(state='normal')
            except Exception:
                pass
            self.update_status()

    def refresh_analytics(self):
        
        try:
            resp = requests.get(f"http://localhost:{self.proxy_port}/cache_stats", headers={"Authorization": self.auth_header})
            if resp.status_code == 200:
                js = resp.json()
                an = js.get('analytics', {})
                self.requests_var.set(f"Requests: {an.get('requests', 0)}")
                self.hits_var.set(f"Cache Hits: {an.get('cache_hits', 0)}")
                self.misses_var.set(f"Cache Misses: {an.get('cache_misses', 0)}")
        except Exception:
            
            pass
        
    def login(self):
        username = self.username_var.get()
        password = self.password_var.get()
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        auth_string = f"{username}:{password}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        if not self.server_running:
            if not self.start_server():
                return
        try:
            response = requests.get(
                f"http://localhost:{self.proxy_port}/analytics",
                headers={"Authorization": f"Basic {auth_b64}"}
            )
            if response.status_code == 200:
                users_db = load_users()
                user = users_db.get(username)
                self.login_frame.pack_forget()
                self.main_frame.pack(fill='both', expand=True)
                self.auth_header = f"Basic {auth_b64}"
                self.server_btn.config(text="Stop Server")
                self.current_user_role = user.get("role") if user else None
                self.current_username = username
                if hasattr(self, 'user_info'):
                    self.user_info.config(text=f"{self.current_username} – {self.current_user_role}")
                if user and user.get("role") == "Admin":
                    self.notebook.add(self.admin_frame, text='User Management')
                    self.refresh_user_list()
                try:
                    self.clear_cache_btn.configure(state='normal')
                except Exception:
                    pass
                try:
                    self.refresh_analytics()
                except Exception:
                    pass
               
                if hasattr(self, 'user_histories') and username in self.user_histories:
                    self.history_list.delete(0, tk.END)
                    for u in self.user_histories[username]:
                        self.history_list.insert(tk.END, u)
            else:
                messagebox.showerror("Error", "Invalid credentials")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Error", "Failed to connect to server. Please try again.")
    
    def start_server(self):
        if not self.server_running:
            try:
                import uvicorn
                import asyncio
                
                def run_server():
                    config = uvicorn.Config(app="server:app", host="0.0.0.0", port=self.proxy_port)
                    self.server = start_proxy_server(self.proxy_port, config)
                    
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    loop.run_until_complete(self.server.serve())
                    loop.close()
                
                self.server_thread = threading.Thread(target=run_server)
                self.server_thread.daemon = True
                self.server_thread.start()
                self.server_running = True
                
                import time
                time.sleep(2)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start server: {str(e)}")
                return False
        return True

    def stop_server(self):
        if self.server_running and self.server:
            try:
                self.server.should_exit = True
                self.server_running = False
                self.server = None
                
                import time
                time.sleep(1)
                return True
            except Exception as e:
                messagebox.showerror("Error", f"Failed to stop server: {str(e)}")
                return False
        return True

    def toggle_server(self):
        if not self.server_running:
            if self.start_server():
                self.server_btn.config(text="Stop Server")
                messagebox.showinfo("Success", f"Server started on port {self.proxy_port}")
        else:
            if self.stop_server():
                self.server_btn.config(text="Start Server")
                messagebox.showinfo("Success", "Server stopped successfully")
    
    def logout(self):
        """Handle user logout"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            
            self.auth_header = None
            self.username_var.set("")
            self.password_var.set("")
            self.current_username = None
            
            if hasattr(self, 'user_info'):
                self.user_info.config(text="Not Logged In")
            
            if hasattr(self, 'admin_frame'):
                for i in range(len(self.notebook.tabs())):
                    if self.notebook.tab(i, "text") == "User Management":
                        self.notebook.forget(i)
                        break

            self.main_frame.pack_forget()
            self.login_frame.pack(fill='both', expand=True)
           
            self.response_area.delete(1.0, tk.END)
            self.url_var.set("")
            
            self.history_list.delete(0, tk.END)
    
    def normalize_url(self, url):
        """Add protocol if missing"""
        if not url:
            return url
        if not url.startswith(('http://', 'https://')):
            return f'https://{url}'
        return url
    
    def send_request(self):
        url = self.url_var.get()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
        
        url = self.normalize_url(url)
        self.url_var.set(url)
        try:
            response = requests.get(
                f"http://localhost:{self.proxy_port}/?url={url}",
                headers={"Authorization": self.auth_header}
            )
            
            self.blocked_var.set("")
            self.blocked_label.configure(foreground=self.text_color)
            
            cache_header = response.headers.get('X-Cache')
            if cache_header:
                self.cache_status_var.set(f"Cache: {cache_header}")
                if cache_header.upper() == 'HIT':
                    self.cache_status_label.configure(foreground='#2ecc71')  # green
                else:
                    self.cache_status_label.configure(foreground=self.accent_color)
            else:
                self.cache_status_var.set("Cache: -")
                self.cache_status_label.configure(foreground=self.text_color)
           
            if response.status_code == 403:
                try:
                    js = response.json()
                    reason = js.get('reason') or js.get('error') or 'Access Denied'
                    blocked_url = js.get('blocked_url', url)
                    self.blocked_var.set(f"ACCESS DENIED: {blocked_url} — {reason}")
                    self.blocked_label.configure(foreground='#ff4d4f')
                    self.update_response_area("", clear=True)
                    return
                except Exception:
                    pass
            if response.status_code == 200:
                self.update_response_area(response.text)
                try:
                    self.add_to_history(url)
                except Exception:
                    pass
                try:
                    self.refresh_analytics()
                except Exception:
                    pass
            else:
                self.update_response_area(
                    f"Error {response.status_code}: {response.text}",
                    error=True
                )
        except requests.exceptions.ConnectionError:
            self.update_response_area(
                "Error: Failed to connect to proxy server",
                error=True
            )
    
    def setup_admin_frame(self):
        
        ttk.Label(self.admin_frame, 
                 text="User Management", 
                 style='Header.TLabel').pack(pady=10)
        
        content_frame = ttk.Frame(self.admin_frame, style='Main.TFrame')
        content_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        list_frame = ttk.Frame(content_frame, style='Main.TFrame')
        list_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        list_header = ttk.Frame(list_frame, style='Main.TFrame')
        list_header.pack(fill='x', pady=(0, 5))
        
        ttk.Label(list_header, 
                 text="Users", 
                 font=('Helvetica', 12, 'bold')).pack(side='left')
        
        ttk.Button(list_header,
                  text="🔄 Refresh",
                  command=self.refresh_user_list,
                  style='Accent.TButton').pack(side='right')
        
        self.style.configure('Custom.Treeview',
                           font=('Helvetica', 10),
                           rowheight=25)
        self.style.configure('Custom.Treeview.Heading',
                           font=('Helvetica', 10, 'bold'))
        
        self.user_list = ttk.Treeview(list_frame,
                                     columns=('Username', 'Role'),
                                     show='headings',
                                     height=12,
                                     style='Custom.Treeview')
        
        self.user_list.heading('Username', text='Username')
        self.user_list.heading('Role', text='Role')
        self.user_list.column('Username', width=150)
        self.user_list.column('Role', width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.user_list.yview)
        self.user_list.configure(yscrollcommand=scrollbar.set)
        
        self.user_list.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        form_frame = ttk.Frame(content_frame, style='Main.TFrame')
        form_frame.pack(side='right', fill='y', padx=(10, 0))
        
        ttk.Label(form_frame,
                 text="Add New User",
                 font=('Helvetica', 12, 'bold')).pack(pady=(0, 20))
        
        ttk.Label(form_frame,
                 text="Username:",
                 font=('Helvetica', 10)).pack(anchor='w', pady=(0, 5))
        self.new_username = tk.StringVar()
        ttk.Entry(form_frame,
                 textvariable=self.new_username,
                 width=25,
                 style='URL.TEntry').pack(fill='x', pady=(0, 15))
        
        ttk.Label(form_frame,
                 text="Password:",
                 font=('Helvetica', 10)).pack(anchor='w', pady=(0, 5))
        self.new_password = tk.StringVar()
        password_frame = self.create_password_frame(form_frame, self.new_password, width=25)
        password_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(form_frame,
                 text="Role:",
                 font=('Helvetica', 10)).pack(anchor='w', pady=(0, 5))
        self.new_role = tk.StringVar(value="Student")
        role_combo = ttk.Combobox(form_frame,
                                textvariable=self.new_role,
                                values=["Admin", "Student", "Faculty"],
                                state='readonly',
                                width=23)
        role_combo.pack(fill='x', pady=(0, 20))
        
        ttk.Button(form_frame,
                  text="Add User",
                  command=self.add_user,
                  style='Accent.TButton').pack(fill='x', ipady=5)

    def refresh_user_list(self):
        
        for item in self.user_list.get_children():
            self.user_list.delete(item)
        
        users_db = load_users()
        for username, user in users_db.items():
            self.user_list.insert('', 'end', values=(username, user.get('role', 'Student')))

    def add_user(self):
        username = self.new_username.get()
        password = self.new_password.get()
        role = self.new_role.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return
            
        try:
           
            with open("users.json", "r") as f:
                data = json.load(f)
            
            if any(u["username"] == username for u in data["users"]):
                messagebox.showerror("Error", "Username already exists")
                return
            
            data["users"].append({
                "username": username,
                "password": password,
                "role": role
            })
            
            with open("users.json", "w") as f:
                json.dump(data, f, indent=2)
            
            self.new_username.set("")
            self.new_password.set("")
            self.new_role.set("Student")
            
            self.refresh_user_list()
            messagebox.showinfo("Success", "User added successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add user: {str(e)}")

    def on_closing(self):
        """Handle window closing event"""
        if self.server_running:
            self.stop_server()
        self.root.destroy()

    def update_status(self):
        """Update the status bar with current information"""
        if self.server_running:
            status = f"Server Status: Running on port {self.proxy_port} • "
            self.server_status.configure(foreground='green')
        else:
            status = "Server Status: Stopped • "
            self.server_status.configure(foreground='red')
         
        status += datetime.now().strftime("%H:%M:%S")
        self.status_bar.configure(text=status)
        
        self.root.after(1000, self.update_status)
        
        self.root.after(5000, self.refresh_analytics)
    
    def update_response_area(self, text, error=False, clear=False):
        """Update response area with formatted text"""
        if clear:
            self.response_area.delete(1.0, tk.END)
            return

        self.response_area.delete(1.0, tk.END)
    
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.response_area.insert(tk.END, f"[{timestamp}]\n", "timestamp")
        
        if error:
            self.response_area.tag_configure("error", foreground="#ff6b6b")
            self.response_area.insert(tk.END, text, "error")
        else:
            self.response_area.insert(tk.END, text)
            
        self.response_area.see(tk.END)
    
    def run(self):
        self.response_area.tag_configure("timestamp", foreground="#9fb3ff")
        self.root.mainloop()

if __name__ == "__main__":
    app = ProxyGUI()
    app.run()