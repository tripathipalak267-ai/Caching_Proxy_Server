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
        self.root = ThemedTk(theme="arc")  # Modern theme
        self.root.title("Caching Proxy Server")
        self.root.geometry("1000x700")
        
        # Configure colors and styles
        self.style = ttk.Style()
        self.bg_color = "#f0f0f0"
        self.accent_color = "#2196F3"
        self.root.configure(bg=self.bg_color)
        
        # Configure styles
        self.style.configure('Main.TFrame', background=self.bg_color)
        self.style.configure('Header.TLabel', 
                           font=('Helvetica', 16, 'bold'),
                           padding=10,
                           background=self.bg_color)
        self.style.configure('Status.TLabel',
                           font=('Helvetica', 10),
                           padding=5,
                           background=self.bg_color)
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
                                  style='Status.TLabel')
        self.status_bar.pack(side='bottom', fill='x')
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Update status bar periodically
        self.update_status()
        
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
        ttk.Label(form_frame, 
                 text="Username:", 
                 font=('Helvetica', 10)).pack(anchor='w', pady=(0, 5))
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(form_frame, 
                                 textvariable=self.username_var,
                                 width=30,
                                 style='URL.TEntry')
        username_entry.pack(pady=(0, 15))
        
        # Password
        ttk.Label(form_frame, 
                 text="Password:", 
                 font=('Helvetica', 10)).pack(anchor='w', pady=(0, 5))
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(form_frame, 
                                 textvariable=self.password_var,
                                 show="•",
                                 width=30,
                                 style='URL.TEntry')
        password_entry.pack(pady=(0, 20))
        
        # Login button
        login_btn = ttk.Button(form_frame, 
                              text="Login",
                              command=self.login,
                              style='Accent.TButton')
        login_btn.pack(pady=10, ipadx=20, ipady=5)
        
        # Bind Enter key to login
        username_entry.bind('<Return>', lambda e: password_entry.focus())
        password_entry.bind('<Return>', lambda e: self.login())
        
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
        
        # Server control with status indicator
        control_frame = ttk.Frame(proxy_frame, style='Main.TFrame')
        control_frame.pack(fill='x', padx=20, pady=10)
        
        self.server_btn = ttk.Button(control_frame, 
                                   text="Start Server",
                                   command=self.toggle_server,
                                   style='Accent.TButton')
        self.server_btn.pack(side='left', padx=5, ipadx=10, ipady=2)
        
        self.server_status = ttk.Label(control_frame,
                                     text="●",
                                     foreground='gray',
                                     font=('Helvetica', 16),
                                     style='Status.TLabel')
        self.server_status.pack(side='left', padx=5)
        
        # URL input with modern styling
        url_frame = ttk.Frame(proxy_frame, style='Main.TFrame')
        url_frame.pack(fill='x', padx=20, pady=10)
        
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
        
        # Response area with better styling
        response_frame = ttk.Frame(proxy_frame, style='Main.TFrame')
        response_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        ttk.Label(response_frame, 
                 text="Response:", 
                 font=('Helvetica', 10)).pack(anchor='w', pady=5)
        
        # Custom style for response area
        self.response_area = scrolledtext.ScrolledText(
            response_frame,
            height=20,
            font=('Consolas', 10),
            bg='white',
            wrap=tk.WORD
        )
        self.response_area.pack(fill='both', expand=True)
        
        # Admin tab
        self.admin_frame = ttk.Frame(self.notebook, style='Main.TFrame')
        self.setup_admin_frame()
        # Admin tab will be added only for admin users
        
        # Bind Enter key to send request
        url_entry.bind('<Return>', lambda e: self.send_request())
        
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
    
    def send_request(self):
        url = self.url_var.get()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
            
        try:
            response = requests.get(
                f"http://localhost:{self.proxy_port}/?url={url}",
                headers={"Authorization": self.auth_header}
            )
            
            if response.status_code == 200:
                self.update_response_area(response.text)
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
        
        # Password field
        ttk.Label(form_frame,
                 text="Password:",
                 font=('Helvetica', 10)).pack(anchor='w', pady=(0, 5))
        self.new_password = tk.StringVar()
        ttk.Entry(form_frame,
                 textvariable=self.new_password,
                 show="•",
                 width=25,
                 style='URL.TEntry').pack(fill='x', pady=(0, 15))
        
        # Role selection
        ttk.Label(form_frame,
                 text="Role:",
                 font=('Helvetica', 10)).pack(anchor='w', pady=(0, 5))
        self.new_role = tk.StringVar(value="Student")
        role_combo = ttk.Combobox(form_frame,
                                textvariable=self.new_role,
                                values=["Admin", "Student", "Teacher"],
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
        
        # Schedule next update
        self.root.after(1000, self.update_status)
    
    def update_response_area(self, text, error=False):
        """Update response area with formatted text"""
        self.response_area.delete(1.0, tk.END)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.response_area.insert(tk.END, f"[{timestamp}]\n", "timestamp")
        
        # Format and insert the response
        if error:
            self.response_area.tag_configure("error", foreground="red")
            self.response_area.insert(tk.END, text, "error")
        else:
            self.response_area.insert(tk.END, text)
            
        self.response_area.see(tk.END)
    
    def run(self):
        # Configure text tags
        self.response_area.tag_configure("timestamp", foreground="blue")
        self.root.mainloop()

if __name__ == "__main__":
    app = ProxyGUI()
    app.run()