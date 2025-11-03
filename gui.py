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
        # Use a modern themed window and custom colors
        self.root = ThemedTk(theme="arc")
        self.root.title("Caching Proxy Server")
        self.root.geometry("1000x700")
        
        # Configure style for entry fields
        self.style = ttk.Style()
        self.style.configure('URL.TEntry', padding=(5, 5))  # Add padding to entries
        
        # Configure colors and styles
        self.style = ttk.Style()
        # Light theme palette
        self.bg_color = "#f7fafc"   # very light gray
        self.accent_color = "#2563eb"  # blue accent
        self.card_color = "#ffffff"  # card white
        self.text_color = "#0f1724"  # dark text
        self.root.configure(bg=self.bg_color)
        
        # Configure styles
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
        
        # Start server automatically
        self.start_server()
        
        # Create login frame
        self.login_frame = ttk.Frame(self.root, style='Main.TFrame')
        self.setup_login_frame()
        self.login_frame.pack(fill='both', expand=True)
        
        # Create main frame (initially hidden)
        self.main_frame = ttk.Frame(self.root, style='Main.TFrame')
        self.setup_main_frame()

        # Create status bar
        self.status_bar = ttk.Label(self.root,
                                  text="Server Status: Starting...",
                                  style='Status.TLabel',
                                  anchor='w')
        self.status_bar.pack(side='bottom', fill='x')
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Update status bar periodically
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
        
        # Create password entry
        password_entry = ttk.Entry(container_frame,
                                 textvariable=password_var,
                                 show="•",
                                 width=width,
                                 style='URL.TEntry')
        password_entry.pack(side='left', expand=True, fill='x')
        
        # Create toggle button with fixed width
        toggle_btn = ttk.Button(container_frame,
                              text='👁',
                              width=3,
                              command=lambda: self.toggle_password_visibility(password_entry, toggle_btn))
        toggle_btn.pack(side='left', padx=(5, 0))
        
        return container_frame  # Return the frame instead of the entry
    
    def setup_login_frame(self):
        # Center the login form
        center_frame = ttk.Frame(self.login_frame, style='Main.TFrame')
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Logo or Title
        ttk.Label(center_frame, 
                 text="Caching Proxy Server", 
                 style='Header.TLabel').pack(pady=20)
        
        # Login form with better styling
        form_frame = ttk.Frame(center_frame, style='Main.TFrame')
        form_frame.pack(padx=40, pady=20)
        
        # Username
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
        
        # Password with show/hide toggle
        password_label_frame = ttk.Frame(form_frame, style='Main.TFrame')
        password_label_frame.pack(fill='x', pady=(0, 5))
        ttk.Label(password_label_frame, 
                 text="Password:", 
                 font=('Helvetica', 10)).pack(side='left')
                 
        self.password_var = tk.StringVar()
        password_frame = self.create_password_frame(form_frame, self.password_var)
        password_frame.pack(fill='x', pady=(0, 15))
        
        # Login button
        login_btn = ttk.Button(form_frame, 
                              text="Login",
                              command=self.login,
                              style='Accent.TButton')
        login_btn.pack(pady=10, ipadx=20, ipady=5)
        
        # Store password entry widget for binding
        self.password_entry = password_frame.winfo_children()[0]  # Get the Entry widget from the frame
        
        # Bind Enter key to login
        username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self.login())
        
    def setup_main_frame(self):
        # Notebook for tabs
        self.style.configure('TNotebook', background=self.bg_color)
        self.style.configure('TNotebook.Tab', padding=[12, 4], font=('Helvetica', 10))
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Proxy tab
        proxy_frame = ttk.Frame(self.notebook, style='Main.TFrame')
        self.notebook.add(proxy_frame, text='🌐 Proxy')

        # Header
        ttk.Label(proxy_frame,
                 text="Proxy Server Control",
                 style='Header.TLabel').pack(pady=10)

        # Server control with status indicator and logout
        control_frame = ttk.Frame(proxy_frame, style='Main.TFrame')
        control_frame.pack(fill='x', padx=20, pady=10)

        # Left side controls
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

        # Right side controls (logout)
        right_controls = ttk.Frame(control_frame, style='Main.TFrame')
        right_controls.pack(side='right')

        self.logout_btn = ttk.Button(right_controls,
                                   text="Logout",
                                   command=self.logout,
                                   style='Accent.TButton')
        self.logout_btn.pack(side='right', padx=5, ipadx=10, ipady=2)

        # Main content: left = controls + response, right = history/analytics
        main_content = ttk.Frame(proxy_frame, style='Main.TFrame')
        main_content.pack(fill='both', expand=True, padx=20, pady=10)

        left_column = ttk.Frame(main_content, style='Main.TFrame')
        left_column.pack(side='left', fill='both', expand=True)

        right_column = ttk.Frame(main_content, style='Main.TFrame')
        right_column.pack(side='right', fill='y')

        # URL input with modern styling (placed in left column)
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

        # Response area with better styling (on left column)
        response_frame = ttk.Frame(left_column, style='Main.TFrame')
        response_frame.pack(fill='both', expand=True)

        ttk.Label(response_frame,
                 text="Response:",
                 font=('Helvetica', 10)).pack(anchor='w', pady=5)

        # Top row: status badges (cache hit/miss) and blocked notice
        top_badge_frame = ttk.Frame(response_frame, style='Main.TFrame')
        top_badge_frame.pack(fill='x', pady=(0, 8))

        self.cache_status_var = tk.StringVar(value="Cache: -")
        self.cache_status_label = ttk.Label(top_badge_frame, textvariable=self.cache_status_var, font=('Helvetica', 10, 'bold'))
        self.cache_status_label.pack(side='left', padx=(0, 10))

        # Blocked notice (hidden by default)
        self.blocked_var = tk.StringVar(value="")
        self.blocked_label = ttk.Label(top_badge_frame, textvariable=self.blocked_var, font=('Helvetica', 10, 'bold'))
        self.blocked_label.pack(side='left')

        # Custom style for response area (text)
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

        # Right column: history and analytics
        # History list
        ttk.Label(right_column, text="History", font=('Helvetica', 12, 'bold'), background=self.bg_color, foreground=self.text_color).pack(anchor='w', pady=(0, 5))
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

        # Analytics panel
        ttk.Label(right_column, text='Analytics', font=('Helvetica', 12, 'bold'), background=self.bg_color, foreground=self.text_color).pack(anchor='w')
        self.analytics_frame = ttk.Frame(right_column, style='Main.TFrame')
        self.analytics_frame.pack(fill='x', pady=(5, 10))

        self.requests_var = tk.StringVar(value='Requests: 0')
        self.hits_var = tk.StringVar(value='Cache Hits: 0')
        self.misses_var = tk.StringVar(value='Cache Misses: 0')

        ttk.Label(self.analytics_frame, textvariable=self.requests_var, background=self.bg_color, foreground=self.text_color).pack(anchor='w')
        ttk.Label(self.analytics_frame, textvariable=self.hits_var, background=self.bg_color, foreground=self.text_color).pack(anchor='w')
        ttk.Label(self.analytics_frame, textvariable=self.misses_var, background=self.bg_color, foreground=self.text_color).pack(anchor='w')

    # (Clear Cache button removed)

        # Admin tab
        self.admin_frame = ttk.Frame(self.notebook, style='Main.TFrame')
        self.setup_admin_frame()

        # Bind Enter key to send request
        url_entry.bind('<Return>', lambda e: self.send_request())

    def add_to_history(self, url):
        if not hasattr(self, 'history'):
            self.history = []
        # Avoid duplicates: move to top
        if url in self.history:
            self.history.remove(url)
        self.history.insert(0, url)
        # Keep to 50 entries
        self.history = self.history[:50]
        # Refresh listbox
        self.history_list.delete(0, tk.END)
        for u in self.history:
            self.history_list.insert(tk.END, u)

    def load_selected_history(self):
        sel = self.history_list.curselection()
        if not sel:
            return
        url = self.history_list.get(sel[0])
        self.url_var.set(url)
        self.send_request()

    def clear_cache(self):
        # Call server endpoint to clear cache. Only Admins allowed; server enforces.
        # Provide immediate UI feedback
        try:
            # disable the button while request is in progress
            try:
                self.clear_cache_btn.configure(state='disabled')
            except Exception:
                pass
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
                # Refresh analytics after clearing
                self.refresh_analytics()
                # Reset cache badge
                self.cache_status_var.set("Cache: -")
            else:
                # show server response text if available
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
            # catch-all — surface any unexpected errors
            messagebox.showerror("Error", f"Unexpected error: {e}")
        finally:
            # Restore button state: enabled only if user is admin
            try:
                users_db = load_users()
                uname = self.username_var.get()
                user = users_db.get(uname)
                if user and user.get('role') == 'Admin':
                    self.clear_cache_btn.configure(state='normal')
                else:
                    self.clear_cache_btn.configure(state='disabled')
            except Exception:
                try:
                    self.clear_cache_btn.configure(state='normal')
                except Exception:
                    pass
            # restore status bar (will be updated by update_status shortly)
            self.update_status()

    def refresh_analytics(self):
        # Fetch analytics from server
        try:
            resp = requests.get(f"http://localhost:{self.proxy_port}/cache_stats", headers={"Authorization": self.auth_header})
            if resp.status_code == 200:
                js = resp.json()
                an = js.get('analytics', {})
                self.requests_var.set(f"Requests: {an.get('requests', 0)}")
                self.hits_var.set(f"Cache Hits: {an.get('cache_hits', 0)}")
                self.misses_var.set(f"Cache Misses: {an.get('cache_misses', 0)}")
        except Exception:
            # Ignore network errors here
            pass
        
    def login(self):
        username = self.username_var.get()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
            
        # Create basic auth header
        auth_string = f"{username}:{password}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        # Make sure server is running
        if not self.server_running:
            if not self.start_server():
                return
                
        # Test authentication with analytics endpoint
        try:
            response = requests.get(
                f"http://localhost:{self.proxy_port}/analytics",
                headers={"Authorization": f"Basic {auth_b64}"}
            )
            
            if response.status_code == 200:
                # Load user details
                users_db = load_users()
                user = users_db.get(username)
                
                self.login_frame.pack_forget()
                self.main_frame.pack(fill='both', expand=True)
                self.auth_header = f"Basic {auth_b64}"
                self.server_btn.config(text="Stop Server")
                
                # Show admin tab if user is admin
                if user and user.get("role") == "Admin":
                    self.notebook.add(self.admin_frame, text='User Management')
                    self.refresh_user_list()
                    # Enable clear cache for admins
                    try:
                        self.clear_cache_btn.configure(state='normal')
                    except Exception:
                        pass
                else:
                    try:
                        self.clear_cache_btn.configure(state='disabled')
                    except Exception:
                        pass

                # Refresh analytics panel
                try:
                    self.refresh_analytics()
                except Exception:
                    pass
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
                    
                    # Create new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Run the server
                    loop.run_until_complete(self.server.serve())
                    loop.close()
                
                self.server_thread = threading.Thread(target=run_server)
                self.server_thread.daemon = True
                self.server_thread.start()
                self.server_running = True
                
                # Wait a bit for the server to start
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
                # Wait for server to stop
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
            # Clear sensitive data
            self.auth_header = None
            self.username_var.set("")
            self.password_var.set("")
            
            # Switch back to login frame
            self.main_frame.pack_forget()
            self.login_frame.pack(fill='both', expand=True)
            
            # Clear response area and URL
            self.response_area.delete(1.0, tk.END)
            self.url_var.set("")
    
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
            
        # Normalize URL
        url = self.normalize_url(url)
        self.url_var.set(url)  # Update the entry with normalized URL
            
        try:
            response = requests.get(
                f"http://localhost:{self.proxy_port}/?url={url}",
                headers={"Authorization": self.auth_header}
            )

            # Reset blocked badge
            self.blocked_var.set("")
            self.blocked_label.configure(foreground=self.text_color)

            # Read cache header if present
            cache_header = response.headers.get('X-Cache')
            if cache_header:
                self.cache_status_var.set(f"Cache: {cache_header}")
                if cache_header.upper() == 'HIT':
                    self.cache_status_label.configure(foreground='#2ecc71')  # green
                else:
                    self.cache_status_label.configure(foreground=self.accent_color)
            else:
                # Unknown -> clear
                self.cache_status_var.set("Cache: -")
                self.cache_status_label.configure(foreground=self.text_color)

            # If blocked, server returns 403 with JSON payload
            if response.status_code == 403:
                try:
                    js = response.json()
                    reason = js.get('reason') or js.get('error') or 'Access Denied'
                    blocked_url = js.get('blocked_url', url)
                    self.blocked_var.set(f"ACCESS DENIED: {blocked_url} — {reason}")
                    # Make blocked label prominent
                    self.blocked_label.configure(foreground='#ff4d4f')
                    # Clear response area (blocked message should be separate)
                    self.update_response_area("", clear=True)
                    return
                except Exception:
                    # Fall through to show error text
                    pass

            if response.status_code == 200:
                self.update_response_area(response.text)
                # Add to history and refresh analytics
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
        # Header
        ttk.Label(self.admin_frame, 
                 text="User Management", 
                 style='Header.TLabel').pack(pady=10)
        
        # Container for list and form
        content_frame = ttk.Frame(self.admin_frame, style='Main.TFrame')
        content_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Left side - User List
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
        
        # Styled Treeview
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
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.user_list.yview)
        self.user_list.configure(yscrollcommand=scrollbar.set)
        
        self.user_list.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Right side - Add User Form
        form_frame = ttk.Frame(content_frame, style='Main.TFrame')
        form_frame.pack(side='right', fill='y', padx=(10, 0))
        
        ttk.Label(form_frame,
                 text="Add New User",
                 font=('Helvetica', 12, 'bold')).pack(pady=(0, 20))
        
        # Username field
        ttk.Label(form_frame,
                 text="Username:",
                 font=('Helvetica', 10)).pack(anchor='w', pady=(0, 5))
        self.new_username = tk.StringVar()
        ttk.Entry(form_frame,
                 textvariable=self.new_username,
                 width=25,
                 style='URL.TEntry').pack(fill='x', pady=(0, 15))
        
        # Password field with show/hide toggle
        ttk.Label(form_frame,
                 text="Password:",
                 font=('Helvetica', 10)).pack(anchor='w', pady=(0, 5))
        self.new_password = tk.StringVar()
        password_frame = self.create_password_frame(form_frame, self.new_password, width=25)
        password_frame.pack(fill='x', pady=(0, 15))
        
        # Role selection
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
        
        # Add user button
        ttk.Button(form_frame,
                  text="Add User",
                  command=self.add_user,
                  style='Accent.TButton').pack(fill='x', ipady=5)

    def refresh_user_list(self):
        # Clear existing items
        for item in self.user_list.get_children():
            self.user_list.delete(item)
        
        # Load and display users
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
            # Load current users
            with open("users.json", "r") as f:
                data = json.load(f)
            
            # Check if username already exists
            if any(u["username"] == username for u in data["users"]):
                messagebox.showerror("Error", "Username already exists")
                return
            
            # Add new user
            data["users"].append({
                "username": username,
                "password": password,
                "role": role
            })
            
            # Save updated users
            with open("users.json", "w") as f:
                json.dump(data, f, indent=2)
            
            # Clear form
            self.new_username.set("")
            self.new_password.set("")
            self.new_role.set("Student")
            
            # Refresh list
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
            
        # Add timestamp
        status += datetime.now().strftime("%H:%M:%S")
        self.status_bar.configure(text=status)
        
        # Schedule next update and periodically refresh analytics
        self.root.after(1000, self.update_status)
        # Update analytics every 5 seconds
        self.root.after(5000, self.refresh_analytics)
    
    def update_response_area(self, text, error=False, clear=False):
        """Update response area with formatted text"""
        if clear:
            self.response_area.delete(1.0, tk.END)
            return

        self.response_area.delete(1.0, tk.END)
        
    # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.response_area.insert(tk.END, f"[{timestamp}]\n", "timestamp")
        
        # Format and insert the response
        if error:
            self.response_area.tag_configure("error", foreground="#ff6b6b")
            self.response_area.insert(tk.END, text, "error")
        else:
            self.response_area.insert(tk.END, text)
            
        self.response_area.see(tk.END)
    
    def run(self):
        # Configure text tags
        self.response_area.tag_configure("timestamp", foreground="#9fb3ff")
        self.root.mainloop()

if __name__ == "__main__":
    app = ProxyGUI()
    app.run()